import json
import os
from pathlib import Path

_APPDATA = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
DEFAULT_CONFIG_PATH = _APPDATA / "Schreibarrly" / "config.json"

DEFAULTS: dict = {
    "model": "marco/em_german_mistral_v01",
    "hotkey": "<ctrl>+<shift>+g",
    "timeout_seconds": 30,
    "max_words": 1500,
    "progress_toast_delay_seconds": 10,
    "ollama_endpoint": "http://localhost:11434/api/generate",
}


def load_config(config_path: Path | None = None) -> dict:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    config = dict(DEFAULTS)
    if not path.exists():
        return config
    try:
        with open(path, encoding="utf-8") as f:
            on_disk = json.load(f)
        config.update({k: v for k, v in on_disk.items() if k in DEFAULTS})
    except (json.JSONDecodeError, OSError):
        pass  # malformed or unreadable — return defaults
    return config


def save_config(config: dict, config_path: Path | None = None) -> None:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
