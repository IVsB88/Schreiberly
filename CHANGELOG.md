# Changelog

## [0.1.1] — 2026-05-08

### Fixed

- **Cold-start timeout**: First correction after hibernate/sleep loads the model into GPU memory, which can exceed the 30-second timeout. The app now catches the timeout and automatically retries once, showing a "warming up" toast during the wait.
- **Ghost tray icon on quit**: pystray did not remove the icon before the process exited. Fixed by setting `icon.visible = False` before calling `icon.stop()`.
- **Terminal flash on tray menu open**: The "Launch at startup" menu item's `checked` lambda called `schtasks.exe` (a console app) on every menu render, causing a brief terminal window flash. Fixed by passing `creationflags=CREATE_NO_WINDOW` to all subprocess calls.
- **Silent error feedback**: Toast notifications were suppressed by a global Windows setting. Error feedback now uses descriptive tray icon tooltips instead (e.g. "Schreibarrly — Ollama not running", visible on hover). Error state display duration extended from 3 s to 5 s.

## [0.1.0] — 2026-04-28

Initial release.

- System tray app for context-aware German text correction via Ollama
- Hotkey-triggered clipboard correction (Ctrl+Shift+G)
- Context detection (Outlook, Jira, Teams, Miro)
- Windows Task Scheduler auto-startup (login + resume from sleep)
- SQLite correction log, configurable via `%APPDATA%\Schreibarrly\config.json`
