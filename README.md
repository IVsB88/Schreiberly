# Schreibarrly

Context-aware German text correction for non-native professionals. Press a hotkey — corrected text lands on your clipboard.

Runs entirely offline via [Ollama](https://ollama.com). No text leaves your machine.

---

## How it works

1. Write your text in any app (Jira, Teams, Outlook, Miro)
2. Select all → **Ctrl+C**
3. Press **Ctrl+Shift+G**
4. Wait 2–20 seconds (tray icon goes amber)
5. Press **Ctrl+V** — corrected text appears

The app detects which program is in the foreground and adjusts the correction style automatically: formal register for Outlook, concise for Jira, casual for Teams.

**Tray menu:** Right-click the tray icon to access About, **Launch at startup** (toggle Windows auto-start), and Quit.

---

## Requirements

- Windows 10 or 11
- [Ollama](https://ollama.com) installed and **running** — Schreibarrly calls it on every correction. If Ollama is not running you will get an error (red tray icon). You can add Ollama to Windows startup manually, or launch it from the Start menu before using the hotkey.
- A supported GPU is strongly recommended (see latency table below)

---

## Installation

1. Install Ollama: https://ollama.com/download
2. Pull the default model: `ollama pull marco/em_german_mistral_v01`
3. Download `Schreibarrly.exe` from [Releases](../../releases)
4. Double-click to launch — it appears in your system tray

**Windows SmartScreen warning:** Because the `.exe` is unsigned, Windows will show "Unknown publisher — Windows protected your PC." Click **More info → Run anyway**. This is expected for open-source tools without a code signing certificate.

---

## Expected latency (em_german_mistral, default model)

Correction time depends on your hardware and text length. The app has a 30-second timeout by default (configurable).

| Hardware | 50 words | 200 words | 500 words | Notes |
|---|---|---|---|---|
| **RTX 4090** | ~1s | ~3s | ~7s | Ideal |
| **RTX 4070 / RX 7900** | ~1–2s | ~5s | ~13s | Great |
| **RTX 3060 8 GB / RX 6700** | ~2–3s | ~9s | ~22s | Good |
| **RTX 3050 / RX 6600** | ~4–6s | ~15s | ~35s | May hit timeout on long texts |
| **CPU only** | ~15–45s | ~45–90s | ~2–4 min | Increase timeout, use lighter model |

**Cold start:** The first correction after launching the app loads the model into GPU memory. This adds 3–10 seconds on first use. Subsequent corrections are faster.

**Rule of thumb:** For Jira comments and Teams messages (under 100 words), any modern GPU feels instant. For long emails (300–500 words), a mid-range GPU (RTX 3060 or better) keeps corrections under 30 seconds.

**CPU users:** CPU works but is slow. The default 30-second timeout is too short — increase it to 120 seconds in your config file: `"timeout_seconds": 120`. For faster corrections, try a lighter model: `ollama pull orca-mini` and set `"model": "orca-mini"`. Expect 20–60 seconds for a typical email on a modern laptop CPU.

---

## Configuration

Config file location: `%APPDATA%\Schreibarrly\config.json`

```json
{
  "model": "marco/em_german_mistral_v01",
  "hotkey": "<ctrl>+<shift>+g",
  "timeout_seconds": 30,
  "max_words": 1500,
  "progress_toast_delay_seconds": 10,
  "ollama_endpoint": "http://localhost:11434/api/generate"
}
```

Changes take effect after restarting the app (right-click tray icon → Quit, then relaunch).

**Note on `ollama_endpoint`:** If you point this at a remote server, your text will be sent over the network. Only do this on a trusted private network.

---

## Privacy

All text is processed locally. Nothing is sent to external servers (unless you configure a remote Ollama endpoint — see above).

Every correction is logged to `%APPDATA%\Schreibarrly\corrections.db` (SQLite). This database contains the original and corrected text. Do not use Schreibarrly on a shared Windows account.

Logs are written to `%APPDATA%\Schreibarrly\schreibarrly.log`.

---

## Development

```bash
pip install -e .
pytest
python -m schreibarrly
```

Source lives in `schreibarrly/`.

---

## License

MIT
