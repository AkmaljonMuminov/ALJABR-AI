"""Voice interaction state machine."""

from __future__ import annotations

import enum


class VoiceState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    STOPPED = "stopped"


_ALLOWED = {
    VoiceState.IDLE: {VoiceState.LISTENING, VoiceState.STOPPED},
    VoiceState.LISTENING: {
        VoiceState.IDLE, VoiceState.THINKING, VoiceState.SPEAKING, VoiceState.STOPPED,
    },
    VoiceState.THINKING: {VoiceState.SPEAKING, VoiceState.IDLE, VoiceState.STOPPED},
    VoiceState.SPEAKING: {VoiceState.IDLE, VoiceState.LISTENING, VoiceState.STOPPED},
    VoiceState.STOPPED: set(),
}


class InvalidTransition(ValueError):
    """Raised for a state change the voice loop must never make."""


class VoiceStateMachine:
    def __init__(self) -> None:
        self.state = VoiceState.IDLE

    def transition(self, new_state: VoiceState) -> None:
        if new_state not in _ALLOWED[self.state]:
            raise InvalidTransition(f"{self.state.value} -> {new_state.value}")
        self.state = new_state

    def reset(self) -> None:
        """Return to IDLE after an error or a finished turn (no-op once stopped)."""
        if self.state is not VoiceState.STOPPED:
            self.state = VoiceState.IDLE

    def stop(self) -> None:
        self.state = VoiceState.STOPPED

    @property
    def stopped(self) -> bool:
        return self.state is VoiceState.STOPPED
