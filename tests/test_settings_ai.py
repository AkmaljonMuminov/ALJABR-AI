import tempfile
import unittest
from pathlib import Path

from config.settings import load_settings
from core.errors import ConfigError


class AiSettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def load(self, **env):
        return load_settings(environ=env, base_dir=Path(self._tmp.name))

    def test_defaults(self):
        s = self.load()
        self.assertEqual(s.ai_base_url, "https://api.openai.com/v1")
        self.assertEqual(s.ai_timeout, 30)
        self.assertEqual(s.ai_max_history, 20)

    def test_overrides_and_trailing_slash_is_removed(self):
        s = self.load(ALJABR_AI_BASE_URL="https://example.test/v1/",
                      ALJABR_AI_TIMEOUT="60", ALJABR_AI_MAX_HISTORY="50")
        self.assertEqual(s.ai_base_url, "https://example.test/v1")
        self.assertEqual((s.ai_timeout, s.ai_max_history), (60, 50))

    def test_http_is_allowed_only_for_localhost(self):
        self.assertEqual(
            self.load(ALJABR_AI_BASE_URL="http://localhost:11434/v1").ai_base_url,
            "http://localhost:11434/v1",
        )
        self.assertEqual(
            self.load(ALJABR_AI_BASE_URL="http://127.0.0.1:8080/v1").ai_base_url,
            "http://127.0.0.1:8080/v1",
        )

    def test_invalid_values_are_rejected(self):
        bad = [
            {"ALJABR_AI_BASE_URL": "http://example.test/v1"},
            {"ALJABR_AI_BASE_URL": "ftp://example.test"},
            {"ALJABR_AI_BASE_URL": "https://"},
            {"ALJABR_AI_BASE_URL": "not a url"},
            {"ALJABR_AI_TIMEOUT": "abc"},
            {"ALJABR_AI_TIMEOUT": "4"},
            {"ALJABR_AI_TIMEOUT": "121"},
            {"ALJABR_AI_MAX_HISTORY": "1"},
            {"ALJABR_AI_MAX_HISTORY": "201"},
        ]
        for env in bad:
            with self.subTest(env=env):
                with self.assertRaises(ConfigError):
                    self.load(**env)


if __name__ == "__main__":
    unittest.main()
