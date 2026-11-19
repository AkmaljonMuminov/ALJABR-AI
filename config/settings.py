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

VOICE_BACKENDS = ("auto", "termux", "console")
DEFAULT_TTS_PITCH = 1.1   # slightly raised for a female-sounding voice (verify on device)
DEFAULT_TTS_RATE = 0.95   # slightly slower for a calm delivery
DEFAULT_STT_TIMEOUT = 20
_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._-]{0,64}$")
_USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DEFAULT_USER_ID = "owner"
DEFAULT_MEMORY_PROMPT_ITEMS = 10
_TRUE_VALUES = ("1", "true", "yes", "on")
_FALSE_VALUES = ("0", "false", "no", "off", "")

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
    voice_backend: str = "auto"
    tts_language: str = "uz"
    tts_region: str = ""
    tts_engine: str = ""
    tts_pitch: float = DEFAULT_TTS_PITCH
    tts_rate: float = DEFAULT_TTS_RATE
    stt_timeout: int = DEFAULT_STT_TIMEOUT
    voice_require_wake: bool = False
    memory_enabled: bool = True
    memory_in_prompt: bool = True
    memory_max_prompt_items: int = DEFAULT_MEMORY_PROMPT_ITEMS
    user_id: str = DEFAULT_USER_ID

    @property
    def db_path(self) -> Path:
        """Location of the SQLite database (inside the data directory)."""
        return self.data_dir / "aljabr.db"

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


def _float_in_range(values, key: str, default: float, minimum: float, maximum: float) -> float:
    raw = _get(values, key, str(default))
    try:
        number = float(raw)
    except ValueError:
        raise ConfigError(f"{key} must be a number (got {raw!r})") from None
    if not minimum <= number <= maximum:
        raise ConfigError(f"{key} must be between {minimum} and {maximum} (got {number})")
    return number


def _bool(values, key: str, default: bool = False) -> bool:
    raw = _get(values, key, "true" if default else "false").lower()
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise ConfigError(f"{key} must be true or false (got {raw!r})")


def _token(values, key: str, default: str) -> str:
    """A short identifier (language, region, engine package) with no spaces or symbols."""
    raw = _get(values, key, default)
    if not _TOKEN_PATTERN.match(raw):
        raise ConfigError(f"{key} may only contain letters, digits, '.', '_' and '-'")
    return raw


def _user_id(values, key: str, default: str) -> str:
    raw = _get(values, key, default)
    if not _USER_ID_PATTERN.match(raw):
        raise ConfigError(
            f"{key} must start with a letter or digit and contain only letters, "
            "digits, '.', '_' and '-' (max 64 characters)"
        )
    return raw


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
        voice_backend=_choice(values, "ALJABR_VOICE_BACKEND", "auto", VOICE_BACKENDS),
        tts_language=_token(values, "ALJABR_TTS_LANGUAGE", "uz") or "uz",
        tts_region=_token(values, "ALJABR_TTS_REGION", ""),
        tts_engine=_token(values, "ALJABR_TTS_ENGINE", ""),
        tts_pitch=_float_in_range(values, "ALJABR_TTS_PITCH", DEFAULT_TTS_PITCH, 0.5, 2.0),
        tts_rate=_float_in_range(values, "ALJABR_TTS_RATE", DEFAULT_TTS_RATE, 0.5, 2.0),
        stt_timeout=_int_in_range(values, "ALJABR_STT_TIMEOUT", DEFAULT_STT_TIMEOUT, 5, 60),
        voice_require_wake=_bool(values, "ALJABR_VOICE_REQUIRE_WAKE", False),
        memory_enabled=_bool(values, "ALJABR_MEMORY_ENABLED", True),
        memory_in_prompt=_bool(values, "ALJABR_MEMORY_IN_PROMPT", True),
        memory_max_prompt_items=_int_in_range(
            values, "ALJABR_MEMORY_MAX_PROMPT_ITEMS", DEFAULT_MEMORY_PROMPT_ITEMS, 1, 50
        ),
        user_id=_user_id(values, "ALJABR_USER_ID", DEFAULT_USER_ID),
    )
