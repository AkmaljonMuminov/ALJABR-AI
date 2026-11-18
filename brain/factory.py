"""Create the configured AI provider from settings."""

from __future__ import annotations

from typing import Callable, Dict

from brain.openai_provider import OpenAIProvider
from brain.provider import LLMProvider
from core.errors import ConfigError


def _make_openai(settings) -> LLMProvider:
    return OpenAIProvider(
        api_key=settings.openai_api_key.reveal(),
        model=settings.ai_model,
        base_url=settings.ai_base_url,
        timeout=settings.ai_timeout,
    )


#: Register new providers here (name used in ``ALJABR_AI_PROVIDER`` -> builder).
PROVIDERS: Dict[str, Callable] = {
    "openai": _make_openai,
}


def create_provider(settings) -> LLMProvider:
    """Return the provider named by ``settings.ai_provider``.

    Raises ``ConfigError`` for an unknown provider and
    ``ProviderNotConfiguredError`` when the key or model is missing.
    """
    builder = PROVIDERS.get(settings.ai_provider)
    if builder is None:
        supported = ", ".join(sorted(PROVIDERS))
        raise ConfigError(
            f"unknown AI provider {settings.ai_provider!r} (supported: {supported})"
        )
    return builder(settings)
