import os
import sqlite3
from contextlib import closing
from pathlib import Path


def find_duplicates(
    database: Path, directory: Path
) -> list[tuple[int, list[str]]]:
    duplicates: dict[str, tuple[int, list[str]]] = {}
    prefix = f"{directory.resolve()}{os.sep}"
    with closing(sqlite3.connect(database)) as connection:
        rows = connection.execute(
            """
            SELECT sha256, size, path FROM files
            WHERE substr(path, 1, length(?)) = ?
            ORDER BY sha256, path
            """,
            (prefix, prefix),
        )
        for digest, size, path in rows:
            if digest not in duplicates:
                duplicates[digest] = (size, [])
            duplicates[digest][1].append(path)

    return [
        (size, paths)
        for size, paths in duplicates.values()
        if len(paths) > 1
    ]


def largest_files(
    database: Path, directory: Path, limit: int = 10
) -> list[tuple[str, int]]:
    prefix = f"{directory.resolve()}{os.sep}"
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(
            """
            SELECT path, size FROM files
            WHERE substr(path, 1, length(?)) = ?
            ORDER BY size DESC, path
            LIMIT ?
            """,
            (prefix, prefix, limit),
        ).fetchall()


def extension_sizes(database: Path, directory: Path) -> list[tuple[str, int, int]]:
    prefix = f"{directory.resolve()}{os.sep}"
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute(
            """
            SELECT extension, COUNT(*), SUM(size)
            FROM files
            WHERE substr(path, 1, length(?)) = ?
            GROUP BY extension
            ORDER BY SUM(size) DESC, extension
            """,
            (prefix, prefix),
        ).fetchall()
