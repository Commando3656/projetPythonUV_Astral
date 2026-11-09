import sqlite3
from pathlib import Path


def prepare_database(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            size INTEGER NOT NULL,
            modified_at TEXT NOT NULL,
            created_at TEXT,
            extension TEXT NOT NULL DEFAULT '',
            sha256 TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            scanned_at TEXT NOT NULL
        )
        """
    )
    columns = {row[1] for row in connection.execute("PRAGMA table_info(files)")}
    if "extension" not in columns:
        connection.execute(
            "ALTER TABLE files ADD COLUMN extension TEXT NOT NULL DEFAULT ''"
        )


def save_file(
    connection: sqlite3.Connection,
    path: Path,
    size: int,
    modified_at: str,
    created_at: str | None,
    extension: str,
    sha256: str,
    mime_type: str,
    scanned_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO files
            (path, size, modified_at, created_at, extension,
             sha256, mime_type, scanned_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            size = excluded.size,
            modified_at = excluded.modified_at,
            created_at = excluded.created_at,
            extension = excluded.extension,
            sha256 = excluded.sha256,
            mime_type = excluded.mime_type,
            scanned_at = excluded.scanned_at
        """,
        (
            str(path),
            size,
            modified_at,
            created_at,
            extension,
            sha256,
            mime_type,
            scanned_at,
        ),
    )
