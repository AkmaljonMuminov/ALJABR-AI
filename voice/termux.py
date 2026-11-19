"""Termux:API speech adapters (Android).

Requires the Termux:API *app* plus ``pkg install termux-api`` in Termux, and
microphone permission for Termux:API.

IMPORTANT - not yet verified on a real device:
* ``termux-speech-to-text`` uses the phone's speech recogniser in the phone's
  own recognition language; it has no language option. Set the phone's speech
  language to Uzbek (if available) and test.
* ``termux-tts-speak`` takes ``-l`` language, ``-n`` region, ``-e`` engine,
  ``-p`` pitch and ``-r`` rate. It cannot choose a named voice, so the
  "female" voice is approximated with pitch; the real result depends on the
  TTS engine installed on the phone.
"""

from __future__ import annotations

from typing import Optional

from core.errors import VoiceError
from voice.interfaces import SpeechToText, TextToSpeech
from voice.runner import CommandResult, CommandRunner

STT_COMMAND = "termux-speech-to-text"
TTS_COMMAND = "termux-tts-speak"
TTS_TIMEOUT = 120  # speaking a long answer takes time


def _failure(result: CommandResult, what: str) -> VoiceError:
    combined = f"{result.stdout} {result.stderr}".lower()
    if "permission" in combined:
        return VoiceError(f"{what}: permission denied", code="permission")
    return VoiceError(f"{what} failed (exit code {result.returncode})", code="failed")


class TermuxSTT(SpeechToText):
    def __init__(self, runner: Optional[CommandRunner] = None, timeout: float = 20) -> None:
        self._runner = runner or CommandRunner()
        self.timeout = timeout

    def listen(self) -> str:
        result = self._runner.run([STT_COMMAND], timeout=self.timeout)
        if result.returncode != 0:
            raise _failure(result, "speech recognition")
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines[-1] if lines else ""  # last line = final recognition result


class TermuxTTS(TextToSpeech):
    def __init__(
        self,
        runner: Optional[CommandRunner] = None,
        language: str = "uz",
        region: str = "",
        engine: str = "",
        pitch: float = 1.1,
        rate: float = 0.95,
    ) -> None:
        self._runner = runner or CommandRunner()
        self.language = language
        self.region = region
        self.engine = engine
        self.pitch = pitch
        self.rate = rate

    def build_args(self) -> list:
        args = [TTS_COMMAND, "-l", self.language, "-p", str(self.pitch), "-r", str(self.rate)]
        if self.region:
            args += ["-n", self.region]
        if self.engine:
            args += ["-e", self.engine]
        return args

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        # The text goes through stdin, so it can never be mistaken for an option.
        result = self._runner.run(self.build_args(), input_text=text, timeout=TTS_TIMEOUT)
        if result.returncode != 0:
            raise _failure(result, "text-to-speech")
