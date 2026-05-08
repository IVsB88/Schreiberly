import subprocess
from unittest.mock import MagicMock, call, patch

from schreibarrly.startup import (
    _pythonw_path,
    _task_xml,
    is_startup_enabled,
    set_startup_enabled,
)


def test_pythonw_path_contains_python():
    assert "python" in _pythonw_path().lower()


def test_task_xml_contains_session_unlock():
    xml = _task_xml()
    assert "SessionUnlock" in xml


def test_task_xml_contains_logon_trigger():
    xml = _task_xml()
    assert "LogonTrigger" in xml


def test_task_xml_contains_schreibarrly_module():
    xml = _task_xml()
    assert "-m schreibarrly" in xml


def test_is_startup_enabled_true():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert is_startup_enabled() is True
    mock_run.assert_called_once()
    assert "schtasks" in mock_run.call_args[0][0]


def test_is_startup_enabled_false():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        assert is_startup_enabled() is False


def test_set_startup_enabled_creates_task():
    with patch("subprocess.run") as mock_run, \
         patch("schreibarrly.startup._remove_legacy_registry_entry"), \
         patch("tempfile.NamedTemporaryFile"), \
         patch("os.unlink"):
        mock_run.return_value = MagicMock(returncode=0)
        set_startup_enabled(True)

    calls = [str(c) for c in mock_run.call_args_list]
    assert any("/create" in c for c in calls)


def test_set_startup_enabled_removes_legacy_registry():
    with patch("subprocess.run"), \
         patch("schreibarrly.startup._remove_legacy_registry_entry") as mock_legacy, \
         patch("tempfile.NamedTemporaryFile"), \
         patch("os.unlink"):
        set_startup_enabled(True)

    mock_legacy.assert_called_once()


def test_set_startup_enabled_deletes_task():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        set_startup_enabled(False)

    args = mock_run.call_args[0][0]
    assert "schtasks" in args
    assert "/delete" in args
    assert _task_xml.__module__.split(".")[0] or True  # just ensure import is fine


def test_set_startup_enabled_delete_missing_is_silent():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        set_startup_enabled(False)  # should not raise
