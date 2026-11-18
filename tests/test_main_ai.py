import contextlib
import io
import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main as main_module
from core.logging_setup import LOGGER_NAME, close_logging
from tests.helpers import FakeProvider, network_error


class MainAiTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(close_logging, logging.getLogger(LOGGER_NAME))
        self.set_env()

    def set_env(self, **extra):
        env = {
            "ALJABR_DATA_DIR": str(self.base / "data"),
            "ALJABR_LANGUAGE": "uz",
            "OPENAI_API_KEY": "",
            "ALJABR_AI_MODEL": "",
            "ALJABR_AI_PROVIDER": "openai",
            "ALJABR_AI_BASE_URL": "https://api.openai.com/v1",
        }
        env.update(extra)
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main_module.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_ask_without_key_explains_what_to_do(self):
        code, out, err = self.run_main(["--ask", "Salom"])
        self.assertEqual(code, main_module.EXIT_AI)
        self.assertIn("OPENAI_API_KEY", err)
        self.assertEqual(out, "")
        self.assertNotIn("Traceback", err)

    def test_ask_with_key_but_without_model(self):
        self.set_env(OPENAI_API_KEY="sk-mainleakcheck123456")
        code, _, err = self.run_main(["--ask", "Salom"])
        self.assertEqual(code, main_module.EXIT_AI)
        self.assertIn("ALJABR_AI_MODEL", err)
        self.assertNotIn("sk-mainleakcheck123456", err)

    def test_ask_success(self):
        with mock.patch.object(main_module, "create_provider", return_value=FakeProvider()):
            code, out, _ = self.run_main(["--ask", "Salom"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertEqual(out.strip(), "echo:Salom")

    def test_ask_provider_failure_shows_uzbek_message_not_traceback(self):
        provider = FakeProvider(failures=[network_error()])
        with mock.patch.object(main_module, "create_provider", return_value=provider):
            code, _, err = self.run_main(["--ask", "Salom"])
        self.assertEqual(code, main_module.EXIT_AI)
        self.assertIn("Internet aloqasini tekshiring", err)
        self.assertNotIn("Traceback", err)

    def test_ask_empty_text_is_rejected(self):
        with mock.patch.object(main_module, "create_provider", return_value=FakeProvider()):
            code, _, err = self.run_main(["--ask", ""])
        self.assertEqual(code, main_module.EXIT_AI)
        self.assertIn("bo'sh", err)

    def test_chat_session(self):
        with mock.patch.object(main_module, "create_provider", return_value=FakeProvider()), \
                mock.patch("builtins.input", side_effect=["Salom", "/exit"]):
            code, out, _ = self.run_main(["--chat"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("Suhbat boshlandi", out)
        self.assertIn("echo:Salom", out)

    def test_chat_without_key_exits_with_ai_code(self):
        code, _, err = self.run_main(["--chat"])
        self.assertEqual(code, main_module.EXIT_AI)
        self.assertIn("OPENAI_API_KEY", err)

    def test_unknown_provider_is_a_config_error(self):
        self.set_env(ALJABR_AI_PROVIDER="other")
        code, _, err = self.run_main(["--ask", "Salom"])
        self.assertEqual(code, main_module.EXIT_CONFIG)
        self.assertIn("unknown AI provider", err)

    def test_invalid_base_url_is_a_config_error(self):
        self.set_env(ALJABR_AI_BASE_URL="http://example.test/v1")
        code, _, err = self.run_main(["--check"])
        self.assertEqual(code, main_module.EXIT_CONFIG)
        self.assertIn("ALJABR_AI_BASE_URL", err)

    def test_check_reports_model_as_optional_until_set(self):
        _, out, _ = self.run_main(["--check"])
        self.assertIn("[ixtiyoriy] AI modeli", out)
        self.set_env(ALJABR_AI_MODEL="my-model")
        code, out, _ = self.run_main(["--check"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("[OK] AI modeli: openai / my-model", out)


if __name__ == "__main__":
    unittest.main()
