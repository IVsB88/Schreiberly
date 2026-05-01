import sqlite3
from pathlib import Path
import os

_APPDATA = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
DEFAULT_DB_PATH = _APPDATA / "Schreibarrly" / "corrections.db"

_SCHEMA_V1 = """
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY
);
INSERT INTO schema_version VALUES (1);

CREATE TABLE corrections (
    id INTEGER PRIMARY KEY,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    context TEXT,
    original TEXT,
    raw_response TEXT,
    corrected TEXT
);
"""


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cur.fetchone() is None:
        conn.executescript(_SCHEMA_V1)
        conn.commit()


def log_correction(
    conn: sqlite3.Connection,
    context: str,
    original: str,
    raw_response: str,
    corrected: str,
) -> None:
    conn.execute(
        "INSERT INTO corrections (context, original, raw_response, corrected) VALUES (?, ?, ?, ?)",
        (context, original, raw_response, corrected),
    )
    conn.commit()
