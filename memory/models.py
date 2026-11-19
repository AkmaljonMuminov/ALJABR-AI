"""Memory data types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryItem:
    """One saved note. Timestamps are UTC ISO-8601 strings."""

    id: int
    content: str
    created_at: str
    updated_at: str
