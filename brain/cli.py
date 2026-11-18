"""Text interface for ALJABR BRAIN (used by ``main.py --chat`` and ``--ask``)."""

from __future__ import annotations

from typing import Callable, Optional

from brain.brain import Brain
from core.errors import AljabrError, InputError, ProviderError
from core.messages import MESSAGES, t

EXIT_COMMANDS = ("/exit", "/quit")
CLEAR_COMMAND = "/clear"


def describe_error(exc: AljabrError, lang: str) -> str:
    """Return a user-facing, localized message for a brain-related error.

    Unknown error codes fall back to a generic message instead of a raw key.
    """
    if isinstance(exc, InputError):
        key = f"input_{exc.code}"
        return t(key if key in MESSAGES["uz"] else "input_empty", lang)
    if isinstance(exc, ProviderError):
        key = f"provider_{exc.code}"
        return t(key if key in MESSAGES["uz"] else "provider_error", lang)
    return t("unexpected_error", lang)


def run_chat(
    brain: Brain,
    lang: str,
    input_func: Optional[Callable[[str], str]] = None,
    output: Optional[Callable[[str], None]] = None,
) -> None:
    """Interactive chat loop. Ends on /exit, Ctrl+D or Ctrl+C.

    ``input_func`` and ``output`` default to ``input`` and ``print`` (looked up
    at call time so they can be replaced in tests).
    """
    read = input_func or input
    write = output or print
    write(t("chat_intro", lang))
    while True:
        try:
            line = read("> ").strip()
        except (EOFError, KeyboardInterrupt):
            write("")
            return
        if not line:
            continue
        lowered = line.lower()
        if lowered in EXIT_COMMANDS:
            return
        if lowered == CLEAR_COMMAND:
            brain.reset()
            write(t("history_cleared", lang))
            continue
        try:
            write(brain.ask(line))
        except (InputError, ProviderError) as exc:
            write(describe_error(exc, lang))
