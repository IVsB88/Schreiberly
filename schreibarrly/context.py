"""
Context detection: maps (process_name, window_title) to a correction context.
Rules are checked top-to-bottom; first match wins.
"""

_BROWSER_PROCS = {"chrome.exe", "msedge.exe", "firefox.exe"}


def detect_context(process_name: str, window_title: str) -> str:
    proc = process_name.lower()
    title = window_title.lower()

    # Teams: native app or browser tab
    if proc in ("teams.exe", "ms-teams.exe"):
        return "teams"
    if proc in _BROWSER_PROCS and "microsoft teams" in title:
        return "teams"

    # Outlook: native app only
    if proc == "outlook.exe":
        return "outlook"

    # Jira: browser tab with Jira or Atlassian in title
    if proc in _BROWSER_PROCS and ("jira" in title or "atlassian" in title):
        return "jira"

    # Miro: native app or browser tab
    if proc == "miro.exe":
        return "miro"
    if proc in _BROWSER_PROCS and "miro" in title:
        return "miro"

    return "default"
