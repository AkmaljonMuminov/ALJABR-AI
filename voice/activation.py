"""What starts listening.

Today: push-to-talk (the user presses Enter). Later: background wake-word.

Why background wake-word is a separate, later step
--------------------------------------------------
* Android stops microphone access for background apps. Continuous listening
  needs a *foreground service* with a visible notification and the user's
  microphone permission; a plain Termux script is not allowed to do it.
* Always-on listening drains the battery and raises privacy risk, so it must
  be opt-in, visible and easy to switch off.
* The planned ``BackgroundWakeTrigger`` will implement ``ActivationTrigger``
  (same ``wait`` contract), so ``VoiceSession`` will not need to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

from core.errors import VoiceError

QUIT_WORDS = ("q", "quit", "exit", "/exit", "/quit")


class ActivationTrigger(ABC):
    @abstractmethod
    def wait(self) -> bool:
        """Block until the user wants to speak. Return False to end the session."""


class PushToTalkTrigger(ActivationTrigger):
    """The microphone opens only after an explicit key press."""

    def __init__(self, prompt: str, input_func: Optional[Callable[[str], str]] = None) -> None:
        self.prompt = prompt
        self._input = input_func

    def wait(self) -> bool:
        read = self._input or input
        try:
            answer = read(self.prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer not in QUIT_WORDS


class AlwaysActiveTrigger(ActivationTrigger):
    """Used by the text fallback, where the input line itself is the trigger."""

    def wait(self) -> bool:
        return True


class BackgroundWakeTrigger(ActivationTrigger):
    """Placeholder for hands-free wake-word detection (not implemented)."""

    def __init__(self) -> None:
        raise VoiceError(
            "background wake-word detection is not implemented yet", code="unavailable"
        )

    def wait(self) -> bool:  # pragma: no cover - cannot be constructed
        return False
