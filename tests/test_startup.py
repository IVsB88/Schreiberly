from unittest.mock import MagicMock, patch
import sys
import winreg

import pytest

from schreibarrly.startup import is_startup_enabled, set_startup_enabled, _startup_command


def test_startup_command_contains_pythonw():
    cmd = _startup_command()
    assert "pythonw" in cmd.lower() or "python" in cmd.lower()
    assert "-m schreibarrly" in cmd


def test_is_startup_enabled_true():
    mock_key = MagicMock()
    with patch("winreg.OpenKey", return_value=mock_key.__enter__.return_value):
        mock_key.__enter__.return_value = MagicMock()
        with patch("winreg.QueryValueEx"):
            assert is_startup_enabled() is True


def test_is_startup_enabled_false():
    with patch("winreg.OpenKey", side_effect=OSError):
        assert is_startup_enabled() is False


def test_set_startup_enabled_writes_value():
    mock_key = MagicMock()
    with patch("winreg.OpenKey", return_value=mock_key) as mock_open:
        mock_key.__enter__ = lambda s: s
        mock_key.__exit__ = MagicMock(return_value=False)
        with patch("winreg.SetValueEx") as mock_set:
            set_startup_enabled(True)
            mock_set.assert_called_once()
            args = mock_set.call_args[0]
            assert args[1] == "Schreibarrly"
            assert "-m schreibarrly" in args[4]


def test_set_startup_enabled_deletes_value():
    mock_key = MagicMock()
    with patch("winreg.OpenKey", return_value=mock_key):
        mock_key.__enter__ = lambda s: s
        mock_key.__exit__ = MagicMock(return_value=False)
        with patch("winreg.DeleteValue") as mock_del:
            set_startup_enabled(False)
            mock_del.assert_called_once_with(mock_key, "Schreibarrly")


def test_set_startup_enabled_delete_missing_key_is_silent():
    mock_key = MagicMock()
    with patch("winreg.OpenKey", return_value=mock_key):
        mock_key.__enter__ = lambda s: s
        mock_key.__exit__ = MagicMock(return_value=False)
        with patch("winreg.DeleteValue", side_effect=OSError):
            set_startup_enabled(False)  # should not raise
