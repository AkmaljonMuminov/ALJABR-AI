"""Open the SQLite database and keep its schema up to date."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Sequence, Union

from core.errors import DatabaseError
from database.migrations import MIGRATIONS

MEMORY_PATH = ":memory:"


def schema_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migrate(conn: sqlite3.Connection, migrations: Sequence[str] = MIGRATIONS) -> int:
    """Apply pending migrations (each in its own transaction). Returns the version.

    Raises ``DatabaseError`` if the database was created by a newer program.
    """
    version = schema_version(conn)
    if version > len(migrations):
        raise DatabaseError(
            f"database schema version {version} is newer than this program supports "
            f"({len(migrations)}); update ALJABR AI"
        )
    for number in range(version, len(migrations)):
        try:
            conn.executescript(
                f"BEGIN;\n{migrations[number]}\nPRAGMA user_version = {number + 1};\nCOMMIT;"
            )
        except sqlite3.Error:
            if conn.in_transaction:
                conn.rollback()
            raise
    return schema_version(conn)


def _make_private(path: Path) -> None:
    """Owner read/write only, where the operating system supports it."""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def open_database(path: Union[str, Path]) -> sqlite3.Connection:
    """Open (and create/migrate) the database. Raises ``DatabaseError`` on failure.

    The file is created readable by its owner only. ``":memory:"`` gives a
    throw-away database (used by tests).
    """
    in_memory = str(path) == MEMORY_PATH
    conn = None
    try:
        if not in_memory:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        migrate(conn)
        if not in_memory:
            _make_private(Path(path))
    except (sqlite3.Error, OSError) as exc:
        if conn is not None:
            conn.close()
        raise DatabaseError(f"cannot open database: {type(exc).__name__}: {exc}") from None
    except DatabaseError:
        if conn is not None:
            conn.close()
        raise
    return conn
