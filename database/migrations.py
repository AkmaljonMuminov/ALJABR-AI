"""Database schema migrations.

``MIGRATIONS[i]`` upgrades the schema from version ``i`` to ``i + 1``. The
current version is stored in SQLite's ``PRAGMA user_version``. Never edit an
existing entry; add a new one at the end.

Every table that holds user data has a ``user_id`` column from the start, so
the later multi-user platform (Phase 8) needs no data migration.
"""

from __future__ import annotations

MIGRATIONS = [
    # 0 -> 1: long-term, user-approved memory
    """
    CREATE TABLE memories (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    TEXT    NOT NULL,
        content    TEXT    NOT NULL,
        created_at TEXT    NOT NULL,
        updated_at TEXT    NOT NULL
    );
    CREATE INDEX idx_memories_user ON memories (user_id, id);
    """,
]
