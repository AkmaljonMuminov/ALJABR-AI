"""Backend-independent interfaces for speech input and output."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SpeechToText(ABC):
    """Turns one spoken phrase into text."""

    #: True when the user's words are already visible on screen (typed input).
    echoes_input: bool = False

    @abstractmethod
    def listen(self) -> str:
        """Record one phrase and return it ('' if nothing was recognised).

        Must raise ``core.errors.VoiceError`` (never a raw OS error) on failure.
        """


class TextToSpeech(ABC):
    """Speaks text aloud."""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Speak ``text`` and return when finished.

        Must raise ``core.errors.VoiceError`` on failure.
        """
