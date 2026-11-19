import unittest

from voice.wake import WakePhraseMatcher


class WakeTests(unittest.TestCase):
    def setUp(self):
        self.matcher = WakePhraseMatcher("Salom, ALJABR")

    def test_phrase_alone_matches_with_empty_remainder(self):
        for text in ("Salom, ALJABR", "salom aljabr", "SALOM, ALJABR!", "salomaljabr"):
            with self.subTest(text=text):
                result = self.matcher.match(text)
                self.assertTrue(result.matched)
                self.assertEqual(result.remainder, "")

    def test_recogniser_spelling_variants_match(self):
        for text in ("salom al jabr", "Salom, Al-Jabr", "salom Al Jabr."):
            with self.subTest(text=text):
                self.assertTrue(self.matcher.match(text).matched)

    def test_command_after_phrase_is_returned(self):
        result = self.matcher.match("Salom, Al-Jabr! Soat nechchi?")
        self.assertTrue(result.matched)
        self.assertEqual(result.remainder, "Soat nechchi?")
        self.assertEqual(
            self.matcher.match("salom aljabr, bugun ob-havo qanday").remainder,
            "bugun ob-havo qanday",
        )

    def test_phrase_must_be_at_the_start(self):
        self.assertFalse(self.matcher.match("hello salom aljabr").matched)
        self.assertFalse(self.matcher.match("aljabr salom").matched)

    def test_phrase_must_end_at_a_word_boundary(self):
        self.assertFalse(self.matcher.match("salom aljabrxyz").matched)

    def test_unrelated_and_empty_text(self):
        for text in ("", "   ", "bugun havo yaxshi", "salom"):
            with self.subTest(text=text):
                self.assertFalse(self.matcher.match(text).matched)

    def test_custom_phrase(self):
        matcher = WakePhraseMatcher("Hey Jabr")
        self.assertEqual(matcher.match("hey jabr, turn on").remainder, "turn on")

    def test_phrase_without_letters_is_rejected(self):
        with self.assertRaises(ValueError):
            WakePhraseMatcher("...")


if __name__ == "__main__":
    unittest.main()
