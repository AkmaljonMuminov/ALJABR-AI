import unittest

from core.messages import MESSAGES, t


class MessagesTests(unittest.TestCase):
    def test_all_languages_define_the_same_keys(self):
        reference = set(MESSAGES["uz"])
        for lang in ("ru", "en"):
            with self.subTest(lang=lang):
                self.assertEqual(set(MESSAGES[lang]), reference)

    def test_placeholders_match_across_languages(self):
        import string

        def fields(template):
            return {name for _, name, _, _ in string.Formatter().parse(template) if name}

        for key, uz_text in MESSAGES["uz"].items():
            for lang in ("ru", "en"):
                with self.subTest(key=key, lang=lang):
                    self.assertEqual(fields(MESSAGES[lang][key]), fields(uz_text))

    def test_formatting(self):
        self.assertIn("Salom, ALJABR", t("wake_hint", "uz", wake_phrase="Salom, ALJABR"))

    def test_unknown_language_falls_back_to_uzbek(self):
        self.assertEqual(t("shutdown", "zz"), MESSAGES["uz"]["shutdown"])

    def test_unknown_key_returns_key(self):
        self.assertEqual(t("does_not_exist"), "does_not_exist")

    def test_missing_placeholder_value_does_not_raise(self):
        self.assertIsInstance(t("wake_hint", "uz"), str)


if __name__ == "__main__":
    unittest.main()
