"""Run external commands safely (no shell, with a timeout)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Optional, Sequence

from core.errors import VoiceError


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class CommandRunner:
    """Thin wrapper around ``subprocess.run``.

    * Arguments are passed as a list; no shell is involved, so text can never
      be interpreted as a command.
    * Every low-level failure is converted to ``VoiceError``.
    """

    def run(
        self,
        args: Sequence[str],
        *,
        input_text: Optional[str] = None,
        timeout: float = 20,
    ) -> CommandResult:
        try:
            completed = subprocess.run(
                list(args),
                input=input_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError:
            raise VoiceError(f"command not found: {args[0]}", code="unavailable") from None
        except subprocess.TimeoutExpired:
            raise VoiceError(f"{args[0]} timed out after {timeout}s", code="timeout") from None
        except OSError as exc:
            raise VoiceError(
                f"cannot run {args[0]}: {type(exc).__name__}", code="failed"
            ) from None
        return CommandResult(completed.returncode, completed.stdout or "", completed.stderr or "")
