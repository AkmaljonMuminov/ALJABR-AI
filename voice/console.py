"""Text fallback used when no speech tools are installed.

Lets the whole voice loop (wake phrase, states, brain) be used and tested
without a microphone or speaker.
"""

from __future__ import annotations

from typing import Callable, Optional

from core.errors import VoiceError
from voice.interfaces import SpeechToText, TextToSpeech

QUIT_WORDS = ("q", "quit", "exit", "/exit", "/quit")


class ConsoleSTT(SpeechToText):
    """Reads a typed line instead of listening."""

    echoes_input = True

    def __init__(self, input_func: Optional[Callable[[str], str]] = None, prompt: str = "> ") -> None:
        self._input = input_func
        self.prompt = prompt

    def listen(self) -> str:
        read = self._input or input  # looked up at call time so tests can patch input
        try:
            line = read(self.prompt).strip()
        except (EOFError, KeyboardInterrupt):
            raise VoiceError("input closed", code="closed") from None
        if line.lower() in QUIT_WORDS:
            raise VoiceError("user quit", code="closed")
        return line


class ConsoleTTS(TextToSpeech):
    """Does not speak; the session already prints every reply."""

    def speak(self, text: str) -> None:
        return None
