"""VoiceSession: the push-to-talk conversation loop.

One turn: trigger -> listen -> (wake phrase) -> brain -> speak.
The microphone is opened only after the trigger, never in the background.
Spoken text is never written to the log (only sizes and state changes).
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from brain.brain import Brain
from brain.cli import describe_error
from core.errors import InputError, ProviderError, VoiceError
from core.logging_setup import get_logger
from core.messages import t
from voice.activation import ActivationTrigger
from voice.interfaces import SpeechToText, TextToSpeech
from voice.state import VoiceState, VoiceStateMachine
from voice.text import clean_for_speech
from voice.wake import WakePhraseMatcher

#: Errors that make further listening pointless; they end the session.
FATAL_CODES = ("unavailable", "permission")


def describe_voice_error(exc: VoiceError, lang: str) -> str:
    """Localized message for a voice error (generic message for unknown codes)."""
    return t(f"voice_{exc.code}" if exc.code in ("unavailable", "permission", "timeout") else "voice_failed", lang)


class _StopSession(Exception):
    """Internal: the user ended the session."""


class VoiceSession:
    def __init__(
        self,
        brain: Brain,
        stt: SpeechToText,
        tts: TextToSpeech,
        trigger: ActivationTrigger,
        language: str = "uz",
        wake_phrase: str = "Salom, ALJABR",
        require_wake: bool = False,
        output: Optional[Callable[[str], None]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.brain = brain
        self.stt = stt
        self.tts = tts
        self.trigger = trigger
        self.language = language
        self.matcher = WakePhraseMatcher(wake_phrase) if require_wake else None
        self.machine = VoiceStateMachine()
        self._output = output
        self.logger = logger or get_logger("voice")

    # -- public -----------------------------------------------------------

    def run(self) -> None:
        """Run until the user quits. Raises ``VoiceError`` for fatal voice problems."""
        self._say(t("voice_intro", self.language))
        try:
            while True:
                if not self.trigger.wait():
                    break
                self._turn()
        except _StopSession:
            pass
        finally:
            self.machine.stop()

    # -- one turn ---------------------------------------------------------

    def _turn(self) -> None:
        text = self._listen()
        if not text:
            self.machine.reset()
            return
        command = self._command_from(text)
        if not command:
            self.machine.reset()
            return
        self._respond(command)

    def _command_from(self, text: str) -> str:
        """Apply the wake phrase rule and return the command to send to the brain."""
        if self.matcher is None:
            return text
        match = self.matcher.match(text)
        if not match.matched:
            self.logger.info("Speech ignored: wake phrase not heard")
            self.machine.reset()
            return ""
        if match.remainder:
            return match.remainder
        self._speak(t("voice_ready_phrase", self.language))  # wake phrase alone: ask for the command
        return self._listen()

    def _listen(self) -> str:
        self.machine.transition(VoiceState.LISTENING)
        self._say(t("voice_listening", self.language))
        try:
            text = self.stt.listen().strip()
        except VoiceError as exc:
            self.machine.reset()
            if exc.code == "closed":
                raise _StopSession from None
            self.logger.warning("Speech input failed: code=%s detail=%s", exc.code, exc)
            if exc.code in FATAL_CODES:
                raise
            self._say(describe_voice_error(exc, self.language))
            return ""
        if not text:
            self.machine.reset()
            self._say(t("voice_no_speech", self.language))
            return ""
        self.logger.info("Speech input: %d chars", len(text))
        if not self.stt.echoes_input:
            self._say(t("voice_heard", self.language, text=text))
        return text

    def _respond(self, command: str) -> None:
        self.machine.transition(VoiceState.THINKING)
        try:
            reply = self.brain.ask(command)
        except (InputError, ProviderError) as exc:
            self._say_and_speak(describe_error(exc, self.language))
            return
        self._say_and_speak(reply)

    # -- output helpers ---------------------------------------------------

    def _say(self, message: str) -> None:
        (self._output or print)(message)

    def _say_and_speak(self, message: str) -> None:
        self._say(message)  # always show the text, even if speech fails
        self._speak(message)

    def _speak(self, message: str) -> None:
        self.machine.transition(VoiceState.SPEAKING)
        try:
            self.tts.speak(clean_for_speech(message))
        except VoiceError as exc:
            self.logger.warning("Speech output failed: code=%s detail=%s", exc.code, exc)
            self._say(describe_voice_error(exc, self.language))
        finally:
            self.machine.reset()
