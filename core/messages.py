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
            "ALJABR ishga tushdi. AI bilan suhbat: python main.py --chat, ovozli suhbat: python main.py --voice. "
            "Ovoz, xotira va boshqa modullar keyingi bosqichlarda qo'shiladi."
        ),
        "wake_hint": (
            "Uyg'otish iborasi: «{wake_phrase}» "
            "(ALJABR_VOICE_REQUIRE_WAKE=true bo'lsa, ovozli rejimda ishlatiladi)."
        ),
        "check_title": "Tizim tekshiruvi",
        "check_python": "Python versiyasi",
        "check_data_dir": "Ma'lumotlar papkasi",
        "check_log_dir": "Log papkasi",
        "check_ai_model": "AI modeli",
        "check_api_key": "AI API kaliti",
        "detail_python": "{version}",
        "detail_python_old": "{version} (kamida {minimum} kerak)",
        "detail_writable": "yozish mumkin: {path}",
        "detail_not_writable": "yozib bo'lmaydi: {path}",
        "detail_model_set": "{provider} / {model}",
        "detail_model_missing": "sozlanmagan (.env da ALJABR_AI_MODEL ni kiriting)",
        "detail_key_set": "sozlangan",
        "detail_key_missing": "sozlanmagan (AI suhbat uchun kerak)",
        "status_ok": "OK",
        "status_fail": "XATO",
        "status_optional": "ixtiyoriy",
        "check_ok": "Barcha majburiy tekshiruvlar muvaffaqiyatli.",
        "check_fail": "Ba'zi majburiy tekshiruvlar muvaffaqiyatsiz tugadi.",
        "config_error": "Sozlamalarda xatolik: {detail}",
        "unexpected_error": "Kutilmagan xatolik yuz berdi. Tafsilotlar log faylida.",
        "interrupted": "To'xtatildi.",
        "shutdown": "ALJABR AI to'xtatildi.",
        "chat_intro": (
            "Suhbat boshlandi. Chiqish: /exit, suhbat tarixini tozalash: /clear."
        ),
        "history_cleared": "Suhbat tarixi tozalandi.",
        "input_empty": "Savol bo'sh bo'lmasligi kerak.",
        "input_too_long": "Savol juda uzun. Iltimos, qisqaroq yozing.",
        "provider_no_api_key": (
            "AI API kaliti sozlanmagan. .env faylida OPENAI_API_KEY ni kiriting."
        ),
        "provider_no_model": (
            "AI modeli sozlanmagan. .env faylida ALJABR_AI_MODEL ni kiriting."
        ),
        "provider_auth": "AI kaliti qabul qilinmadi. Kalitni tekshiring.",
        "provider_rate_limit": (
            "AI xizmati hozir band yoki limit tugagan. Birozdan keyin urinib ko'ring."
        ),
        "provider_network": (
            "AI xizmatiga ulanib bo'lmadi. Internet aloqasini tekshiring."
        ),
        "provider_server": "AI xizmatida vaqtinchalik nosozlik. Keyinroq urinib ko'ring.",
        "provider_bad_response": "AI xizmatidan noto'g'ri javob keldi. Qayta urinib ko'ring.",
        "provider_error": "AI so'rovi bajarilmadi. Tafsilotlar log faylida.",
        "check_voice": "Ovoz tizimi",
        "detail_voice_termux": "Termux:API topildi (mikrofon va ovoz)",
        "detail_voice_console": "matn rejimi (Termux:API topilmadi)",
        "voice_intro": (
            "Ovozli rejim. Gapirish uchun Enter bosing, chiqish uchun q yozing."
        ),
        "voice_prompt": "[Enter = gapirish, q = chiqish] ",
        "voice_listening": "Tinglayapman...",
        "voice_heard": "Siz: {text}",
        "voice_ready_phrase": "Eshitaman.",
        "voice_console_mode": (
            "Termux:API topilmadi, shuning uchun matn rejimida ishlayapman "
            "(ovoz o'rniga yozasiz va o'qiysiz)."
        ),
        "voice_no_speech": "Hech narsa eshitilmadi. Qayta urinib ko'ring.",
        "voice_unavailable": (
            "Ovoz xizmati topilmadi. Termux:API ilovasini va "
            "'pkg install termux-api' ni o'rnating."
        ),
        "voice_permission": (
            "Mikrofon ruxsati yo'q. Telefon sozlamalarida Termux:API ga "
            "mikrofon ruxsatini bering."
        ),
        "voice_timeout": "Ovoz xizmati javob bermadi (vaqt tugadi). Qayta urinib ko'ring.",
        "voice_failed": "Ovoz tizimida xatolik. Tafsilotlar log faylida.",
    },
    "ru": {
        "greeting": "Здравствуйте! Я ALJABR AI — ваш персональный ИИ-ассистент.",
        "core_ready": (
            "ALJABR запущен. Чат с ИИ: python main.py --chat, голосовой чат: python main.py --voice. "
            "Голос, память и другие модули появятся на следующих этапах."
        ),
        "wake_hint": (
            "Фраза активации: «{wake_phrase}» "
            "(используется в голосовом режиме при ALJABR_VOICE_REQUIRE_WAKE=true)."
        ),
        "check_title": "Проверка системы",
        "check_python": "Версия Python",
        "check_data_dir": "Папка данных",
        "check_log_dir": "Папка логов",
        "check_ai_model": "Модель ИИ",
        "check_api_key": "API-ключ ИИ",
        "detail_python": "{version}",
        "detail_python_old": "{version} (требуется минимум {minimum})",
        "detail_writable": "запись возможна: {path}",
        "detail_not_writable": "запись невозможна: {path}",
        "detail_model_set": "{provider} / {model}",
        "detail_model_missing": "не настроена (укажите ALJABR_AI_MODEL в .env)",
        "detail_key_set": "настроен",
        "detail_key_missing": "не настроен (нужен для чата с ИИ)",
        "status_ok": "OK",
        "status_fail": "ОШИБКА",
        "status_optional": "необязательно",
        "check_ok": "Все обязательные проверки пройдены.",
        "check_fail": "Некоторые обязательные проверки не пройдены.",
        "config_error": "Ошибка в настройках: {detail}",
        "unexpected_error": "Произошла непредвиденная ошибка. Подробности в файле логов.",
        "interrupted": "Остановлено.",
        "shutdown": "ALJABR AI остановлен.",
        "chat_intro": "Чат начат. Выход: /exit, очистить историю: /clear.",
        "history_cleared": "История чата очищена.",
        "input_empty": "Вопрос не должен быть пустым.",
        "input_too_long": "Вопрос слишком длинный. Пожалуйста, сократите его.",
        "provider_no_api_key": "API-ключ ИИ не настроен. Укажите OPENAI_API_KEY в файле .env.",
        "provider_no_model": "Модель ИИ не настроена. Укажите ALJABR_AI_MODEL в файле .env.",
        "provider_auth": "API-ключ не принят. Проверьте ключ.",
        "provider_rate_limit": (
            "Сервис ИИ перегружен или лимит исчерпан. Попробуйте позже."
        ),
        "provider_network": "Не удалось подключиться к сервису ИИ. Проверьте интернет.",
        "provider_server": "Временная неполадка сервиса ИИ. Попробуйте позже.",
        "provider_bad_response": "Сервис ИИ вернул некорректный ответ. Попробуйте ещё раз.",
        "provider_error": "Запрос к ИИ не выполнен. Подробности в файле логов.",
        "check_voice": "Голосовая система",
        "detail_voice_termux": "Termux:API найден (микрофон и голос)",
        "detail_voice_console": "текстовый режим (Termux:API не найден)",
        "voice_intro": (
            "Голосовой режим. Нажмите Enter, чтобы говорить, или введите q для выхода."
        ),
        "voice_prompt": "[Enter = говорить, q = выход] ",
        "voice_listening": "Слушаю...",
        "voice_heard": "Вы: {text}",
        "voice_ready_phrase": "Слушаю вас.",
        "voice_console_mode": (
            "Termux:API не найден, поэтому работаю в текстовом режиме "
            "(вы пишете и читаете вместо голоса)."
        ),
        "voice_no_speech": "Ничего не слышно. Попробуйте ещё раз.",
        "voice_unavailable": (
            "Голосовой сервис не найден. Установите приложение Termux:API и "
            "выполните 'pkg install termux-api'."
        ),
        "voice_permission": (
            "Нет доступа к микрофону. Дайте Termux:API разрешение на микрофон "
            "в настройках телефона."
        ),
        "voice_timeout": "Голосовой сервис не ответил (время истекло). Попробуйте ещё раз.",
        "voice_failed": "Ошибка голосовой системы. Подробности в файле логов.",
    },
    "en": {
        "greeting": "Hello! I am ALJABR AI, your personal AI assistant.",
        "core_ready": (
            "ALJABR is running. AI chat: python main.py --chat, voice chat: python main.py --voice. "
            "Voice, memory and other modules arrive in later phases."
        ),
        "wake_hint": (
            "Wake phrase: “{wake_phrase}” "
            "(used in voice mode when ALJABR_VOICE_REQUIRE_WAKE=true)."
        ),
        "check_title": "System check",
        "check_python": "Python version",
        "check_data_dir": "Data directory",
        "check_log_dir": "Log directory",
        "check_ai_model": "AI model",
        "check_api_key": "AI API key",
        "detail_python": "{version}",
        "detail_python_old": "{version} (minimum {minimum} required)",
        "detail_writable": "writable: {path}",
        "detail_not_writable": "not writable: {path}",
        "detail_model_set": "{provider} / {model}",
        "detail_model_missing": "not set (put ALJABR_AI_MODEL in .env)",
        "detail_key_set": "configured",
        "detail_key_missing": "not configured (needed for AI chat)",
        "status_ok": "OK",
        "status_fail": "FAIL",
        "status_optional": "optional",
        "check_ok": "All required checks passed.",
        "check_fail": "Some required checks failed.",
        "config_error": "Configuration error: {detail}",
        "unexpected_error": "An unexpected error occurred. See the log file for details.",
        "interrupted": "Interrupted.",
        "shutdown": "ALJABR AI stopped.",
        "chat_intro": "Chat started. Quit: /exit, clear history: /clear.",
        "history_cleared": "Chat history cleared.",
        "input_empty": "The question must not be empty.",
        "input_too_long": "The question is too long. Please shorten it.",
        "provider_no_api_key": "The AI API key is not set. Put OPENAI_API_KEY in your .env file.",
        "provider_no_model": "The AI model is not set. Put ALJABR_AI_MODEL in your .env file.",
        "provider_auth": "The AI key was rejected. Please check the key.",
        "provider_rate_limit": "The AI service is busy or the limit is reached. Try again later.",
        "provider_network": "Could not reach the AI service. Check your internet connection.",
        "provider_server": "The AI service has a temporary problem. Try again later.",
        "provider_bad_response": "The AI service returned an invalid reply. Please try again.",
        "provider_error": "The AI request failed. See the log file for details.",
        "check_voice": "Voice system",
        "detail_voice_termux": "Termux:API found (microphone and speech)",
        "detail_voice_console": "text mode (Termux:API not found)",
        "voice_intro": "Voice mode. Press Enter to speak, or type q to quit.",
        "voice_prompt": "[Enter = speak, q = quit] ",
        "voice_listening": "Listening...",
        "voice_heard": "You: {text}",
        "voice_ready_phrase": "I'm listening.",
        "voice_console_mode": (
            "Termux:API was not found, so I am running in text mode "
            "(you type and read instead of speaking)."
        ),
        "voice_no_speech": "I did not hear anything. Please try again.",
        "voice_unavailable": (
            "Voice service not found. Install the Termux:API app and run "
            "'pkg install termux-api'."
        ),
        "voice_permission": (
            "No microphone permission. Grant Termux:API the microphone permission "
            "in your phone settings."
        ),
        "voice_timeout": "The voice service did not respond (timed out). Please try again.",
        "voice_failed": "Voice system error. See the log file for details.",
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
