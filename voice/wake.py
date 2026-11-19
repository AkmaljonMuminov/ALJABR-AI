"""Wake phrase matching (default: "Salom, ALJABR").

Matching ignores case, punctuation, apostrophes and spaces, so recognisers that
return "salom al jabr", "Salom, Al-Jabr" or "salom aljabr!" all match.

This works on text the speech recogniser already produced. It is NOT a
background wake-word detector (see ``voice/activation.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


def _compact(text: str) -> Tuple[str, List[int]]:
    """Return (letters/digits only, casefolded) and the original index of each kept char."""
    chars: List[str] = []
    positions: List[int] = []
    for index, char in enumerate(text):
        if char.isalnum():
            folded = char.casefold()
            for part in folded:
                chars.append(part)
                positions.append(index)
    return "".join(chars), positions


@dataclass(frozen=True)
class WakeMatch:
    matched: bool
    remainder: str = ""


class WakePhraseMatcher:
    def __init__(self, phrase: str) -> None:
        self.phrase = phrase
        self._needle, _ = _compact(phrase)
        if not self._needle:
            raise ValueError("wake phrase must contain letters or digits")

    def match(self, text: str) -> WakeMatch:
        """Match the wake phrase at the *start* of ``text``.

        ``remainder`` is whatever follows it (the command), with leading
        punctuation and spaces removed; it is '' if only the phrase was said.
        """
        haystack, positions = _compact(text)
        if not haystack.startswith(self._needle):
            return WakeMatch(False)
        last_char_index = positions[len(self._needle) - 1]
        rest = text[last_char_index + 1:]
        # The phrase must end at a word boundary ("aljabrxyz" is not a match).
        if rest and rest[0].isalnum():
            return WakeMatch(False)
        return WakeMatch(True, rest.lstrip(" \t,.;:!?-–—").strip())
