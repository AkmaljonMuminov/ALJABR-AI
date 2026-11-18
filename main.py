#!/usr/bin/env python3
"""ALJABR AI entry point (Phase 1: ALJABR CORE).

Usage:
    python main.py              # start and show the greeting
    python main.py --check      # run system checks (exit code 0 if all pass)
    python main.py --version
    python main.py --env-file /path/to/.env
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from config.settings import load_settings
from core import APP_NAME, __version__
from core.app import Application
from core.errors import ConfigError
from core.logging_setup import get_logger, setup_logging
from core.messages import DEFAULT_LANGUAGE, t

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CONFIG = 2
EXIT_CHECK_FAILED = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aljabr", description=f"{APP_NAME} personal assistant")
    parser.add_argument("--check", action="store_true", help="run system checks and exit")
    parser.add_argument("--version", action="store_true", help="show version and exit")
    parser.add_argument("--env-file", type=Path, default=None, help="path to a .env file")
    return parser


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

    try:
        app.start()
        if args.check:
            results = app.run_checks()
            print("\n".join(app.format_report(results)))
            if not app.checks_passed(results):
                exit_code = EXIT_CHECK_FAILED
        else:
            print("\n".join(app.banner()))
    except KeyboardInterrupt:
        print(t("interrupted", settings.language))
    except Exception:  # noqa: BLE001 - last-resort handler, details go to the log
        logger.exception("Unexpected error")
        print(t("unexpected_error", settings.language), file=sys.stderr)
        exit_code = EXIT_ERROR
    finally:
        app.stop()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
