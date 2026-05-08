import os
import subprocess
import sys
import tempfile
import winreg
from pathlib import Path

_TASK_NAME = "Schreibarrly"
_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _pythonw_path() -> str:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return str(pythonw if pythonw.exists() else Path(sys.executable))


def _project_dir() -> str:
    return str(Path(__file__).parent.parent)


def _remove_legacy_registry_entry() -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, _TASK_NAME)
    except OSError:
        pass


def _task_xml() -> str:
    user = os.environ.get("USERNAME", "")
    pythonw = _pythonw_path()
    workdir = _project_dir()
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Triggers>
    <LogonTrigger>
      <UserId>{user}</UserId>
      <Enabled>true</Enabled>
    </LogonTrigger>
    <SessionStateChangeTrigger>
      <StateChange>SessionUnlock</StateChange>
      <UserId>{user}</UserId>
      <Enabled>true</Enabled>
    </SessionStateChangeTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{pythonw}</Command>
      <Arguments>-m schreibarrly</Arguments>
      <WorkingDirectory>{workdir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""


def is_startup_enabled() -> bool:
    result = subprocess.run(
        ["schtasks", "/query", "/tn", _TASK_NAME],
        capture_output=True,
    )
    return result.returncode == 0


def set_startup_enabled(enabled: bool) -> None:
    if not enabled:
        subprocess.run(
            ["schtasks", "/delete", "/tn", _TASK_NAME, "/f"],
            capture_output=True,
        )
        return

    _remove_legacy_registry_entry()

    xml = _task_xml()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-16"
    ) as f:
        f.write(xml)
        tmp_path = f.name

    try:
        subprocess.run(
            ["schtasks", "/create", "/tn", _TASK_NAME, "/xml", tmp_path, "/f"],
            capture_output=True,
            check=True,
        )
    finally:
        os.unlink(tmp_path)
