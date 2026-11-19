"""Test doubles for the voice tests (no microphone, speaker or network)."""

from __future__ import annotations

from core.errors import VoiceError
from voice.activation import ActivationTrigger
from voice.interfaces import SpeechToText, TextToSpeech
from voice.runner import CommandResult


class FakeRunner:
    """Replays scripted outcomes: CommandResult -> returned, Exception -> raised."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def run(self, args, *, input_text=None, timeout=20):
        self.calls.append({"args": list(args), "input": input_text, "timeout": timeout})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def ok(stdout="", stderr=""):
    return CommandResult(0, stdout, stderr)


def fail(stderr="", stdout="", code=1):
    return CommandResult(code, stdout, stderr)


class FakeSTT(SpeechToText):
    """Returns scripted phrases; an Exception item is raised instead."""

    def __init__(self, *items, echoes_input=False):
        self.items = list(items)
        self.echoes_input = echoes_input
        self.calls = 0

    def listen(self):
        self.calls += 1
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FakeTTS(TextToSpeech):
    def __init__(self, failures=None):
        self.spoken = []
        self._failures = list(failures or [])

    def speak(self, text):
        if self._failures:
            raise self._failures.pop(0)
        self.spoken.append(text)


class ScriptedTrigger(ActivationTrigger):
    def __init__(self, *answers):
        self.answers = list(answers)

    def wait(self):
        return self.answers.pop(0) if self.answers else False


def voice_error(code, message="x"):
    return VoiceError(message, code=code)
