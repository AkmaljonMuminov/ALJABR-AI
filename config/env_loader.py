"""Minimal ``.env`` file parser (no third-party dependency).

Supported syntax::

    # comment
    KEY=value
    export KEY="quoted value"
    KEY='single quoted'
    KEY=value  # inline comment (unquoted values only)

Values are returned as a dict. Nothing is written to ``os.environ``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

from core.errors import ConfigError

_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_value(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        return raw[1:-1]
    # Unquoted: an inline comment starts at " #".
    comment_at = raw.find(" #")
    if comment_at != -1:
        raw = raw[:comment_at]
    return raw.strip()


def parse_env_text(text: str) -> Dict[str, str]:
    """Parse ``.env`` formatted text into a dict. Malformed lines are skipped."""
    values: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, raw_value = line.partition("=")
        key = key.strip()
        if not _KEY_PATTERN.match(key):
            continue
        values[key] = _parse_value(raw_value)
    return values


def load_env_file(path) -> Dict[str, str]:
    """Read and parse a ``.env`` file. Raises ``ConfigError`` if unreadable."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"cannot read env file {path}: {exc}") from exc
    return parse_env_text(text)
