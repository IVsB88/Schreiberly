import ctypes
import logging
import os
import sys
import threading
import time
from pathlib import Path

import pystray
import requests
import win32clipboard
import win32gui
import win32process
import psutil
from PIL import Image, ImageDraw
from pynput import keyboard
from winotify import Notification

from schreibarrly.config import load_config, save_config, DEFAULT_CONFIG_PATH
from schreibarrly.context import detect_context
from schreibarrly.db import init_db, log_correction
from schreibarrly.ollama import call_ollama, strip_preamble
from schreibarrly.startup import is_startup_enabled, set_startup_enabled

# ── Paths ─────────────────────────────────────────────────────────────────────

_APPDATA = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
_LOG_PATH = _APPDATA / "Schreibarrly" / "schreibarrly.log"

# ── Logging ───────────────────────────────────────────────────────────────────


def _setup_logging() -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(_LOG_PATH),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


# ── Single instance ───────────────────────────────────────────────────────────

_MUTEX_NAME = "SchreibarrlyMutex"
_mutex_handle = None


def _acquire_single_instance() -> bool:
    global _mutex_handle
    _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


# ── Icons ─────────────────────────────────────────────────────────────────────


def _make_icon(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    return img


_ICON_IDLE = _make_icon("#4CAF50")
_ICON_BUSY = _make_icon("#FF9800")
_ICON_ERROR = _make_icon("#F44336")

# ── Global state ──────────────────────────────────────────────────────────────

_config: dict = {}
_db_conn = None
_session: requests.Session | None = None
_tray: pystray.Icon | None = None
_correction_lock = threading.Lock()
_state = "idle"


# ── Clipboard ─────────────────────────────────────────────────────────────────


def _get_clipboard_text() -> str | None:
    win32clipboard.OpenClipboard()
    try:
        if not win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            return None
        return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()


def _set_clipboard_text(text: str) -> None:
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


# ── Window detection ──────────────────────────────────────────────────────────


def _get_foreground_window_info() -> tuple[str, str]:
    hwnd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hwnd) or ""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc_name = psutil.Process(pid).name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        proc_name = ""
    return proc_name, title


# ── Toast notifications ───────────────────────────────────────────────────────


def _show_toast(title: str, message: str) -> None:
    try:
        if _tray is not None:
            _tray.notify(message, title)
        else:
            Notification(app_id="Schreibarrly", title=title, msg=message).show()
    except Exception:
        logging.exception("toast failed")


# ── Tray state ────────────────────────────────────────────────────────────────


def _set_state(state: str, title: str | None = None) -> None:
    global _state
    _state = state
    if _tray is None:
        return
    icon_map = {
        "idle": _ICON_IDLE,
        "correcting": _ICON_BUSY,
        "error": _ICON_ERROR,
    }
    _tray.icon = icon_map.get(state, _ICON_IDLE)
    _tray.title = title or f"Schreibarrly — {state}"


# ── Correction logic ──────────────────────────────────────────────────────────


