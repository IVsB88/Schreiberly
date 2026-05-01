import pytest
from schreibarrly.context import detect_context


@pytest.mark.parametrize("proc,title,expected", [
    # Teams — native app (both process names)
    ("ms-teams.exe", "General — Microsoft Teams", "teams"),
    ("Teams.exe", "Channel — Microsoft Teams", "teams"),
    # Teams — browser tab
    ("chrome.exe", "Microsoft Teams", "teams"),
    # Outlook — native app
    ("OUTLOOK.EXE", "RE: Meeting tomorrow", "outlook"),
    # Jira — browser tab with Jira in title
    ("chrome.exe", "PROJ-123 — Jira", "jira"),
    # Jira — browser tab with Atlassian in title
    ("msedge.exe", "Atlassian | Dashboard", "jira"),
    # Miro — native app
    ("Miro.exe", "Team board", "miro"),
    # Miro — browser tab
    ("chrome.exe", "Miro | whiteboard", "miro"),
    # Default — unrecognised browser tab
    ("chrome.exe", "Google — Chrome", "default"),
    # Default — unrelated desktop app
    ("notepad.exe", "Untitled", "default"),
])
def test_detect_context(proc, title, expected):
    assert detect_context(proc, title) == expected


def test_teams_msedge_browser():
    assert detect_context("msedge.exe", "General — Microsoft Teams") == "teams"


def test_jira_firefox():
    # firefox is a browser; should still detect Jira
    assert detect_context("firefox.exe", "PROJ-42 — Jira") == "jira"


def test_miro_msedge():
    assert detect_context("msedge.exe", "Miro | My board") == "miro"


def test_outlook_case_insensitive():
    # Process names on Windows can arrive in any case
    assert detect_context("outlook.exe", "Inbox") == "outlook"
    assert detect_context("OUTLOOK.EXE", "Inbox") == "outlook"


def test_teams_takes_priority_over_title_miro():
    # If somehow Teams title contains "Miro", Teams wins (priority order)
    assert detect_context("ms-teams.exe", "Miro channel — Microsoft Teams") == "teams"
