import tempfile
import unittest
from pathlib import Path

from config.settings import load_settings
from core.logging_setup import (
    LOG_FILE_NAME,
    LOGGER_NAME,
    close_logging,
    redact,
    setup_logging,
)

import logging


class RedactTests(unittest.TestCase):
    def test_known_secret_value_is_masked(self):
        self.assertEqual(redact("key is abcd1234", ["abcd1234"]), "key is ***")

    def test_openai_style_key_is_masked(self):
        text = redact("using sk-abcdefghijklmnop now")
        self.assertNotIn("abcdefghijklmnop", text)

    def test_bearer_token_is_masked(self):
        text = redact("Authorization: Bearer abcdefghijklmnop12345")
        self.assertNotIn("abcdefghijklmnop12345", text)

    def test_assignments_are_masked(self):
        for raw in ("password=hunter2", "api_key: abc123", "OPENAI_API_KEY=zzz999", "token = 'x y'"):
            with self.subTest(raw=raw):
                self.assertIn("***", redact(raw))
                for leaked in ("hunter2", "abc123", "zzz999", "x y"):
                    self.assertNotIn(leaked, redact(raw))

    def test_normal_text_is_untouched(self):
        self.assertEqual(redact("ALJABR AI started"), "ALJABR AI started")

    def test_short_secrets_are_ignored_to_avoid_mangling_text(self):
        self.assertEqual(redact("a b c", ["a"]), "a b c")


class SetupLoggingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(close_logging, logging.getLogger(LOGGER_NAME))

    def settings(self, **env):
        return load_settings(environ=env, base_dir=self.base)

    def test_writes_log_file_and_redacts_secret(self):
        key = "sk-topsecretvalue987654"
        logger = setup_logging(self.settings(OPENAI_API_KEY=key))
        logger.info("calling provider with %s", key)
        try:
            raise ValueError(f"failed using {key}")
        except ValueError:
            logger.exception("boom")
        for handler in logger.handlers:
            handler.flush()
        content = (self.base / "data" / "logs" / LOG_FILE_NAME).read_text(encoding="utf-8")
        self.assertIn("calling provider", content)
        self.assertIn("boom", content)
        self.assertNotIn(key, content)
        self.assertNotIn("topsecretvalue987654", content)

    def test_calling_twice_does_not_duplicate_handlers(self):
        s = self.settings()
        setup_logging(s)
        logger = setup_logging(s)
        self.assertEqual(len(logger.handlers), 2)

    def test_unusable_log_dir_falls_back_to_console_only(self):
        blocker = self.base / "blocked"
        blocker.write_text("i am a file, not a folder", encoding="utf-8")
        logger = setup_logging(self.settings(ALJABR_LOG_DIR=str(blocker)))
        self.assertEqual(len(logger.handlers), 1)
        logger.warning("still works")


if __name__ == "__main__":
    unittest.main()
