#!/usr/bin/env python3
"""
ToonHQ-style Invasion Tracker for the macOS menu bar.

Polls Toontown Rewritten's OFFICIAL public invasions API and ToonHQ's live
groups API, with notifications for new invasions and new groups (filterable
by group type).

Setup:
    pip3 install rumps requests
    python3 toonhq_invasion_tracker.py
"""

import json
import re
import time
from pathlib import Path

import requests
import rumps

API_URL = "https://www.toontownrewritten.com/api/invasions"
POPULATION_URL = "https://www.toontownrewritten.com/api/population"
TOONHQ_INVASIONS_URL = "https://toonhq.org/invasions/"
TOONHQ_GROUPS_LIST_URL = "https://toonhq.org/api/groups/list/1/"
TOONHQ_GROUPS_CORE_URL = "https://toonhq.org/api/groups/core_data/1/"

CONFIG_PATH = Path.home() / ".toonhq_tracker" / "config.json"
GROUPS_POLL_INTERVAL = 12
INVASIONS_POLL_INTERVAL = 30
USER_AGENT = "ToonTrack/1.0 (macOS menu bar invasion & group tracker)"
MENU_EMOJI = "🐱"
JSON_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}

COG_SUITS = {
    "Sellbot": [
        "Cold Caller", "Telemarketer", "Name Dropper", "Glad Hander",
        "Mover & Shaker", "Two-Face", "The Mingler", "Mr. Hollywood",
    ],
    "Cashbot": [
        "Short Change", "Penny Pincher", "Tightwad", "Bean Counter",
        "Number Cruncher", "Money Bags", "Loan Shark", "Robber Baron",
    ],
    "Lawbot": [
        "Bottom Feeder", "Bloodsucker", "Double Talker", "Ambulance Chaser",
        "Back Stabber", "Spin Doctor", "Legal Eagle", "Big Wig",
    ],
    "Bossbot": [
        "Flunky", "Pencil Pusher", "Yesman", "Micromanager",
        "Downsizer", "Head Hunter", "Corporate Raider", "The Big Cheese",
    ],
}
COG_TO_SUIT = {
    cog: suit for suit, cogs in COG_SUITS.items() for cog in cogs
}

DEFAULT_CONFIG = {
    "muted_group_types": [],
    "show_all_groups": False,
    "play_sound": True,
}


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        # migrate old key name
        if "selected_group_types" in cfg and "muted_group_types" not in cfg:
            all_types = cfg.pop("_known_group_types", [])
            selected = set(cfg.pop("selected_group_types", []))
            cfg["muted_group_types"] = sorted(t for t in all_types if t not in selected)
        return cfg
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()


def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def base_cog_name(raw_name: str) -> str:
    name = raw_name.replace("Version 2.0 ", "").replace(" (Skelecog)", "")
    return name.strip()


def cog_suit(raw_name: str) -> str:
    return COG_TO_SUIT.get(base_cog_name(raw_name), "Unknown")


def parse_progress(progress: str) -> tuple[int, int] | None:
    try:
        defeated, total = progress.split("/")
        return int(defeated), int(total)
    except (ValueError, AttributeError):
        return None


def format_eta(seconds: float | None) -> str:
    if seconds is None or seconds <= 0:
        return "?"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s" if secs else f"{minutes}m"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def estimate_eta(defeated: int, total: int, as_of: int, history: list) -> float | None:
    remaining = total - defeated
    if remaining <= 0:
        return 0

    samples = history + [(as_of, defeated)]
    if len(samples) < 2:
        return None

    prev_as_of, prev_defeated = samples[-2]
    dt = as_of - prev_as_of
    if dt <= 0:
        return None

    rate = (defeated - prev_defeated) / dt
    if rate <= 0:
        return None
    return remaining / rate


def group_types_from_core(core_data: dict) -> list[str]:
    return sorted({
        t["name"]
        for t in core_data.get("group_types", [])
        if t.get("game") == 1
    })


