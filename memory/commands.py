"""Chat commands for managing memory.

    /remember <text>      save a note (the only way a note is created)
    /memories [words]     list notes, or search them
    /edit <id> <text>     change a note
    /forget <id>          delete one note
    /forget all [yes]     delete every note (needs the confirmation word)

``make_memory_handler`` returns a function ``handler(line) -> str | None``;
it returns ``None`` for anything that is not a memory command, so the chat
loop can pass that line on to the AI.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from core.errors import MemoryStoreError
from core.messages import MESSAGES, t

CONFIRM_WORDS = ("ha", "yes", "да")
CONFIRM_WORD_FOR = {"uz": "ha", "ru": "да", "en": "yes"}
MAX_LISTED = 20


def _error_text(exc: MemoryStoreError, store, lang: str) -> str:
    key = f"mem_err_{exc.code}"
    if key not in MESSAGES["uz"]:
        key = "mem_err_storage"
    return t(key, lang, limit=store.max_chars if exc.code == "too_long" else store.max_items)


def _list_text(items, title_key: str, lang: str) -> str:
    lines = [t(title_key, lang, count=len(items))]
    for item in items[:MAX_LISTED]:
        lines.append(t("mem_item", lang, id=item.id, text=item.content))
    if len(items) > MAX_LISTED:
        lines.append(t("mem_more", lang, count=len(items) - MAX_LISTED))
    return "\n".join(lines)


def make_memory_handler(
    store, lang: str, logger: Optional[logging.Logger] = None
) -> Callable[[str], Optional[str]]:
    def handler(line: str) -> Optional[str]:
        parts = line.strip().split(None, 1)
        if not parts:
            return None
        command = parts[0].lower()
        argument = parts[1].strip() if len(parts) > 1 else ""
        try:
            if command == "/remember":
                return _remember(argument)
            if command == "/memories":
                return _memories(argument)
            if command == "/edit":
                return _edit(argument)
            if command == "/forget":
                return _forget(argument)
        except MemoryStoreError as exc:
            if exc.code == "storage" and logger is not None:
                logger.warning("Memory storage error: %s", exc)
            return _error_text(exc, store, lang)
        return None

    def _remember(argument: str) -> str:
        if not argument:
            return t("mem_usage", lang)
        item = store.add(argument)
        return t("mem_saved", lang, id=item.id, text=item.content)

    def _memories(argument: str) -> str:
        items = store.search(argument) if argument else store.list()
        if not items:
            return t("mem_search_none" if argument else "mem_none", lang)
        return _list_text(items, "mem_search_title" if argument else "mem_list_title", lang)

    def _parse_id(raw: str) -> Optional[int]:
        return int(raw) if raw.isdigit() else None

    def _edit(argument: str) -> str:
        parts = argument.split(None, 1)
        if len(parts) < 2:
            return t("mem_usage", lang)
        item_id = _parse_id(parts[0].lstrip("#"))
        if item_id is None:
            return t("mem_bad_id", lang)
        item = store.update(item_id, parts[1])
        return t("mem_updated", lang, id=item.id, text=item.content)

    def _forget(argument: str) -> str:
        if not argument:
            return t("mem_usage", lang)
        words = argument.split()
        if words[0].lower() == "all":
            count = store.count()
            if count == 0:
                return t("mem_none", lang)
            if len(words) == 2 and words[1].lower() in CONFIRM_WORDS:
                return t("mem_cleared", lang, count=store.delete_all())
            return t("mem_forget_all_confirm", lang, count=count,
                     word=CONFIRM_WORD_FOR.get(lang, "yes"))
        item_id = _parse_id(words[0].lstrip("#"))
        if item_id is None or len(words) != 1:
            return t("mem_bad_id", lang)
        store.delete(item_id)
        return t("mem_deleted", lang, id=item_id)

    return handler
