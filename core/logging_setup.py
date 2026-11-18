"""Secure logging for ALJABR AI.

Every log line (including tracebacks) passes through ``redact`` so API keys,
bearer tokens and ``password=...`` style values never reach disk or console.
"""

from __future__ import annotations

import copy
import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from typing import Iterable, Tuple

LOGGER_NAME = "aljabr"
LOG_FILE_NAME = "aljabr.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
MIN_SECRET_LENGTH = 4
REDACTED = "***"

_OPENAI_STYLE_KEY = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
_BEARER_TOKEN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{8,}")
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Za-z0-9_]*?(?:api[_-]?key|token|password|passwd|secret)[A-Za-z0-9_]*)"
    r"\s*[=:]\s*(\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """Mask known secret values and common secret patterns in ``text``."""
    usable = sorted(
        {s for s in secrets if s and len(s) >= MIN_SECRET_LENGTH},
        key=len,
        reverse=True,
    )
    for secret in usable:
        text = text.replace(secret, REDACTED)
    text = _OPENAI_STYLE_KEY.sub("sk-" + REDACTED, text)
    text = _BEARER_TOKEN.sub(lambda m: m.group(1) + REDACTED, text)
    text = _SECRET_ASSIGNMENT.sub(lambda m: m.group(1) + "=" + REDACTED, text)
    return text


class RedactingFormatter(logging.Formatter):
    """Formatter that redacts secrets from the fully formatted record.

    With ``show_traceback=False`` exception details are left out, which keeps
    the mobile console short while the log file still gets the full traceback.
    """

    def __init__(
        self,
        fmt: str = LOG_FORMAT,
        datefmt=None,
        secrets: Iterable[str] = (),
        show_traceback: bool = True,
    ):
        super().__init__(fmt, datefmt)
        self._secrets: Tuple[str, ...] = tuple(secrets)
        self._show_traceback = show_traceback

    def format(self, record: logging.LogRecord) -> str:
        if not self._show_traceback and (record.exc_info or record.exc_text or record.stack_info):
            record = copy.copy(record)
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
        return redact(super().format(record), self._secrets)


def get_logger(name: str = "") -> logging.Logger:
    """Return the project logger, or a child logger ``aljabr.<name>``."""
    return logging.getLogger(f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME)


def close_logging(logger: logging.Logger) -> None:
    """Close and detach all handlers from ``logger``."""
    for handler in list(logger.handlers):
        try:
            handler.close()
        finally:
            logger.removeHandler(handler)


def _restrict_permissions(path) -> None:
    """Make the log file private (owner read/write) where the OS supports it."""
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def setup_logging(settings, extra_secrets: Iterable[str] = ()) -> logging.Logger:
    """Configure the ``aljabr`` logger and return it.

    * Console shows WARNING and above (DEBUG when the level is DEBUG), so the
      mobile terminal stays quiet.
    * A rotating file keeps the configured level. If the log directory cannot
      be used, the app keeps running with console logging only.
    * Safe to call repeatedly: previous handlers are removed first.
    """
    logger = logging.getLogger(LOGGER_NAME)
    close_logging(logger)

    level = getattr(logging, settings.log_level)
    logger.setLevel(level)
    logger.propagate = False

    secrets = tuple(settings.secret_values()) + tuple(extra_secrets)
    formatter = RedactingFormatter(LOG_FORMAT, secrets=secrets)

    debug = level == logging.DEBUG
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if debug else logging.WARNING)
    console.setFormatter(RedactingFormatter(LOG_FORMAT, secrets=secrets, show_traceback=debug))
    logger.addHandler(console)

    log_path = settings.log_dir / LOG_FILE_NAME
    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("File logging disabled (%s). Using console only.", exc)
    else:
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        _restrict_permissions(log_path)

    return logger
