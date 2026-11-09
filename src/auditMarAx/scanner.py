import hashlib
import logging
import mimetypes
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from auditMarAx.database import prepare_database, save_file


logger = logging.getLogger(__name__)


def scan_directory(
    directory: Path,
    database: Path,
) -> tuple[int, list[str]]:
    root = directory.resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Le chemin n'est pas un répertoire : {root}")

    database_path = database.resolve()
    log_path = Path("auditMarAx.log").resolve()
    scanned = 0
    errors: list[str] = []

    def report_error(path: Path, error: Exception) -> None:
        message = f"{path}: {error}"
        errors.append(message)
        logger.error(message)

    def report_walk_error(error: OSError) -> None:
        report_error(Path(error.filename or root), error)

    with closing(sqlite3.connect(database_path)) as connection, connection:
        prepare_database(connection)

        for current, folders, filenames in os.walk(root, onerror=report_walk_error):
            folders.sort()
            for filename in sorted(filenames):
                path = Path(current) / filename
                try:
                    resolved_path = path.resolve()
                    if resolved_path in (database_path, log_path) or str(
                        resolved_path
                    ).startswith(f"{database_path}-"):
                        continue

                    metadata = path.stat()
                    with path.open("rb") as file:
                        digest = hashlib.file_digest(file, "sha256").hexdigest()

                    modified_at = datetime.fromtimestamp(
                        metadata.st_mtime, timezone.utc
                    ).isoformat(timespec="seconds")
                    created_time = getattr(metadata, "st_birthtime", None)
                    created_at = (
                        datetime.fromtimestamp(created_time, timezone.utc).isoformat(
                            timespec="seconds"
                        )
                        if created_time is not None
                        else None
                    )
                    mime_type = mimetypes.guess_type(path.name)[0]

                    save_file(
                        connection,
                        path,
                        metadata.st_size,
                        modified_at,
                        created_at,
                        path.suffix.lower(),
                        digest,
                        mime_type or "application/octet-stream",
                        datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    )
                    scanned += 1
                except (OSError, RuntimeError, OverflowError) as error:
                    report_error(path, error)

    return scanned, errors
