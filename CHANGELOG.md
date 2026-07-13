# Changelog

All notable changes to ToonTrack are documented here.

## [1.2.3] — 2026-07-13

### Fixed
- Invasion timers now count down live in the menu (1-second refresh while open)
- Invasion row text uses the same custom-drawn black style as Groups (no grey inactive menu text)

*Wave fixed the bugs: invasion grey text and non-live invasion timers.*

## [1.2.2] — 2026-07-10

### Changed
- Reverted custom app icon; restored default py2app bundle icon

## [1.2.1] — 2026-07-10

### Changed
- ~~App icon updated to 👀~~ (reverted in v1.2.2)

## [1.2.0] — 2026-07-10

### Changed
- Menu bar icon updated from 🐱 to 👀
- Renamed **Active Invasions** → **Invasions** and **Active Groups** → **Groups**
- Toons online count shown in the menu bar title and as a grey status row in the menu
- Last updated time moved to the main menu (under toons online), removed from the Invasions submenu
- Invasions submenu lists invasion rows only

### Fixed
- Active Invasions and Active Groups text visibility using view-based menu rows
- Hover highlighting on Group Notifications, Active Groups, and Invasions menu rows
- Menu row hover tracking for menu bar apps (`NSTrackingActiveAlways`)

### Added
- `Install ToonTrack.command` — one-click rebuild and install to `/Applications`

## [1.1.1] — 2026-07-10

### Fixed
- Hover highlighting on Active Groups menu rows

## [1.1.0] — 2026-07-10

### Added
- Online population in menu bar
- Group notification toggles that keep the submenu open
- View-based checkbox and action menu rows for Group Notifications

## [1.0.0] — 2026-07-10

### Added
- Initial ToonTrack macOS menu bar app
- Live invasion and group tracking via TTR and ToonHQ APIs
- Notifications for new invasions and groups
