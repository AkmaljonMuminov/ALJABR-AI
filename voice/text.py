"""Prepare AI replies for speech."""

from __future__ import annotations

import re

MAX_SPOKEN_CHARS = 1500

_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_URL = re.compile(r"https?://\S+")
_MARKDOWN_CHARS = re.compile(r"[*_`#>~|]")
_BULLET = re.compile(r"(?m)^\s*[-+•]\s+")
_SPACES = re.compile(r"\s+")


def clean_for_speech(text: str, max_chars: int = MAX_SPOKEN_CHARS) -> str:
    """Remove markdown, code blocks and links; shorten very long answers.

    Long answers are cut at a sentence end where possible. The full text is
    still shown on screen by the session.
    """
    text = _CODE_BLOCK.sub(" ", text)
    text = _URL.sub(" ", text)
    text = _BULLET.sub("", text)
    text = _MARKDOWN_CHARS.sub("", text)
    text = _SPACES.sub(" ", text).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    boundary = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if boundary > max_chars // 2:
        return cut[: boundary + 1]
    return cut.rstrip()
