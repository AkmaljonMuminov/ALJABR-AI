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
    command_handler: Optional[Callable[[str], Optional[str]]] = None,
    hint: str = "",
) -> None:
    """Interactive chat loop. Ends on /exit, Ctrl+D or Ctrl+C.

    ``input_func`` and ``output`` default to ``input`` and ``print`` (looked up
    at call time so they can be replaced in tests). ``command_handler`` gets
    every line that starts with ``/`` first; if it returns text, that text is
    shown and the line is not sent to the AI (used for memory commands).
    """
    read = input_func or input
    write = output or print
    write(t("chat_intro", lang))
    if hint:
        write(hint)
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
        if command_handler is not None and line.startswith("/"):
            handled = command_handler(line)
            if handled is not None:
                write(handled)
                continue
        try:
            write(brain.ask(line))
        except (InputError, ProviderError) as exc:
            write(describe_error(exc, lang))