def fetch_population() -> int | None:
    """Return total toons online from TTR's public population API."""
    resp = requests.get(POPULATION_URL, timeout=10, headers=JSON_HEADERS)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        return None
    return data.get("totalPopulation")


def fetch_toonhq_state(url: str) -> dict:
    resp = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    match = re.search(r"window\.STATE\s*=\s*(\{.*?\});\s*window\.", resp.text, re.DOTALL)
    if not match:
        raise ValueError("Could not parse ToonHQ page state")
    return json.loads(match.group(1))


def fetch_toonhq_groups_core() -> dict:
    resp = requests.get(TOONHQ_GROUPS_CORE_URL, timeout=15, headers=JSON_HEADERS)
    resp.raise_for_status()
    return resp.json()


def parse_toonhq_groups_list(list_data: dict, core_data: dict) -> list[dict]:
    type_by_id = {
        t["id"]: t["name"]
        for t in core_data.get("group_types", [])
        if t.get("game") == 1
    }
    districts = {d["id"]: d["name"] for d in core_data.get("districts", [])}
    locations = {loc["id"]: loc["name"] for loc in core_data.get("locations", [])}

    groups = []
    for group in list_data.get("groups", []):
        if group.get("game") != 1:
            continue
        type_name = type_by_id.get(group.get("type"))
        if not type_name:
            continue
        groups.append({
            "id": group["id"],
            "type": type_name,
            "district": districts.get(group.get("district"), "?"),
            "location": locations.get(group.get("location"), "?"),
            "members": len(group.get("members") or []),
            "note": (group.get("note") or "").strip(),
        })
    return groups


def fetch_live_groups(core_data: dict | None) -> tuple[list[dict], dict]:
    if core_data is None:
        core_data = fetch_toonhq_groups_core()
    resp = requests.get(TOONHQ_GROUPS_LIST_URL, timeout=15, headers=JSON_HEADERS)
    resp.raise_for_status()
    return parse_toonhq_groups_list(resp.json(), core_data), core_data


def parse_toonhq_invasions(state: dict) -> dict[str, dict]:
    districts = {d["id"]: d["name"] for d in state.get("districts", [])}
    cogs = {c["id"]: c for c in state.get("cogs", [])}
    parsed = {}
    for inv in state.get("invasions", []):
        district = districts.get(inv.get("district"))
        cog_info = cogs.get(inv.get("cog"))
        if not district or not cog_info:
            continue
        cog_name = cog_info["name"]
        defeated = inv.get("defeated", 0)
        total = inv.get("total", 0)
        rate = float(inv.get("defeat_rate") or 0)
        remaining = max(total - defeated, 0)
        eta = remaining / rate if rate > 0 else None
        parsed[district] = {
            "type": cog_name,
            "suit": cog_info.get("type") or cog_suit(cog_name),
            "defeated": defeated,
            "total": total,
            "eta_seconds": eta,
        }
    return parsed


def format_invasion_line(inv: dict) -> str:
    pct = int((inv["defeated"] / inv["total"]) * 100) if inv["total"] else 0
    eta = format_eta(inv.get("eta_seconds"))
    suit = inv.get("suit", cog_suit(inv["type"]))
    return (
        f"{inv['district']} · {suit} · {inv['type']} · {eta} left · "
        f"{inv['defeated']}/{inv['total']} ({pct}%)"
    )


def format_group_line(group: dict, invasions_by_district: dict[str, dict]) -> str:
    note = f' · "{group["note"][:40]}"' if group["note"] else ""
    invasion = invasions_by_district.get(group["district"])
    invasion_tag = ""
    if invasion:
        suit = invasion.get("suit", cog_suit(invasion["type"]))
        invasion_tag = f" · ⚔️ {suit} invasion ({invasion['type']})"
    return (
        f"{group['type']} · {group['district']}{invasion_tag} · "
        f"{group['location']} · {group['members']} toon(s){note}"
    )


