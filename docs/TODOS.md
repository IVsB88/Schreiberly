# TODOS

## Settings dialog (V2)
Tray menu → "Settings" → opens a small native dialog (Tkinter or tkinter.ttk) with three fields: hotkey (text input), Ollama model (dropdown: mistral, llama3.1, EM-German-Mistral), timeout in seconds (spinbox). Saves to config.json on OK. Required for non-technical users who want to change the hotkey without editing JSON.

**Depends on:** V1 shipping and user feedback confirming hotkey-change friction is real.
**Estimate:** ~1 day.
**Why:** Currently blocks non-technical expat community users from changing the default hotkey without opening a JSON file. V1 README documents config.json editing, but this is a barrier for the target audience.

## In-app update button (V2)
Tray menu → "Check for updates" → hits GitHub Releases API, compares version tag, downloads new .exe, launches it, exits current process.

**Depends on:** GitHub Actions CI/CD pipeline that builds .exe on tag push and uploads to GitHub Releases.
**Estimate:** ~1 day.
**Why now:** user mentioned this during V1 eng review as preferred distribution UX over manual downloads.
