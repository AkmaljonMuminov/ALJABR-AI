"""Shared test doubles for the AI brain tests (no network, no API key)."""

from __future__ import annotations

from brain.provider import LLMProvider
from brain.types import ChatResponse
from core.errors import ProviderError


class FakeProvider(LLMProvider):
    """Echoes the last user message. Can be told to fail first."""

    name = "fake"

    def __init__(self, failures=None):
        self.calls = []
        self._failures = list(failures or [])

    def generate(self, messages, *, max_tokens=None, temperature=None):
        self.calls.append(list(messages))
        if self._failures:
            raise self._failures.pop(0)
        last_user = [m for m in messages if m.role == "user"][-1].content
        return ChatResponse(text=f"echo:{last_user}", model="fake-model", usage={"total_tokens": 5})


def network_error():
    return ProviderError("network error: URLError", code="network", retryable=True)
