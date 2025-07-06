import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("jobs.db")


def get_connection():
    """Return a connection with row objects for nice dict‑like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
