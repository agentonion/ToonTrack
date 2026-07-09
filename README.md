# ToonTrack

A macOS menu bar app that tracks [Toontown Rewritten](https://www.toontownrewritten.com/) invasions and sends native notifications when cogs you care about start (and optionally when they end).

Active groups use ToonHQ's live groups API (`/api/groups/list/1/`) — the same endpoint their website polls every 12 seconds, so groups appear and disappear automatically.

## Quick start

```bash
cd /path/to/ToonTrack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 toonhq_invasion_tracker.py
```

Look for **🐹** in the menu bar. Click it to see active invasion count, refresh, pick which cogs notify you, and open ToonHQ pages.

Settings are saved to `~/.toonhq_tracker/config.json`.

## Menu bar features

- Live counts in the menu bar: `🐱 Active Groups (X) Active Invasion (X)`
- **Active Invasions** submenu with suit type, cog name, time remaining, and progress
- **Active Groups** submenu listing current ToonHQ groups
- Groups auto-refresh every **12 seconds** (same as ToonHQ); invasions every **30 seconds**
- **Group Notifications…** menu — uncheck a type (CJ, Beanfest, DA Office, etc.) to mute alerts for that type
- Groups in an invaded district show `⚔️ Sellbot invasion (Two-Face)` in the list
- Notifications when any new invasion or group appears (respecting group type mutes)
- Toggle notification sounds
- One-click links to ToonHQ Invasions and Groups pages

Invasion ETAs use ToonHQ's computed defeat rate when available, with a local fallback estimate from TTR progress updates.

## Build a double-clickable `.app` (optional)

Uses [py2app](https://py2app.readthedocs.io/) so ToonTrack runs without a terminal and stays in the menu bar only (no Dock icon).

```bash
source .venv/bin/activate
pip install py2app
python3 setup.py py2app
```

The app bundle is created at `dist/ToonTrack.app`. Drag it to **Applications** (or anywhere you like) and double-click to launch.

To rebuild after code changes:

```bash
rm -rf build dist
python3 setup.py py2app
```

## Permissions

On first launch, macOS may ask you to allow **Notifications** for ToonTrack (or Terminal/Python if running from the command line). Enable them in **System Settings → Notifications** if you want alerts.

## Unofficial fan tool

Not affiliated with Toontown Rewritten or ToonHQ. Uses only TTR's public invasions endpoint.
