"""MemoryStore: long-term notes in SQLite, isolated per user.

Safety properties:
* Every query is parameterised and filtered by ``user_id`` (a note id that
  belongs to another user behaves as "not found").
* Text is validated before it is stored: not empty, not too long, no secrets.
* Note contents are never written to the log.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Callable, List, Optional

from core.errors import MemoryStoreError
from memory.guard import contains_sensitive
from memory.models import MemoryItem

DEFAULT_MAX_ITEMS = 500
DEFAULT_MAX_CHARS = 500

_WORD = re.compile(r"\w+")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize(text: str) -> str:
    """Trim and collapse all whitespace (including newlines) to single spaces."""
    return " ".join((text or "").split())


class MemoryStore:
    def __init__(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        *,
        max_items: int = DEFAULT_MAX_ITEMS,
        max_chars: int = DEFAULT_MAX_CHARS,
        clock: Optional[Callable[[], str]] = None,
    ) -> None:
        if not user_id:
            raise ValueError("user_id must not be empty")
        self._conn = conn
        self.user_id = user_id
        self.max_items = max_items
        self.max_chars = max_chars
        self._clock = clock or _utc_now

    # -- helpers ----------------------------------------------------------

    @contextmanager
    def _db(self):
        """Turn SQLite errors into ``MemoryStoreError(code='storage')``."""
        try:
            yield
        except sqlite3.Error as exc:
            try:
                self._conn.rollback()
            except sqlite3.Error:
                pass
            raise MemoryStoreError(
                f"database error: {type(exc).__name__}", code="storage"
            ) from None

    def _validate(self, text: str) -> str:
        text = normalize(text)
        if not text:
            raise MemoryStoreError("note is empty", code="empty")
        if len(text) > self.max_chars:
            raise MemoryStoreError(
                f"note is longer than {self.max_chars} characters", code="too_long"
            )
        if contains_sensitive(text):
            raise MemoryStoreError("note looks like it contains a secret", code="secret")
        return text

    @staticmethod
    def _item(row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(row["id"], row["content"], row["created_at"], row["updated_at"])

    # -- reading ----------------------------------------------------------

    def count(self) -> int:
        with self._db():
            row = self._conn.execute(
                "SELECT COUNT(*) FROM memories WHERE user_id = ?", (self.user_id,)
            ).fetchone()
        return row[0]

    def list(self, limit: Optional[int] = None) -> List[MemoryItem]:
        """All notes of this user, newest first."""
        sql = (
            "SELECT id, content, created_at, updated_at FROM memories "
            "WHERE user_id = ? ORDER BY id DESC"
        )
        params: list = [self.user_id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(int(limit))
        with self._db():
            rows = self._conn.execute(sql, params).fetchall()
        return [self._item(row) for row in rows]

    def get(self, item_id: int) -> MemoryItem:
        with self._db():
            row = self._conn.execute(
                "SELECT id, content, created_at, updated_at FROM memories "
                "WHERE id = ? AND user_id = ?",
                (item_id, self.user_id),
            ).fetchone()
        if row is None:
            raise MemoryStoreError("note not found", code="not_found")
        return self._item(row)

    def search(self, query: str) -> List[MemoryItem]:
        """Notes containing every word of ``query`` (case-insensitive, any language).

        Matching is done in Python on the user's own notes, because SQLite's
        LIKE is case-insensitive for ASCII only (not for Cyrillic or Uzbek letters).
        """
        words = _WORD.findall((query or "").casefold())
        items = self.list()
        if not words:
            return items
        return [i for i in items if all(w in i.content.casefold() for w in words)]

    # -- writing ----------------------------------------------------------

    def add(self, text: str) -> MemoryItem:
        """Save a note. Saving the same text again returns the existing note."""
        text = self._validate(text)
        for existing in self.list():
            if existing.content.casefold() == text.casefold():
                return existing
        if self.count() >= self.max_items:
            raise MemoryStoreError(f"limit of {self.max_items} notes reached", code="limit")
        now = self._clock()
        with self._db():
            cursor = self._conn.execute(
                "INSERT INTO memories (user_id, content, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (self.user_id, text, now, now),
            )
            self._conn.commit()
        return MemoryItem(cursor.lastrowid, text, now, now)

    def update(self, item_id: int, text: str) -> MemoryItem:
        text = self._validate(text)
        now = self._clock()
        with self._db():
            cursor = self._conn.execute(
                "UPDATE memories SET content = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (text, now, item_id, self.user_id),
            )
            self._conn.commit()
        if cursor.rowcount == 0:
            raise MemoryStoreError("note not found", code="not_found")
        return self.get(item_id)

    def delete(self, item_id: int) -> None:
        with self._db():
            cursor = self._conn.execute(
                "DELETE FROM memories WHERE id = ? AND user_id = ?", (item_id, self.user_id)
            )
            self._conn.commit()
        if cursor.rowcount == 0:
            raise MemoryStoreError("note not found", code="not_found")

    def delete_all(self) -> int:
        """Delete every note of this user; returns how many were removed."""
        with self._db():
            cursor = self._conn.execute(
                "DELETE FROM memories WHERE user_id = ?", (self.user_id,)
            )
            self._conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error:
            pass
