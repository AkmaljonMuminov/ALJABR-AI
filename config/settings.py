"""Validated application settings for ALJABR AI.

Settings come from (highest priority first):

1. Real environment variables
2. A ``.env`` file in the project root (or the file given via ``--env-file``)
3. Built-in defaults

Secrets are wrapped in ``Secret`` so they never appear in ``repr()``/logs.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Tuple
from urllib.parse import urlparse

from config.env_loader import load_env_file
from core.errors import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUPPORTED_LANGUAGES = ("uz", "ru", "en")
VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
VALID_ENVIRONMENTS = ("development", "production", "test")

DEFAULT_WAKE_PHRASE = "Salom, ALJABR"
MAX_WAKE_PHRASE_LENGTH = 60
MAX_MODEL_LENGTH = 100

DEFAULT_AI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AI_TIMEOUT = 30
DEFAULT_AI_MAX_HISTORY = 20
_LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")

_PROVIDER_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._:/\-]*$")


class Secret:
    """Holds a secret string and hides it from ``repr``/``str``."""

    __slots__ = ("_value",)

    def __init__(self, value: str = "") -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __bool__(self) -> bool:
        return bool(self._value)

    def __repr__(self) -> str:
        return "Secret('***')" if self._value else "Secret('')"

    __str__ = __repr__


@dataclass(frozen=True)
class Settings:
    environment: str
    language: str
    wake_phrase: str
    log_level: str
    base_dir: Path
    data_dir: Path
    log_dir: Path
    ai_provider: str
    ai_model: str
    openai_api_key: Secret
    log_max_bytes: int = 1_000_000
    log_backup_count: int = 3
    ai_base_url: str = DEFAULT_AI_BASE_URL
    ai_timeout: int = DEFAULT_AI_TIMEOUT
    ai_max_history: int = DEFAULT_AI_MAX_HISTORY

    def secret_values(self) -> Tuple[str, ...]:
        """Return raw secret values (used only to redact logs)."""
        values = []
        if self.openai_api_key:
            values.append(self.openai_api_key.reveal())
        return tuple(values)


def _get(values: Mapping[str, str], key: str, default: str = "") -> str:
    return (values.get(key) or default).strip()


def _resolve_path(raw: str, base_dir: Path) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (base_dir / path)


def _choice(values, key: str, default: str, allowed: Tuple[str, ...], upper: bool = False) -> str:
    raw = _get(values, key, default)
    value = raw.upper() if upper else raw.lower()
    if value not in allowed:
        raise ConfigError(f"{key} must be one of {', '.join(allowed)} (got {raw!r})")
    return value


def _int_in_range(values, key: str, default: int, minimum: int, maximum: int) -> int:
    raw = _get(values, key, str(default))
    try:
        number = int(raw)
    except ValueError:
        raise ConfigError(f"{key} must be a whole number (got {raw!r})") from None
    if not minimum <= number <= maximum:
        raise ConfigError(f"{key} must be between {minimum} and {maximum} (got {number})")
    return number


def _base_url(values, key: str, default: str) -> str:
    """Validate an API base URL: HTTPS, or HTTP only for a local server."""
    raw = _get(values, key, default).rstrip("/")
    parsed = urlparse(raw)
    if parsed.scheme == "https" and parsed.hostname:
        return raw
    if parsed.scheme == "http" and parsed.hostname in _LOCAL_HOSTS:
        return raw
    raise ConfigError(f"{key} must be an https:// URL (http:// only for localhost)")


def load_settings(
    environ: Optional[Mapping[str, str]] = None,
    base_dir: Optional[Path] = None,
    env_file: Optional[Path] = None,
) -> Settings:
    """Build validated ``Settings``. Raises ``ConfigError`` on invalid input.

    ``environ`` defaults to ``os.environ``. ``base_dir`` is the directory used
    to resolve relative paths and to find ``.env`` (default: project root).
    An explicitly given ``env_file`` must exist; the default ``.env`` is optional.
    """
    base = Path(base_dir).resolve() if base_dir else PROJECT_ROOT
    env = dict(os.environ if environ is None else environ)

    file_values = {}
    if env_file is not None:
        env_path = Path(env_file)
        if not env_path.is_file():
            raise ConfigError(f"env file not found: {env_path}")
        file_values = load_env_file(env_path)
    else:
        default_env = base / ".env"
        if default_env.is_file():
            file_values = load_env_file(default_env)

    values = {**file_values, **env}  # real environment wins over the file

    wake_phrase = _get(values, "ALJABR_WAKE_PHRASE", DEFAULT_WAKE_PHRASE) or DEFAULT_WAKE_PHRASE
    if len(wake_phrase) > MAX_WAKE_PHRASE_LENGTH:
        raise ConfigError(f"ALJABR_WAKE_PHRASE is longer than {MAX_WAKE_PHRASE_LENGTH} characters")

    provider = _get(values, "ALJABR_AI_PROVIDER", "openai").lower()
    if not _PROVIDER_PATTERN.match(provider):
        raise ConfigError(f"ALJABR_AI_PROVIDER has an invalid value: {provider!r}")

    model = _get(values, "ALJABR_AI_MODEL", "")
    if len(model) > MAX_MODEL_LENGTH or not _MODEL_PATTERN.match(model):
        raise ConfigError("ALJABR_AI_MODEL has an invalid value")

    data_dir = _resolve_path(_get(values, "ALJABR_DATA_DIR", "data"), base)
    log_raw = _get(values, "ALJABR_LOG_DIR", "")
    log_dir = _resolve_path(log_raw, base) if log_raw else data_dir / "logs"

    return Settings(
        environment=_choice(values, "ALJABR_ENV", "development", VALID_ENVIRONMENTS),
        language=_choice(values, "ALJABR_LANGUAGE", "uz", SUPPORTED_LANGUAGES),
        wake_phrase=wake_phrase,
        log_level=_choice(values, "ALJABR_LOG_LEVEL", "INFO", VALID_LOG_LEVELS, upper=True),
        base_dir=base,
        data_dir=data_dir,
        log_dir=log_dir,
        ai_provider=provider,
        ai_model=model,
        openai_api_key=Secret(_get(values, "OPENAI_API_KEY")),
        ai_base_url=_base_url(values, "ALJABR_AI_BASE_URL", DEFAULT_AI_BASE_URL),
        ai_timeout=_int_in_range(values, "ALJABR_AI_TIMEOUT", DEFAULT_AI_TIMEOUT, 5, 120),
        ai_max_history=_int_in_range(
            values, "ALJABR_AI_MAX_HISTORY", DEFAULT_AI_MAX_HISTORY, 2, 200
        ),
    )