def _do_correction() -> None:
    if not _correction_lock.acquire(blocking=False):
        _show_toast("Schreibarrly", "Correction already in progress.")
        return

    error = False
    timer = None
    try:
        text = _get_clipboard_text()
        if not text or not text.strip():
            _show_toast("Schreibarrly", "No text in clipboard.")
            return

        words = text.split()
        if len(words) > _config["max_words"]:
            _show_toast(
                "Schreibarrly",
                f"Text too long ({len(words)} words, max {_config['max_words']}).",
            )
            return

        _set_state("correcting")
        preview = text[:40].replace("\n", " ")
        timer = threading.Timer(
            _config["progress_toast_delay_seconds"],
            lambda: _show_toast("Schreibarrly", f"Correcting: {preview}..."),
        )
        timer.start()

        proc, title = _get_foreground_window_info()
        ctx = detect_context(proc, title)
        logging.info("correction started context=%s words=%d", ctx, len(words))

        try:
            raw = call_ollama(
                _session,
                _config["ollama_endpoint"],
                _config["model"],
                ctx,
                text,
                _config["timeout_seconds"],
            )
        except requests.exceptions.Timeout:
            # Model was cold (not loaded). Warm-up takes >30s; retry once.
            logging.info("ollama cold start, retrying once")
            _show_toast("Schreibarrly", "Ollama is warming up, retrying...")
            raw = call_ollama(
                _session,
                _config["ollama_endpoint"],
                _config["model"],
                ctx,
                text,
                _config["timeout_seconds"],
            )
        corrected = strip_preamble(raw)
        _set_clipboard_text(corrected)
        log_correction(_db_conn, ctx, text, raw, corrected)
        logging.info("correction done context=%s", ctx)
        _set_state("idle")

    except requests.exceptions.ConnectionError:
        logging.warning("ollama not reachable")
        _set_state("error", title="Schreibarrly — Ollama not running")
        error = True
    except requests.exceptions.Timeout:
        logging.warning("ollama timed out")
        _set_state("error", title="Schreibarrly — correction timed out")
        error = True
    except Exception:
        logging.exception("unexpected error in correction")
        _set_state("error", title="Schreibarrly — unexpected error")
        error = True
    finally:
        if timer:
            timer.cancel()
        _correction_lock.release()

    if error:
        time.sleep(5)
        _set_state("idle")


def _on_hotkey() -> None:
    threading.Thread(target=_do_correction, daemon=True).start()


# ── Tray menu actions ─────────────────────────────────────────────────────────


def _on_about(_icon, _item) -> None:
    hotkey = _config.get("hotkey", "<ctrl>+<shift>+g")
    _show_toast("Schreibarrly", f"Schreibarrly v0.1.0 — Hotkey: {hotkey}")


def _on_toggle_startup(_icon, _item) -> None:
    enabled = not is_startup_enabled()
    try:
        set_startup_enabled(enabled)
        msg = "Schreibarrly will start automatically at login." if enabled else "Removed from startup."
        _show_toast("Schreibarrly", msg)
        logging.info("startup set to %s", enabled)
    except Exception:
        logging.exception("failed to set startup")
        _show_toast("Schreibarrly", "Could not update startup setting.")


def _on_quit(icon, _item) -> None:
    icon.visible = False
    icon.stop()


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    global _config, _db_conn, _session, _tray

    _setup_logging()
    logging.info("Schreibarrly starting")

    if not _acquire_single_instance():
        _show_toast("Schreibarrly", "Schreibarrly is already running.")
        sys.exit(0)

    first_run = not DEFAULT_CONFIG_PATH.exists()
    _config = load_config()
    if first_run:
        save_config(_config)

    _db_conn = init_db()
    _session = requests.Session()

    hotkey_str = _config["hotkey"]
    listener = keyboard.GlobalHotKeys({hotkey_str: _on_hotkey})
    listener.start()
    logging.info("hotkey registered: %s", hotkey_str)

    def _status_text(item):
        return f"Schreibarrly — {_state}"

    menu = pystray.Menu(
        pystray.MenuItem(_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("About Schreibarrly", _on_about),
        pystray.MenuItem(
            "Launch at startup",
            _on_toggle_startup,
            checked=lambda item: is_startup_enabled(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", _on_quit),
    )

    _tray = pystray.Icon("Schreibarrly", _ICON_IDLE, "Schreibarrly — idle", menu)

    if first_run:
        def _first_run_toast():
            time.sleep(1)
            _show_toast(
                "Schreibarrly",
                f"Schreibarrly is running! Press {hotkey_str} to correct text.",
            )
        threading.Thread(target=_first_run_toast, daemon=True).start()

    logging.info("tray icon starting")
    _tray.run()

    listener.stop()
    logging.info("Schreibarrly exiting")


if __name__ == "__main__":
    main()
