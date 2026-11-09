import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from auditMarAx.cli import build_parser
from auditMarAx.scanner import scan_directory


class ScanDirectoryTests(unittest.TestCase):
    def test_scan_saves_metadata_and_respects_filters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            directory = base / "files"
            excluded_directory = directory / "ignored"
            excluded_directory.mkdir(parents=True)
            included_file = directory / "notes.txt"
            included_file.write_text("hello", encoding="utf-8")
            (directory / "script.py").write_text("print('hi')", encoding="utf-8")
            (excluded_directory / "hidden.txt").write_text(
                "ignored", encoding="utf-8"
            )
            database = base / "scan.sqlite3"

            scanned, skipped, errors = scan_directory(
                directory, database, excludes=["ignored", "*.py"], includes=["*.txt"]
            )

            self.assertEqual((scanned, skipped, errors), (1, 1, []))
            with sqlite3.connect(database) as connection:
                row = connection.execute(
                    """
                    SELECT path, size, modified_at, extension, sha256, mime_type
                    FROM files
                    """
                ).fetchone()

            self.assertEqual(row[0], str(included_file))
            self.assertEqual(row[1], 5)
            self.assertTrue(row[2])
            self.assertEqual(row[3], ".txt")
            self.assertEqual(row[4], hashlib.sha256(b"hello").hexdigest())
            self.assertEqual(row[5], "text/plain")

    def test_adds_extension_to_existing_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            directory = base / "files"
            directory.mkdir()
            (directory / "file.dat").write_text("data", encoding="utf-8")
            database = base / "old.sqlite3"
            with sqlite3.connect(database) as connection:
                connection.execute(
                    """
                    CREATE TABLE files (
                        path TEXT PRIMARY KEY,
                        size INTEGER NOT NULL,
                        modified_at TEXT NOT NULL,
                        created_at TEXT,
                        sha256 TEXT NOT NULL,
                        mime_type TEXT NOT NULL,
                        scanned_at TEXT NOT NULL
                    )
                    """
                )

            scanned, _, errors = scan_directory(directory, database)

            self.assertEqual((scanned, errors), (1, []))
            with sqlite3.connect(database) as connection:
                extension = connection.execute(
                    "SELECT extension FROM files"
                ).fetchone()[0]
            self.assertEqual(extension, ".dat")


class CliArgumentTests(unittest.TestCase):
    def test_accepts_repeated_filters(self) -> None:
        args = build_parser().parse_args(
            ["--exclude", "*.pyc", "--exclude", ".git", "--include", "*.py"]
        )

        self.assertEqual(args.exclude, ["*.pyc", ".git"])
        self.assertEqual(args.include, ["*.py"])


if __name__ == "__main__":
    unittest.main()
