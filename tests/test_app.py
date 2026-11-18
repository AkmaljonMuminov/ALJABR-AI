import contextlib
import io
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main as main_module
from config.settings import load_settings
from core.app import Application
from core.logging_setup import LOGGER_NAME, close_logging


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def app(self, **env):
        settings = load_settings(environ=env, base_dir=self.base)
        return Application(settings, logging.getLogger(f"{LOGGER_NAME}.test"))

    def test_start_creates_directories_and_stop_is_repeatable(self):
        app = self.app()
        app.start()
        self.assertTrue((self.base / "data" / "logs").is_dir())
        self.assertTrue(app.running)
        app.stop()
        app.stop()
        self.assertFalse(app.running)

    def test_checks_pass_without_api_key(self):
        app = self.app()
        app.start()
        results = app.run_checks()
        self.assertTrue(Application.checks_passed(results))
        key_check = results[-1]
        self.assertFalse(key_check.ok)
        self.assertFalse(key_check.required)

    def test_checks_never_reveal_api_key(self):
        key = "sk-reportleakcheck12345"
        app = self.app(OPENAI_API_KEY=key)
        app.start()
        report = "\n".join(app.format_report(app.run_checks()))
        self.assertNotIn(key, report)

    def test_unwritable_data_dir_fails_required_check(self):
        blocker = self.base / "blocked"
        blocker.write_text("file", encoding="utf-8")
        app = self.app(ALJABR_DATA_DIR=str(blocker), ALJABR_LOG_DIR=str(self.base / "logs"))
        app.start()
        results = app.run_checks()
        self.assertFalse(Application.checks_passed(results))

    def test_banner_uses_configured_language_and_wake_phrase(self):
        text = "\n".join(self.app().banner())
        self.assertIn("ALJABR", text)
        self.assertIn("Salom, ALJABR", text)
        english = "\n".join(self.app(ALJABR_LANGUAGE="en").banner())
        self.assertIn("Hello", english)


class MainTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(close_logging, logging.getLogger(LOGGER_NAME))
        self.env = mock.patch.dict(
            os.environ,
            {"ALJABR_DATA_DIR": str(self.base / "data"), "ALJABR_LANGUAGE": "uz"},
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main_module.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_version(self):
        code, out, _ = self.run_main(["--version"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("ALJABR AI", out)

    def test_default_run_prints_greeting(self):
        code, out, _ = self.run_main([])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("Salom", out)

    def test_check_succeeds(self):
        code, out, _ = self.run_main(["--check"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("[OK]", out)

    def test_missing_env_file_returns_config_exit_code(self):
        code, _, err = self.run_main(["--env-file", str(self.base / "missing.env")])
        self.assertEqual(code, main_module.EXIT_CONFIG)
        self.assertIn("Sozlamalarda xatolik", err)

    def test_invalid_setting_returns_config_exit_code(self):
        with mock.patch.dict(os.environ, {"ALJABR_LANGUAGE": "xx"}):
            code, _, err = self.run_main([])
        self.assertEqual(code, main_module.EXIT_CONFIG)
        self.assertIn("ALJABR_LANGUAGE", err)

    def test_unexpected_error_is_handled_without_traceback_on_screen(self):
        with mock.patch.object(Application, "banner", side_effect=RuntimeError("boom")):
            code, _, err = self.run_main([])
        self.assertEqual(code, main_module.EXIT_ERROR)
        self.assertIn("Kutilmagan xatolik", err)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
