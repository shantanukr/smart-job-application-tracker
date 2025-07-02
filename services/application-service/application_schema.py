import os
import sqlite3

DB_FILE = "application.db"


def setup_sqlite_db_conn(logger):
    is_new_db = not os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()

    # Schema setup
    if is_new_db:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        conn.commit()
        logger.info("Initialized new SQLite DB", extra={"schema": "applications"})
    return conn
