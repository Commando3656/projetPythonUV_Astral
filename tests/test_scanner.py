import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from auditMarAx.analysis import extension_sizes, find_duplicates, largest_files
from auditMarAx.scanner import scan_directory


class ScanDirectoryTests(unittest.TestCase):
    def test_scan_saves_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            directory = base / "files"
            directory.mkdir()
            included_file = directory / "notes.txt"
            included_file.write_text("hello", encoding="utf-8")
            (directory / "script.py").write_text("print('hi')", encoding="utf-8")
            database = base / "scan.sqlite3"

            scanned, errors = scan_directory(directory, database)

            self.assertEqual((scanned, errors), (2, []))
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

            scanned, errors = scan_directory(directory, database)

            self.assertEqual((scanned, errors), (1, []))
            with sqlite3.connect(database) as connection:
                extension = connection.execute(
                    "SELECT extension FROM files"
                ).fetchone()[0]
            self.assertEqual(extension, ".dat")


class AnalysisTests(unittest.TestCase):
    def test_find_duplicates_and_rank_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            directory = base / "files"
            other_directory = base / "other"
            directory.mkdir()
            other_directory.mkdir()
            (directory / "first.txt").write_text("same", encoding="utf-8")
            (directory / "second.txt").write_text("same", encoding="utf-8")
            (directory / "large.bin").write_bytes(b"x" * 20)
            (other_directory / "larger.bin").write_bytes(b"x" * 30)
            database = base / "scan.sqlite3"

            scan_directory(directory, database)
            scan_directory(other_directory, database)

            duplicates = find_duplicates(database, directory)
            biggest = largest_files(database, directory, limit=2)
            by_extension = extension_sizes(database, directory)

            self.assertEqual(len(duplicates), 1)
            self.assertEqual(duplicates[0][0], 4)
            self.assertEqual(len(duplicates[0][1]), 2)
            self.assertEqual(biggest[0], (str(directory / "large.bin"), 20))
            self.assertEqual(
                by_extension,
                [(".bin", 1, 20), (".txt", 2, 8)],
            )


if __name__ == "__main__":
    unittest.main()
