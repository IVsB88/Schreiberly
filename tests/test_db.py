import pytest
from schreibarrly.db import init_db, log_correction


def test_init_creates_tables(tmp_path):
    conn = init_db(tmp_path / "test.db")
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cur.fetchall()}
    assert "corrections" in tables
    assert "schema_version" in tables


def test_init_sets_schema_version_1(tmp_path):
    conn = init_db(tmp_path / "test.db")
    version = conn.execute("SELECT version FROM schema_version").fetchone()[0]
    assert version == 1


def test_init_idempotent(tmp_path):
    path = tmp_path / "test.db"
    conn = init_db(path)
    conn.close()
    conn2 = init_db(path)
    version = conn2.execute("SELECT version FROM schema_version").fetchone()[0]
    assert version == 1


def test_log_correction_inserts_row(tmp_path):
    conn = init_db(tmp_path / "test.db")
    log_correction(conn, "jira", "hallo welt", "Hallo Welt!", "Hallo Welt!")
    row = conn.execute("SELECT * FROM corrections").fetchone()
    assert row["context"] == "jira"
    assert row["original"] == "hallo welt"
    assert row["raw_response"] == "Hallo Welt!"
    assert row["corrected"] == "Hallo Welt!"


def test_log_correction_stores_raw_and_corrected_separately(tmp_path):
    conn = init_db(tmp_path / "test.db")
    log_correction(
        conn,
        "default",
        "text",
        "Hier ist der korrigierte Text:\nCorrected text.",
        "Corrected text.",
    )
    row = conn.execute("SELECT raw_response, corrected FROM corrections").fetchone()
    assert row["raw_response"] != row["corrected"]


def test_log_multiple_corrections(tmp_path):
    conn = init_db(tmp_path / "test.db")
    log_correction(conn, "teams", "msg 1", "Msg 1", "Msg 1")
    log_correction(conn, "outlook", "msg 2", "Msg 2", "Msg 2")
    count = conn.execute("SELECT COUNT(*) FROM corrections").fetchone()[0]
    assert count == 2


def test_log_correction_timestamp_recorded(tmp_path):
    conn = init_db(tmp_path / "test.db")
    log_correction(conn, "teams", "text", "Text", "Text")
    row = conn.execute("SELECT ts FROM corrections").fetchone()
    assert row["ts"] is not None
