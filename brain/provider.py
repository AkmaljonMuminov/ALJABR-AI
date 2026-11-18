"""Provider-independent interface for AI backends.

Any backend (OpenAI, a local model server, another vendor) only has to
implement ``LLMProvider.generate``. The rest of ALJABR never imports a
vendor-specific module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from brain.types import ChatResponse, Message


class LLMProvider(ABC):
    """Interface every AI provider adapter implements."""

    #: Short identifier used in settings (``ALJABR_AI_PROVIDER``).
    name: str = "base"

    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        *,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ChatResponse:
        """Return the assistant reply for ``messages``.

        Must raise ``core.errors.ProviderError`` (never a vendor-specific or
        raw network exception) when the call fails.
        """
