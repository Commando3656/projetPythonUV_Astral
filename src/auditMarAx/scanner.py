import fnmatch
import hashlib
import logging
import mimetypes
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from auditMarAx.database import prepare_database, save_file


logger = logging.getLogger(__name__)


def matches(path: Path, pattern: str) -> bool:
    return fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(
        path.as_posix(), pattern
    )


def scan_directory(
    directory: Path,
    database: Path,
    excludes: Sequence[str] = (),
    includes: Sequence[str] = (),
) -> tuple[int, int, list[str]]:
    root = directory.resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Le chemin n'est pas un répertoire : {root}")

    database_path = database.resolve()
    log_path = Path("auditMarAx.log").resolve()
    scanned = 0
    skipped = 0
    errors: list[str] = []

    with closing(sqlite3.connect(database_path)) as connection:
        with connection:
            prepare_database(connection)

            def report_walk_error(error: OSError) -> None:
                message = f"{error.filename}: {error}"
                errors.append(message)
                logger.error(message)

            for current, folders, filenames in os.walk(
                root, onerror=report_walk_error
            ):
                current_path = Path(current)
                folders[:] = sorted(
                    folder
                    for folder in folders
                    if not any(
                        matches((current_path / folder).relative_to(root), pattern)
                        for pattern in excludes
                    )
                )

                for filename in sorted(filenames):
                    path = current_path / filename
                    relative_path = path.relative_to(root)

                    if any(matches(relative_path, pattern) for pattern in excludes):
                        skipped += 1
                        continue
                    if includes and not any(
                        matches(relative_path, pattern) for pattern in includes
                    ):
                        skipped += 1
                        continue

                    try:
                        resolved_path = path.resolve()
                        if resolved_path in (database_path, log_path) or str(
                            resolved_path
                        ).startswith(f"{database_path}-"):
                            skipped += 1
                            continue

                        metadata = path.stat()
                        with path.open("rb") as file:
                            digest = hashlib.file_digest(file, "sha256").hexdigest()

                        extension = path.suffix.lower()
                        modified_at = datetime.fromtimestamp(
                            metadata.st_mtime, timezone.utc
                        ).isoformat(timespec="seconds")
                        created_at = (
                            datetime.fromtimestamp(
                                metadata.st_birthtime, timezone.utc
                            ).isoformat(timespec="seconds")
                            if hasattr(metadata, "st_birthtime")
                            else None
                        )
                        mime_type = (
                            mimetypes.guess_type(path.name)[0]
                            or "application/octet-stream"
                        )
                        scanned_at = datetime.now(timezone.utc).isoformat(
                            timespec="seconds"
                        )

                        save_file(
                            connection,
                            path,
                            metadata.st_size,
                            modified_at,
                            created_at,
                            extension,
                            digest,
                            mime_type,
                            scanned_at,
                        )
                        scanned += 1
                    except (OSError, RuntimeError, OverflowError) as error:
                        message = f"{path}: {error}"
                        errors.append(message)
                        logger.error(message)

    return scanned, skipped, errors
