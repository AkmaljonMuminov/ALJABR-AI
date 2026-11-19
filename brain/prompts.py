"""System prompt for ALJABR BRAIN."""

from __future__ import annotations

import datetime as _dt

LANGUAGE_NAMES = {
    "uz": "Uzbek (Latin script)",
    "ru": "Russian",
    "en": "English",
}


SPOKEN_STYLE = (
    "Your reply will be read aloud by a speech engine: keep it short (a few "
    "sentences), use plain sentences, and do not use markdown, lists, code, "
    "emojis or links.\n"
)


def build_system_prompt(language: str, today: _dt.date, spoken: bool = False) -> str:
    """Return the system prompt. ``language`` is the user's default language.

    With ``spoken=True`` the model is asked for short, speech-friendly replies.
    """
    language_name = LANGUAGE_NAMES.get(language, LANGUAGE_NAMES["uz"])
    prompt = _base_prompt(language_name, today)
    return prompt + "\n" + SPOKEN_STYLE.rstrip("\n") if spoken else prompt


def _base_prompt(language_name: str, today: _dt.date) -> str:
    return (
        "You are ALJABR AI, a personal AI assistant. "
        "Your voice is calm, professional and concise.\n"
        f"Reply in the language the user writes in; if it is unclear, reply in {language_name}.\n"
        f"Today's date is {today.isoformat()}.\n"
        "Right now you can only chat. You cannot run commands, send messages, "
        "browse the web or remember things after this session, so never claim "
        "to have done any of that.\n"
        "Never ask the user for passwords, API keys or tokens, and never repeat "
        "such secrets if the user shares them.\n"
        "If you are not sure about something, say so instead of guessing."
    )
