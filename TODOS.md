# TODOs

## Stability / correctness

- [ ] If the second Ollama retry also times out, the user sees "correction timed out" but no explanation that a retry was attempted. Consider a more specific message.
- [ ] `_show_toast` silently swallows all exceptions. Add a `logging.warning` at minimum so notification failures are visible in the log.
- [ ] The correction lock is a threading.Lock; if the UI thread ever calls `_do_correction` directly (not via Thread), a deadlock is possible. Confirm the call path is always threaded.

## UX

- [ ] Tray tooltip is the only feedback channel when toasts are globally disabled. Consider a small persistent status window as an opt-in fallback.
- [ ] "Warming up" message uses `_show_toast`, which may silently fail. Ideally set the tray tooltip to "warming up…" during the retry.
- [ ] First-run experience: no onboarding after fresh install beyond a single toast. Consider a setup checklist (Ollama running? Model pulled?).

## Polish

- [ ] `_on_about` hardcodes `"v0.1.0"`. Read from `VERSION` file or `importlib.metadata` instead.
- [ ] `pyproject.toml` version and `VERSION` file are not in sync automatically. Add a check or consolidate to a single source of truth.
- [ ] `config.json` changes require a restart. Consider a "Reload config" menu item.

## Packaging

- [ ] Build a signed `.exe` with PyInstaller to avoid Windows SmartScreen warning.
- [ ] CI: add a GitHub Actions workflow that runs `pytest` on push.
- [ ] Releases: automate CHANGELOG extraction and GitHub release creation on version tag.
