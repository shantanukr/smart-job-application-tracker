import sqlite3
from datetime import datetime
from typing import List, Dict

from database import get_connection

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS job_applications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    company     TEXT NOT NULL,
    location    TEXT,
    url         TEXT,
    description TEXT,
    source      TEXT,
    date_posted TEXT NOT NULL
);
"""


def init_db() -> None:
    """Create table on start‑up (safe to call repeatedly)."""
    with get_connection() as conn:
        conn.execute(TABLE_SQL)
        conn.commit()


def insert_job(conn: sqlite3.Connection, job: Dict) -> int:
    """Insert one job record, return its new ID."""
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO job_applications
               (title, company, location, url, description, source, date_posted)
        VALUES (?,     ?,       ?,        ?,   ?,           ?,      ?)
        """,
        (
            job["title"],
            job["company"],
            job.get("location"),
            job.get("url"),
            job.get("description"),
            job.get("source"),
            job.get("date_posted", datetime.utcnow().isoformat()),
        ),
    )
    conn.commit()
    return cur.lastrowid


def fetch_all_jobs(conn: sqlite3.Connection) -> List[Dict]:
    """Return all stored jobs as a list of dictionaries."""
    rows = conn.execute("SELECT * FROM job_applications ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]
