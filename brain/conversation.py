"""Short-term conversation history (in memory only).

Persistent, user-approved memory arrives in Phase 4. This class only keeps the
recent turns of the current session so the AI has context.
"""

from __future__ import annotations

from typing import List

from brain.types import ROLE_ASSISTANT, ROLE_SYSTEM, ROLE_USER, Message


class Conversation:
    """Holds recent user/assistant messages, trimmed to ``max_messages``."""

    def __init__(self, max_messages: int = 20) -> None:
        if max_messages < 2:
            raise ValueError("max_messages must be at least 2")
        self.max_messages = max_messages
        self._messages: List[Message] = []

    def __len__(self) -> int:
        return len(self._messages)

    @property
    def messages(self) -> List[Message]:
        """A copy of the stored history (oldest first)."""
        return list(self._messages)

    def add_user(self, text: str) -> None:
        self._append(Message(ROLE_USER, text))

    def add_assistant(self, text: str) -> None:
        self._append(Message(ROLE_ASSISTANT, text))

    def pop_last(self) -> None:
        """Remove the newest message (used to undo a failed request)."""
        if self._messages:
            self._messages.pop()

    def clear(self) -> None:
        self._messages.clear()

    def with_system(self, system_prompt: str) -> List[Message]:
        """Return the system prompt followed by the history, ready for a provider."""
        return [Message(ROLE_SYSTEM, system_prompt)] + self._messages

    def _append(self, message: Message) -> None:
        self._messages.append(message)
        overflow = len(self._messages) - self.max_messages
        if overflow > 0:
            del self._messages[:overflow]
        # A reply without its question is confusing: history must start with the user.
        while self._messages and self._messages[0].role != ROLE_USER:
            del self._messages[0]
