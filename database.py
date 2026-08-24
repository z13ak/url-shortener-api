"""SQLite persistence for shortened links."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "links.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_conn: sqlite3.Connection | None = None


def get_shared_connection() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = get_connection()
        init_db(_conn)
    return _conn


def init_db(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                code TEXT PRIMARY KEY,
                original_url TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def create_link(conn: sqlite3.Connection, code: str, original_url: str) -> bool:
    try:
        with conn:
            conn.execute(
                "INSERT INTO links (code, original_url) VALUES (?, ?)", (code, original_url)
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_link(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()


def increment_clicks(conn: sqlite3.Connection, code: str) -> None:
    with conn:
        conn.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))


def code_exists(conn: sqlite3.Connection, code: str) -> bool:
    row = conn.execute("SELECT 1 FROM links WHERE code = ?", (code,)).fetchone()
    return row is not None
