"""Choose speech backends from settings."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Callable, Optional

from core.errors import VoiceError
from core.messages import t
from voice.activation import ActivationTrigger, AlwaysActiveTrigger, PushToTalkTrigger
from voice.console import ConsoleSTT, ConsoleTTS
from voice.interfaces import SpeechToText, TextToSpeech
from voice.runner import CommandRunner
from voice.termux import STT_COMMAND, TTS_COMMAND, TermuxSTT, TermuxTTS

MODE_TERMUX = "termux"
MODE_CONSOLE = "console"


@dataclass
class VoiceBackend:
    mode: str
    stt: SpeechToText
    tts: TextToSpeech
    trigger: ActivationTrigger


def termux_tools_present(which: Callable[[str], Optional[str]] = shutil.which) -> bool:
    return bool(which(STT_COMMAND)) and bool(which(TTS_COMMAND))


def detect_mode(settings, which: Callable[[str], Optional[str]] = shutil.which) -> str:
    """Return the backend that would be used: ``termux`` or ``console``."""
    if settings.voice_backend == "console":
        return MODE_CONSOLE
    if settings.voice_backend == "termux":
        return MODE_TERMUX
    return MODE_TERMUX if termux_tools_present(which) else MODE_CONSOLE


def create_voice(
    settings,
    runner: Optional[CommandRunner] = None,
    which: Callable[[str], Optional[str]] = shutil.which,
) -> VoiceBackend:
    """Build the speech backend.

    ``ALJABR_VOICE_BACKEND=termux`` with missing tools raises ``VoiceError``
    (``unavailable``); ``auto`` falls back to text mode instead.
    """
    mode = detect_mode(settings, which)
    if mode == MODE_TERMUX:
        if not termux_tools_present(which):
            raise VoiceError("Termux:API speech tools are not installed", code="unavailable")
        return VoiceBackend(
            mode=MODE_TERMUX,
            stt=TermuxSTT(runner, timeout=settings.stt_timeout),
            tts=TermuxTTS(
                runner,
                language=settings.tts_language,
                region=settings.tts_region,
                engine=settings.tts_engine,
                pitch=settings.tts_pitch,
                rate=settings.tts_rate,
            ),
            trigger=PushToTalkTrigger(t("voice_prompt", settings.language)),
        )
    return VoiceBackend(
        mode=MODE_CONSOLE,
        stt=ConsoleSTT(prompt="> "),
        tts=ConsoleTTS(),
        trigger=AlwaysActiveTrigger(),
    )
