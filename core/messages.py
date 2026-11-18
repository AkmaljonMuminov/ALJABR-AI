"""User-facing messages (Uzbek by default, plus Russian and English).

All text shown to the user lives here so that code stays in English and
translations stay in one place. Use ``t(key, lang, **values)`` to fetch text.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "uz"

MESSAGES = {
    "uz": {
        "greeting": "Salom! Men ALJABR AI — shaxsiy sun'iy intellekt yordamchingizman.",
        "core_ready": (
            "ALJABR CORE ishga tushdi (1-bosqich). "
            "Ovoz, xotira va boshqa modullar keyingi bosqichlarda qo'shiladi."
        ),
        "wake_hint": (
            "Uyg'otish iborasi: «{wake_phrase}» "
            "(ovozli tizim 3-bosqichda faollashadi)."
        ),
        "check_title": "Tizim tekshiruvi",
        "check_python": "Python versiyasi",
        "check_data_dir": "Ma'lumotlar papkasi",
        "check_log_dir": "Log papkasi",
        "check_api_key": "AI API kaliti",
        "detail_python": "{version}",
        "detail_python_old": "{version} (kamida {minimum} kerak)",
        "detail_writable": "yozish mumkin: {path}",
        "detail_not_writable": "yozib bo'lmaydi: {path}",
        "detail_key_set": "sozlangan",
        "detail_key_missing": "sozlanmagan (2-bosqichda kerak bo'ladi)",
        "status_ok": "OK",
        "status_fail": "XATO",
        "status_optional": "ixtiyoriy",
        "check_ok": "Barcha majburiy tekshiruvlar muvaffaqiyatli.",
        "check_fail": "Ba'zi majburiy tekshiruvlar muvaffaqiyatsiz tugadi.",
        "config_error": "Sozlamalarda xatolik: {detail}",
        "unexpected_error": "Kutilmagan xatolik yuz berdi. Tafsilotlar log faylida.",
        "interrupted": "To'xtatildi.",
        "shutdown": "ALJABR AI to'xtatildi.",
    },
    "ru": {
        "greeting": "Здравствуйте! Я ALJABR AI — ваш персональный ИИ-ассистент.",
        "core_ready": (
            "ALJABR CORE запущен (этап 1). "
            "Голос, память и другие модули появятся на следующих этапах."
        ),
        "wake_hint": (
            "Фраза активации: «{wake_phrase}» "
            "(голосовая система будет включена на этапе 3)."
        ),
        "check_title": "Проверка системы",
        "check_python": "Версия Python",
        "check_data_dir": "Папка данных",
        "check_log_dir": "Папка логов",
        "check_api_key": "API-ключ ИИ",
        "detail_python": "{version}",
        "detail_python_old": "{version} (требуется минимум {minimum})",
        "detail_writable": "запись возможна: {path}",
        "detail_not_writable": "запись невозможна: {path}",
        "detail_key_set": "настроен",
        "detail_key_missing": "не настроен (понадобится на этапе 2)",
        "status_ok": "OK",
        "status_fail": "ОШИБКА",
        "status_optional": "необязательно",
        "check_ok": "Все обязательные проверки пройдены.",
        "check_fail": "Некоторые обязательные проверки не пройдены.",
        "config_error": "Ошибка в настройках: {detail}",
        "unexpected_error": "Произошла непредвиденная ошибка. Подробности в файле логов.",
        "interrupted": "Остановлено.",
        "shutdown": "ALJABR AI остановлен.",
    },
    "en": {
        "greeting": "Hello! I am ALJABR AI, your personal AI assistant.",
        "core_ready": (
            "ALJABR CORE is running (Phase 1). "
            "Voice, memory and other modules arrive in later phases."
        ),
        "wake_hint": (
            "Wake phrase: “{wake_phrase}” "
            "(the voice system is enabled in Phase 3)."
        ),
        "check_title": "System check",
        "check_python": "Python version",
        "check_data_dir": "Data directory",
        "check_log_dir": "Log directory",
        "check_api_key": "AI API key",
        "detail_python": "{version}",
        "detail_python_old": "{version} (minimum {minimum} required)",
        "detail_writable": "writable: {path}",
        "detail_not_writable": "not writable: {path}",
        "detail_key_set": "configured",
        "detail_key_missing": "not configured (needed in Phase 2)",
        "status_ok": "OK",
        "status_fail": "FAIL",
        "status_optional": "optional",
        "check_ok": "All required checks passed.",
        "check_fail": "Some required checks failed.",
        "config_error": "Configuration error: {detail}",
        "unexpected_error": "An unexpected error occurred. See the log file for details.",
        "interrupted": "Interrupted.",
        "shutdown": "ALJABR AI stopped.",
    },
}


def t(key: str, lang: str = DEFAULT_LANGUAGE, **values: object) -> str:
    """Return the message for ``key`` in ``lang``.

    Falls back to the default language, then to the key itself, and never
    raises on missing or mismatched format placeholders.
    """
    table = MESSAGES.get(lang) or MESSAGES[DEFAULT_LANGUAGE]
    template = table.get(key) or MESSAGES[DEFAULT_LANGUAGE].get(key) or key
    try:
        return template.format(**values)
    except (KeyError, IndexError, ValueError):
        return template
