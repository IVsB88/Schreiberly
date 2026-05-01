import json
import pytest
from schreibarrly.config import load_config, save_config, DEFAULTS


def test_returns_defaults_when_no_file(tmp_path):
    result = load_config(tmp_path / "config.json")
    assert result == DEFAULTS


def test_loads_file_values(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"model": "llama3.1", "timeout_seconds": 60}))
    result = load_config(p)
    assert result["model"] == "llama3.1"
    assert result["timeout_seconds"] == 60


def test_missing_keys_get_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"model": "orca-mini"}))
    result = load_config(p)
    assert result["hotkey"] == DEFAULTS["hotkey"]
    assert result["ollama_endpoint"] == DEFAULTS["ollama_endpoint"]


def test_unknown_keys_are_ignored(tmp_path):
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"model": "mistral", "surprise_key": "ignored"}))
    result = load_config(p)
    assert "surprise_key" not in result


def test_malformed_json_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("this is not json {{{")
    result = load_config(p)
    assert result == DEFAULTS


def test_empty_file_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("")
    result = load_config(p)
    assert result == DEFAULTS


def test_save_creates_directory_and_file(tmp_path):
    p = tmp_path / "nested" / "config.json"
    save_config(DEFAULTS, p)
    assert p.exists()
    loaded = json.loads(p.read_text())
    assert loaded["model"] == DEFAULTS["model"]


def test_save_then_load_roundtrip(tmp_path):
    p = tmp_path / "config.json"
    custom = dict(DEFAULTS, model="llama3.1", timeout_seconds=90)
    save_config(custom, p)
    result = load_config(p)
    assert result["model"] == "llama3.1"
    assert result["timeout_seconds"] == 90
