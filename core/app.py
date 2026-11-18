"""ALJABR CORE application lifecycle and system checks."""

from __future__ import annotations

import logging
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from core import APP_NAME, __version__
from core.logging_setup import close_logging, get_logger
from core.messages import t

MIN_PYTHON = (3, 9)


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one system check. Non-required checks never fail the run."""

    name: str
    ok: bool
    detail: str
    required: bool = True


def _check_writable(directory: Path) -> Tuple[bool, str]:
    """Return (ok, error) after trying to create a file inside ``directory``."""
    probe = directory / f".write_test_{uuid.uuid4().hex}"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe.write_text("ok", encoding="utf-8")
    except OSError as exc:
        return False, str(exc)
    finally:
        try:
            probe.unlink()
        except OSError:
            pass
    return True, ""


class Application:
    """Owns the lifecycle of ALJABR and exposes health checks.

    Later phases (brain, voice, memory...) will be created and started here.
    """

    def __init__(self, settings, logger: Optional[logging.Logger] = None) -> None:
        self.settings = settings
        self.logger = logger or get_logger()
        self.running = False

    def _t(self, key: str, **values: object) -> str:
        return t(key, self.settings.language, **values)

    def start(self) -> None:
        """Prepare runtime directories. Never raises for filesystem problems."""
        for directory in (self.settings.data_dir, self.settings.log_dir):
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                self.logger.warning("Cannot create directory %s: %s", directory, exc)
        self.running = True
        self.logger.info(
            "%s %s started (env=%s, language=%s)",
            APP_NAME,
            __version__,
            self.settings.environment,
            self.settings.language,
        )

    def stop(self) -> None:
        """Stop the application and release logging handlers. Safe to repeat."""
        if self.running:
            self.logger.info("%s stopped", APP_NAME)
        self.running = False
        close_logging(self.logger)

    def banner(self) -> List[str]:
        return [
            self._t("greeting"),
            self._t("core_ready"),
            self._t("wake_hint", wake_phrase=self.settings.wake_phrase),
        ]

    def run_checks(self) -> List[CheckResult]:
        """Run environment checks. Secret values are never included."""
        results: List[CheckResult] = []

        version = ".".join(str(part) for part in sys.version_info[:3])
        minimum = ".".join(str(part) for part in MIN_PYTHON)
        python_ok = sys.version_info[:2] >= MIN_PYTHON
        results.append(
            CheckResult(
                self._t("check_python"),
                python_ok,
                self._t("detail_python" if python_ok else "detail_python_old",
                        version=version, minimum=minimum),
            )
        )

        for label_key, directory in (
            ("check_data_dir", self.settings.data_dir),
            ("check_log_dir", self.settings.log_dir),
        ):
            writable, error = _check_writable(directory)
            if not writable:
                self.logger.warning("Directory check failed for %s: %s", directory, error)
            results.append(
                CheckResult(
                    self._t(label_key),
                    writable,
                    self._t("detail_writable" if writable else "detail_not_writable",
                            path=directory),
                )
            )

        model_set = bool(self.settings.ai_model)
        results.append(
            CheckResult(
                self._t("check_ai_model"),
                model_set,
                self._t(
                    "detail_model_set" if model_set else "detail_model_missing",
                    provider=self.settings.ai_provider,
                    model=self.settings.ai_model,
                ),
                required=False,
            )
        )

        key_set = bool(self.settings.openai_api_key)
        results.append(
            CheckResult(
                self._t("check_api_key"),
                key_set,
                self._t("detail_key_set" if key_set else "detail_key_missing"),
                required=False,
            )
        )
        return results

    def format_report(self, results: List[CheckResult]) -> List[str]:
        """Turn check results into printable lines, ending with a verdict."""
        lines = [self._t("check_title") + ":"]
        for result in results:
            if result.ok:
                status = self._t("status_ok")
            elif result.required:
                status = self._t("status_fail")
            else:
                status = self._t("status_optional")
            lines.append(f"  [{status}] {result.name}: {result.detail}")
        passed = all(r.ok for r in results if r.required)
        lines.append(self._t("check_ok" if passed else "check_fail"))
        return lines

    @staticmethod
    def checks_passed(results: List[CheckResult]) -> bool:
        return all(r.ok for r in results if r.required)
