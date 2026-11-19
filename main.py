#!/usr/bin/env python3
"""ALJABR AI entry point.

Usage:
    python main.py                 # start and show the greeting
    python main.py --check         # run system checks (exit code 0 if all pass)
    python main.py --chat          # interactive text chat with the AI
    python main.py --ask "Savol"   # ask one question and print the answer
    python main.py --voice         # push-to-talk voice conversation
    python main.py --version
    python main.py --env-file /path/to/.env
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from brain.brain import Brain
from brain.cli import describe_error, run_chat
from brain.factory import create_provider
from config.settings import load_settings
from core import APP_NAME, __version__
from core.app import Application
from core.errors import ConfigError, DatabaseError, InputError, ProviderError, VoiceError
from core.logging_setup import get_logger, setup_logging
from core.messages import DEFAULT_LANGUAGE, t
from database.connection import open_database
from memory.commands import make_memory_handler
from memory.context import make_context_provider
from memory.store import MemoryStore
from voice.factory import MODE_CONSOLE, create_voice
from voice.session import VoiceSession, describe_voice_error

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CONFIG = 2
EXIT_CHECK_FAILED = 3
EXIT_AI = 4
EXIT_VOICE = 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aljabr", description=f"{APP_NAME} personal assistant")
    parser.add_argument("--check", action="store_true", help="run system checks and exit")
    parser.add_argument("--chat", action="store_true", help="start an interactive AI chat")
    parser.add_argument("--ask", metavar="TEXT", default=None, help="ask one question and exit")
    parser.add_argument("--voice", action="store_true", help="start a push-to-talk voice chat")
    parser.add_argument("--version", action="store_true", help="show version and exit")
    parser.add_argument("--env-file", type=Path, default=None, help="path to a .env file")
    return parser


def _open_memory(settings, logger) -> Optional[MemoryStore]:
    """Open long-term memory, or return None (memory off or database unusable).

    A database problem never stops the assistant: it just runs without memory.
    """
    if not settings.memory_enabled:
        return None
    try:
        conn = open_database(settings.db_path)
    except DatabaseError as exc:
        logger.warning("Memory database unavailable: %s", exc)
        print(t("mem_unavailable", settings.language), file=sys.stderr)
        return None
    return MemoryStore(conn, settings.user_id)


def _build_brain(settings, spoken: bool = False, memory: Optional[MemoryStore] = None) -> Brain:
    context = None
    if memory is not None and settings.memory_in_prompt:
        context = make_context_provider(memory, settings.memory_max_prompt_items)
    return Brain(
        create_provider(settings),
        language=settings.language,
        max_history=settings.ai_max_history,
        spoken=spoken,
        memory_context=context,
    )


def _run_chat(settings, logger, memory: Optional[MemoryStore]) -> None:
    brain = _build_brain(settings, memory=memory)
    handler = hint = None
    if memory is not None:
        handler = make_memory_handler(memory, settings.language, logger.getChild("memory"))
        hint = t("mem_hint", settings.language)
    run_chat(brain, settings.language, command_handler=handler, hint=hint or "")


def _run_voice(settings, logger, memory: Optional[MemoryStore]) -> None:
    brain = _build_brain(settings, spoken=True, memory=memory)  # fails early if key/model missing
    backend = create_voice(settings)
    if backend.mode == MODE_CONSOLE:
        print(t("voice_console_mode", settings.language))
    VoiceSession(
        brain,
        backend.stt,
        backend.tts,
        backend.trigger,
        language=settings.language,
        wake_phrase=settings.wake_phrase,
        require_wake=settings.voice_require_wake,
        logger=logger.getChild("voice"),
    ).run()


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.version:
        print(f"{APP_NAME} {__version__}")
        return EXIT_OK

    try:
        settings = load_settings(env_file=args.env_file)
    except ConfigError as exc:
        print(t("config_error", DEFAULT_LANGUAGE, detail=exc), file=sys.stderr)
        return EXIT_CONFIG

    setup_logging(settings)
    logger = get_logger()
    app = Application(settings, logger)
    exit_code = EXIT_OK
    memory: Optional[MemoryStore] = None

    try:
        app.start()
        if args.check:
            results = app.run_checks()
            print("\n".join(app.format_report(results)))
            if not app.checks_passed(results):
                exit_code = EXIT_CHECK_FAILED
        elif args.ask is not None:
            memory = _open_memory(settings, logger)
            print(_build_brain(settings, memory=memory).ask(args.ask))
        elif args.chat:
            memory = _open_memory(settings, logger)
            _run_chat(settings, logger, memory)
        elif args.voice:
            memory = _open_memory(settings, logger)
            _run_voice(settings, logger, memory)
        else:
            print("\n".join(app.banner()))
    except ConfigError as exc:
        print(t("config_error", settings.language, detail=exc), file=sys.stderr)
        exit_code = EXIT_CONFIG
    except (InputError, ProviderError) as exc:
        logger.info("AI unavailable: code=%s detail=%s", getattr(exc, "code", ""), exc)
        print(describe_error(exc, settings.language), file=sys.stderr)
        exit_code = EXIT_AI
    except VoiceError as exc:
        logger.info("Voice unavailable: code=%s detail=%s", exc.code, exc)
        print(describe_voice_error(exc, settings.language), file=sys.stderr)
        exit_code = EXIT_VOICE
    except KeyboardInterrupt:
        print(t("interrupted", settings.language))
    except Exception:  # noqa: BLE001 - last-resort handler, details go to the log
        logger.exception("Unexpected error")
        print(t("unexpected_error", settings.language), file=sys.stderr)
        exit_code = EXIT_ERROR
    finally:
        if memory is not None:
            memory.close()
        app.stop()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