class InvasionTrackerApp(rumps.App):
    def __init__(self):
        super().__init__("ToonTrack", title=f"{MENU_EMOJI} Loading…")
        self.config = load_config()
        self.active_invasions = {}
        self.active_groups = {}
        self.invasion_history = {}
        self.invasion_display = []
        self.invasion_count = 0
        self.group_count = 0
        self.online_population = None
        self.groups_core_data = None
        self.known_group_types = []
        self.group_type_items = {}
        self.invasions_by_district = {}
        self.all_groups_count = 0
        self.group_type_menu = self.build_group_type_menu()

        self.menu = [
            ("Active Invasions", ["Checking…"]),
            ("Active Groups", ["Checking…"]),
            None,
            rumps.MenuItem("Refresh Now", callback=self.manual_refresh),
            None,
            ("Group Notifications…", self.group_type_menu),
            rumps.MenuItem("Play Sound With Notifications", callback=self.toggle_sound),
        ]
        self.menu["Play Sound With Notifications"].state = self.config["play_sound"]

    @rumps.timer(2)
    def startup_poll(self, timer):
        timer.stop()
        self.poll_groups()
        self.poll_invasions()

    @rumps.timer(GROUPS_POLL_INTERVAL)
    def auto_groups_poll(self, _):
        self.poll_groups()

    @rumps.timer(INVASIONS_POLL_INTERVAL)
    def auto_invasions_poll(self, _):
        self.poll_invasions()

    # ---------- menu construction ----------

    def build_group_type_menu(self):
        show_all = self.config.get("show_all_groups", False)
        show_all_item = rumps.MenuItem("Show All Groups", callback=self.on_show_all_groups)
        show_all_item.state = show_all
        return [
            show_all_item,
            None,
            rumps.MenuItem("Select All", callback=self.select_all_group_types),
            rumps.MenuItem("Unselect All", callback=self.unselect_all_group_types),
            None,
            rumps.MenuItem("(loads on first refresh)", callback=None),
        ]

    def rebuild_group_type_menu(self):
        muted = set(self.config.get("muted_group_types") or [])
        show_all = self.config.get("show_all_groups", False)
        submenu = self.menu["Group Notifications…"]
        submenu.clear()

        show_all_item = rumps.MenuItem("Show All Groups", callback=self.on_show_all_groups)
        show_all_item.state = show_all

        items = [
            show_all_item,
            None,
            rumps.MenuItem("Select All", callback=self.select_all_group_types),
            rumps.MenuItem("Unselect All", callback=self.unselect_all_group_types),
            None,
        ]
        self.group_type_items = {}
        for type_name in self.known_group_types:
            item = rumps.MenuItem(type_name, callback=self.make_group_type_toggle(type_name))
            item.state = type_name not in muted
            self.group_type_items[type_name] = item
            items.append(item)

        submenu.update(items)
        self.group_type_menu = items

    def make_group_type_toggle(self, type_name):
        def _toggle(sender):
            self.toggle_group_type(type_name)
            sender.state = self.group_notifications_enabled(type_name)
        return _toggle

    def on_show_all_groups(self, sender):
        self.toggle_show_all_groups()
        sender.state = self.config.get("show_all_groups", False)

    def refresh_group_type_checkmarks(self):
        muted = set(self.config.get("muted_group_types") or [])
        show_all = self.config.get("show_all_groups", False)
        if "Show All Groups" in self.menu["Group Notifications…"]:
            self.menu["Group Notifications…"]["Show All Groups"].state = show_all
        for type_name, item in self.group_type_items.items():
            item.state = type_name not in muted

    def toggle_group_type(self, type_name: str):
        muted = set(self.config.get("muted_group_types") or [])
        if type_name in muted:
            muted.discard(type_name)
        else:
            muted.add(type_name)
        self.config["muted_group_types"] = sorted(muted)
        save_config(self.config)
        self.refresh_group_type_checkmarks()
        self.redisplay_groups()

    def toggle_show_all_groups(self):
        self.config["show_all_groups"] = not self.config.get("show_all_groups", False)
        save_config(self.config)
        self.refresh_group_type_checkmarks()
        self.redisplay_groups()

    def select_all_group_types(self, sender):
        self.config["muted_group_types"] = []
        save_config(self.config)
        self.refresh_group_type_checkmarks()
        self.redisplay_groups()

    def unselect_all_group_types(self, sender):
        self.config["muted_group_types"] = self.known_group_types[:]
        save_config(self.config)
        self.refresh_group_type_checkmarks()
        self.redisplay_groups()

    def group_notifications_enabled(self, type_name: str) -> bool:
        return type_name not in set(self.config.get("muted_group_types") or [])

    def filter_groups_for_display(self, groups: list[dict]) -> list[dict]:
        if self.config.get("show_all_groups"):
            return groups
        return [g for g in groups if self.group_notifications_enabled(g["type"])]

    def redisplay_groups(self):
        if self.active_groups:
            self.update_groups_menu(list(self.active_groups.values()), None)
            self.refresh_title_and_sections()

    # ---------- callbacks ----------

    def toggle_sound(self, sender):
        sender.state = not sender.state
        self.config["play_sound"] = sender.state
        save_config(self.config)

    def manual_refresh(self, sender):
        self.poll_groups()
        self.poll_invasions()

    # ---------- display helpers ----------

    def update_invasions_menu(self, status_line: str, invasions: list[dict]):
        submenu = self.menu["Active Invasions"]
        submenu.clear()
        items = [status_line]
        if invasions:
            items.append(None)
            items.extend(format_invasion_line(inv) for inv in invasions)
        submenu.update(items)

    def update_groups_menu(self, groups: list[dict], group_error: str | None):
        submenu = self.menu["Active Groups"]
        submenu.clear()

        if group_error:
            submenu.update([f"Unavailable ({group_error})"])
            return

        self.all_groups_count = len(groups)
        visible = self.filter_groups_for_display(groups)
        self.group_count = len(visible)

        if not visible:
            if groups and not self.config.get("show_all_groups"):
                submenu.update(["(no groups match your selected types)"])
            else:
                submenu.update(["(none listed)"])
            return

        sorted_groups = sorted(visible, key=lambda g: (-g["members"], g["type"], g["district"]))
        submenu.update(
            format_group_line(group, self.invasions_by_district)
            for group in sorted_groups
        )

    def refresh_title_and_sections(self):
        online = f"{self.online_population} toons · " if self.online_population is not None else ""
        self.title = (
            f"{MENU_EMOJI} {online}"
            f"Active Groups ({self.group_count}) "
            f"Active Invasion ({self.invasion_count})"
        )
        self.menu["Active Invasions"].title = f"Active Invasions ({self.invasion_count})"
        self.menu["Active Groups"].title = f"Active Groups ({self.group_count})"

    # ---------- polling ----------

    def poll_groups(self, *_):
        group_error = None
        groups = []

        try:
            self.online_population = fetch_population()
        except requests.RequestException:
            pass

        try:
            groups, self.groups_core_data = fetch_live_groups(self.groups_core_data)
            types = group_types_from_core(self.groups_core_data)
            if types and types != self.known_group_types:
                self.known_group_types = types
                self.config["_known_group_types"] = types
                save_config(self.config)
                self.rebuild_group_type_menu()
        except requests.RequestException as e:
            group_error = str(e)

        if not group_error:
            current_groups = {g["id"]: g for g in groups}
            previous_groups = self.active_groups
            for group_id, group in current_groups.items():
                if group_id not in previous_groups and self.group_notifications_enabled(group["type"]):
                    invasion = self.invasions_by_district.get(group["district"])
                    invasion_note = ""
                    if invasion:
                        invasion_note = f" · ⚔️ {invasion['type']} invading district"
                    note = f' — "{group["note"]}"' if group["note"] else ""
                    self.notify(
                        title="New Group!",
                        subtitle=group["type"],
                        message=(
                            f"{group['district']} · {group['location']} · "
                            f"{group['members']} toon(s){invasion_note}{note}"
                        ),
                    )
            self.active_groups = current_groups

        self.update_groups_menu(groups, group_error)
        if not group_error:
            self.refresh_title_and_sections()
        elif self.invasion_count:
            self.title = f"{MENU_EMOJI} Active Groups (?) Active Invasion ({self.invasion_count})"

    def poll_invasions(self, *_):
        invasion_error = None
        population_error = None
        invasions_raw = {}
        toonhq_invasions = {}

        try:
            self.online_population = fetch_population()
        except requests.RequestException:
            population_error = True

        try:
            resp = requests.get(API_URL, timeout=10, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            invasions_raw = resp.json().get("invasions", {})
        except requests.RequestException as e:
            invasion_error = str(e)

        try:
            hq_state = fetch_toonhq_state(TOONHQ_INVASIONS_URL)
            toonhq_invasions = parse_toonhq_invasions(hq_state)
        except (requests.RequestException, ValueError):
            pass

        current_invasions = {}
        invasion_display = []

        for district, info in invasions_raw.items():
            raw_cog = info.get("type", "")
            progress = parse_progress(info.get("progress", ""))
            as_of = info.get("asOf") or info.get("startTimestamp") or int(time.time())

            defeated, total = (0, 0)
            if progress:
                defeated, total = progress

            hq = toonhq_invasions.get(district, {})
            eta_seconds = hq.get("eta_seconds")
            suit = hq.get("suit") or cog_suit(raw_cog)
            if hq:
                defeated = hq.get("defeated", defeated)
                total = hq.get("total", total)
                raw_cog = hq.get("type", raw_cog)

            history = self.invasion_history.setdefault(district, [])
            if progress and (not history or history[-1][0] != as_of):
                history.append((as_of, defeated))
                history[:] = history[-5:]

            if eta_seconds is None and progress:
                eta_seconds = estimate_eta(defeated, total, as_of, history[:-1] if history else [])

            invasion_display.append({
                "district": district,
                "type": raw_cog,
                "suit": suit,
                "defeated": defeated,
                "total": total,
                "eta_seconds": eta_seconds,
            })
            current_invasions[district] = raw_cog

        invasion_display.sort(
            key=lambda inv: (
                inv["eta_seconds"] if inv["eta_seconds"] is not None else float("inf"),
                inv["district"],
            )
        )

        previous_invasions = self.active_invasions
        for district, raw_cog in current_invasions.items():
            if district not in previous_invasions:
                detail = next(d for d in invasion_display if d["district"] == district)
                eta = format_eta(detail.get("eta_seconds"))
                suit = detail.get("suit", cog_suit(raw_cog))
                self.notify(
                    title="Invasion Started!",
                    subtitle=district,
                    message=f"{suit} · {raw_cog} has invaded {district} (~{eta} left)",
                )

        self.active_invasions = current_invasions
        self.invasion_display = invasion_display
        self.invasion_count = len(current_invasions) if not invasion_error else 0
        self.invasions_by_district = {
            inv["district"]: inv for inv in invasion_display
        }

        status_parts = [f"Updated {time.strftime('%I:%M:%S %p')}"]
        if self.online_population is not None:
            status_parts.insert(0, f"{self.online_population:,} toons online")
        elif population_error:
            status_parts.insert(0, "population unavailable")
        if invasion_error:
            status_parts.insert(0, f"invasions unavailable ({invasion_error})")

        self.update_invasions_menu(" · ".join(status_parts), invasion_display)

        # Refresh group lines so invasion tags stay in sync with districts.
        if self.active_groups and not invasion_error:
            groups = list(self.active_groups.values())
            self.update_groups_menu(groups, None)

        if invasion_error and not self.group_count:
            self.title = f"{MENU_EMOJI} ⚠️"
        else:
            self.refresh_title_and_sections()

    def notify(self, title, subtitle, message):
        rumps.notification(
            title=title,
            subtitle=subtitle,
            message=message,
            sound=self.config.get("play_sound", True),
        )


if __name__ == "__main__":
    InvasionTrackerApp().run()
