import tempfile
import unittest
from pathlib import Path

from config.env_loader import load_env_file, parse_env_text
from core.errors import ConfigError


class ParseEnvTextTests(unittest.TestCase):
    def test_basic_pairs_comments_and_blank_lines(self):
        text = "# comment\n\nA=1\nB = two\n"
        self.assertEqual(parse_env_text(text), {"A": "1", "B": "two"})

    def test_export_prefix_and_quotes(self):
        text = 'export A="hello world"\nB=\'single\'\n'
        self.assertEqual(parse_env_text(text), {"A": "hello world", "B": "single"})

    def test_inline_comment_only_for_unquoted_values(self):
        text = 'A=value # note\nB="keep # this"\n'
        self.assertEqual(parse_env_text(text), {"A": "value", "B": "keep # this"})

    def test_value_may_contain_equals_and_be_empty(self):
        text = "A=x=y\nB=\n"
        self.assertEqual(parse_env_text(text), {"A": "x=y", "B": ""})

    def test_invalid_lines_are_skipped(self):
        text = "no equals sign\n1BAD=x\nGOOD=ok\n"
        self.assertEqual(parse_env_text(text), {"GOOD": "ok"})

    def test_wake_phrase_with_comma_survives(self):
        self.assertEqual(
            parse_env_text("ALJABR_WAKE_PHRASE=Salom, ALJABR\n"),
            {"ALJABR_WAKE_PHRASE": "Salom, ALJABR"},
        )


class LoadEnvFileTests(unittest.TestCase):
    def test_reads_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("A=1\n", encoding="utf-8")
            self.assertEqual(load_env_file(path), {"A": "1"})

    def test_missing_file_raises_config_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ConfigError):
                load_env_file(Path(tmp) / "missing.env")


if __name__ == "__main__":
    unittest.main()
