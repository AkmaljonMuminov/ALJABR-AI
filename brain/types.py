"""Plain data types shared by all AI providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

ROLE_SYSTEM = "system"
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
VALID_ROLES = (ROLE_SYSTEM, ROLE_USER, ROLE_ASSISTANT)


@dataclass(frozen=True)
class Message:
    """One chat message."""

    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(f"invalid role: {self.role!r}")


@dataclass(frozen=True)
class ChatResponse:
    """A provider reply. ``usage`` holds token counts when the provider reports them."""

    text: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
