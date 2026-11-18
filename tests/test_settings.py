import tempfile
import unittest
from pathlib import Path

from config.settings import DEFAULT_WAKE_PHRASE, Secret, load_settings
from core.errors import ConfigError


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def load(self, environ=None, **kwargs):
        return load_settings(environ=environ or {}, base_dir=self.base, **kwargs)

    def test_defaults(self):
        s = self.load()
        self.assertEqual(s.language, "uz")
        self.assertEqual(s.wake_phrase, DEFAULT_WAKE_PHRASE)
        self.assertEqual(s.log_level, "INFO")
        self.assertEqual(s.environment, "development")
        self.assertEqual(s.ai_provider, "openai")
        self.assertEqual(s.ai_model, "")
        self.assertFalse(s.openai_api_key)

    def test_relative_paths_resolve_from_base_dir(self):
        s = self.load()
        self.assertEqual(s.data_dir, self.base.resolve() / "data")
        self.assertEqual(s.log_dir, self.base.resolve() / "data" / "logs")

    def test_environment_overrides(self):
        s = self.load(
            {
                "ALJABR_LANGUAGE": "RU",
                "ALJABR_LOG_LEVEL": "debug",
                "ALJABR_AI_MODEL": "my-model:1.0",
                "ALJABR_LOG_DIR": "mylogs",
            }
        )
        self.assertEqual(s.language, "ru")
        self.assertEqual(s.log_level, "DEBUG")
        self.assertEqual(s.ai_model, "my-model:1.0")
        self.assertEqual(s.log_dir, self.base.resolve() / "mylogs")

    def test_invalid_values_raise_config_error(self):
        bad = [
            {"ALJABR_LANGUAGE": "xx"},
            {"ALJABR_LOG_LEVEL": "LOUD"},
            {"ALJABR_ENV": "staging"},
            {"ALJABR_WAKE_PHRASE": "x" * 61},
            {"ALJABR_AI_PROVIDER": "Bad Provider!"},
            {"ALJABR_AI_MODEL": "bad model; rm -rf"},
        ]
        for environ in bad:
            with self.subTest(environ=environ):
                with self.assertRaises(ConfigError):
                    self.load(environ)

    def test_default_env_file_is_read_and_real_env_wins(self):
        (self.base / ".env").write_text(
            "ALJABR_LANGUAGE=en\nALJABR_LOG_LEVEL=ERROR\n", encoding="utf-8"
        )
        s = self.load({"ALJABR_LANGUAGE": "ru"})
        self.assertEqual(s.language, "ru")
        self.assertEqual(s.log_level, "ERROR")

    def test_explicit_env_file_must_exist(self):
        with self.assertRaises(ConfigError):
            self.load(env_file=self.base / "nope.env")

    def test_explicit_env_file_is_used(self):
        custom = self.base / "custom.env"
        custom.write_text("ALJABR_LANGUAGE=en\n", encoding="utf-8")
        self.assertEqual(self.load(env_file=custom).language, "en")

    def test_secret_is_hidden_in_repr_and_str(self):
        key = "sk-supersecret-1234567890"
        s = self.load({"OPENAI_API_KEY": key})
        self.assertTrue(s.openai_api_key)
        self.assertEqual(s.openai_api_key.reveal(), key)
        self.assertNotIn(key, repr(s))
        self.assertNotIn(key, str(s))
        self.assertNotIn(key, str(s.openai_api_key))
        self.assertEqual(s.secret_values(), (key,))

    def test_empty_secret_is_falsy(self):
        self.assertFalse(Secret(""))
        self.assertEqual(self.load().secret_values(), ())


if __name__ == "__main__":
    unittest.main()
