"""Refuse to store secrets.

Passwords, API keys, tokens and payment card numbers must never end up in
memory (the notes are also sent to the AI provider as context). The check is
deliberately cautious: it may refuse a harmless note, but it should not let a
secret through. It is a safety net, not a guarantee, so users are told not to
save secrets at all.
"""

from __future__ import annotations

import re

_KEYWORDS = (
    r"parol\w*|парол\w*|password|passwd|api[ _-]?key|token|secret|kalit|ключ|pin"
)

# Word edges that treat "_" as a separator, so OPENAI_API_KEY and TOKEN_VALUE match
# (a plain \b would not, because "_" counts as a word character).
_START = r"(?<![^\W_])"
_END = r"(?![^\W_])"
_KEYWORD = rf"{_START}(?:{_KEYWORDS})(?:_\w*)?{_END}"

_PATTERNS = (
    # OpenAI-style keys and bearer tokens
    re.compile(r"sk-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{8,}"),
    # "password: xyz", "OPENAI_API_KEY = xyz"
    re.compile(rf"(?i){_KEYWORD}\s*[:=]\s*\S+"),
    # natural language: "parolim 12345", "my pin is 4821", "пароль от почты qwerty123"
    # (a keyword followed shortly by a word of 4+ characters that contains a digit)
    re.compile(rf"(?i){_KEYWORD}[^\n]{{0,20}}?\s(?=\S{{4,}})\S*\d\S*"),
)

_LONG_TOKEN = re.compile(r"\b[A-Za-z0-9_\-+/=]{32,}\b")
_CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


def _luhn_valid(digits: str) -> bool:
    total = 0
    for index, char in enumerate(reversed(digits)):
        number = int(char)
        if index % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


def _has_card_number(text: str) -> bool:
    for match in _CARD_CANDIDATE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if 13 <= len(digits) <= 19 and _luhn_valid(digits):
            return True
    return False


def _has_long_random_token(text: str) -> bool:
    for match in _LONG_TOKEN.finditer(text):
        token = match.group()
        if any(c.isdigit() for c in token) and any(c.isalpha() for c in token):
            return True
    return False


def contains_sensitive(text: str) -> bool:
    """True if ``text`` looks like it contains a password, key, token or card number."""
    if any(pattern.search(text) for pattern in _PATTERNS):
        return True
    return _has_card_number(text) or _has_long_random_token(text)
