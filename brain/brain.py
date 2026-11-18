"""ALJABR BRAIN: turns user text into AI replies while keeping context."""

from __future__ import annotations

import datetime as _dt
import logging
import time
from typing import Callable, Optional

from brain.conversation import Conversation
from brain.prompts import build_system_prompt
from brain.provider import LLMProvider
from core.errors import InputError, ProviderError
from core.logging_setup import get_logger

MAX_INPUT_CHARS = 4000


class Brain:
    """Combines a provider, a conversation and the system prompt.

    Message *contents* are never logged (privacy); only sizes and timing are.
    """

    def __init__(
        self,
        provider: LLMProvider,
        language: str = "uz",
        max_history: int = 20,
        max_input_chars: int = MAX_INPUT_CHARS,
        logger: Optional[logging.Logger] = None,
        today: Callable[[], _dt.date] = _dt.date.today,
    ) -> None:
        self.provider = provider
        self.language = language
        self.max_input_chars = max_input_chars
        self.conversation = Conversation(max_history)
        self.logger = logger or get_logger("brain")
        self._today = today

    def system_prompt(self) -> str:
        return build_system_prompt(self.language, self._today())

    def reset(self) -> None:
        """Forget the current conversation."""
        self.conversation.clear()

    def ask(self, text: str) -> str:
        """Send ``text`` to the AI and return its reply.

        Raises ``InputError`` for empty/oversized input and ``ProviderError``
        when the AI call fails. On failure the history is left unchanged.
        """
        text = (text or "").strip()
        if not text:
            raise InputError("empty input", code="empty")
        if len(text) > self.max_input_chars:
            raise InputError(
                f"input longer than {self.max_input_chars} characters", code="too_long"
            )

        self.conversation.add_user(text)
        started = time.monotonic()
        try:
            response = self.provider.generate(self.conversation.with_system(self.system_prompt()))
        except ProviderError as exc:
            self.conversation.pop_last()
            self.logger.info(
                "AI request failed: code=%s status=%s detail=%s", exc.code, exc.status, exc
            )
            raise

        self.conversation.add_assistant(response.text)
        self.logger.info(
            "AI reply: model=%s in_chars=%d out_chars=%d seconds=%.2f usage=%s",
            response.model,
            len(text),
            len(response.text),
            time.monotonic() - started,
            response.usage,
        )
        return response.text
