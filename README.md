# ToonTrack

A macOS menu bar app that tracks [Toontown Rewritten](https://www.toontownrewritten.com/) invasions and ToonHQ groups, with notifications when new invasions or groups appear.

Uses TTR's official APIs for invasions and population, and ToonHQ's live groups API (`/api/groups/list/1/`).

## Quick start

```bash
cd /path/to/ToonTrack
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 toonhq_invasion_tracker.py
```

Or double-click **`Run ToonTrack.command`** in Finder.

Settings are saved to `~/.toonhq_tracker/config.json`.

## Menu bar features

- Live counts: `🐱 934 toons · Active Groups (X) Active Invasion (X)`
- **Active Invasions** — suit type, cog name, time remaining, progress
- **Active Groups** — filtered by your notification selections (or all with **Show All Groups**)
- **Group Notifications…** — toggle types on/off, Select All, Unselect All
- Groups refresh every **12 seconds**; invasions and population every **30 seconds**
- Invasion tags on groups when their district is invaded
- Notifications for new invasions and groups (respecting muted group types)

## Build `ToonTrack.app`

```bash
source .venv/bin/activate
pip install py2app
python3 setup.py py2app
```

Output: `dist/ToonTrack.app` — drag to **Applications**.

## Updating `ToonTrack.app` after code changes

Whenever you change the Python code, rebuild and replace the app:

1. **Quit ToonTrack** (menu bar 🐱 → quit, or Activity Monitor)
2. In Terminal:

```bash
cd /Users/user/Desktop/Apps/ToonTrack
source .venv/bin/activate
rm -rf build dist
python3 setup.py py2app
```

3. Replace the old copy:

```bash
cp -R dist/ToonTrack.app /Applications/ToonTrack.app
```

Or drag the new `dist/ToonTrack.app` onto **Applications** and choose **Replace**.

4. Re-open **ToonTrack** from Applications.

Your settings in `~/.toonhq_tracker/config.json` are kept between rebuilds.

## Permissions

Allow **Notifications** in **System Settings → Notifications** if you want alerts.

## Unofficial fan tool

Not affiliated with Toontown Rewritten or ToonHQ.
