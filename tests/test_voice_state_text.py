import unittest

from voice.state import InvalidTransition, VoiceState, VoiceStateMachine
from voice.text import clean_for_speech


class StateTests(unittest.TestCase):
    def test_normal_turn(self):
        m = VoiceStateMachine()
        self.assertEqual(m.state, VoiceState.IDLE)
        for state in (VoiceState.LISTENING, VoiceState.THINKING, VoiceState.SPEAKING,
                      VoiceState.IDLE):
            m.transition(state)
            self.assertEqual(m.state, state)

    def test_invalid_transitions_raise(self):
        m = VoiceStateMachine()
        with self.assertRaises(InvalidTransition):
            m.transition(VoiceState.THINKING)
        m.transition(VoiceState.LISTENING)
        with self.assertRaises(InvalidTransition):
            m.transition(VoiceState.LISTENING)

    def test_reset_returns_to_idle_from_any_active_state(self):
        for state in (VoiceState.LISTENING, VoiceState.THINKING, VoiceState.SPEAKING):
            m = VoiceStateMachine()
            m.state = state
            m.reset()
            self.assertEqual(m.state, VoiceState.IDLE)

    def test_stopped_is_final(self):
        m = VoiceStateMachine()
        m.stop()
        self.assertTrue(m.stopped)
        m.reset()
        self.assertTrue(m.stopped)
        with self.assertRaises(InvalidTransition):
            m.transition(VoiceState.LISTENING)


class CleanForSpeechTests(unittest.TestCase):
    def test_removes_markdown(self):
        self.assertEqual(clean_for_speech("**Salom** _dunyo_ `x` # Sarlavha"), "Salom dunyo x Sarlavha")

    def test_removes_code_blocks_urls_and_bullets(self):
        text = "Mana:\n```python\nprint(1)\n```\n- birinchi\n- ikkinchi\nBatafsil https://example.com/x"
        self.assertEqual(clean_for_speech(text), "Mana: birinchi ikkinchi Batafsil")

    def test_collapses_whitespace_and_handles_empty(self):
        self.assertEqual(clean_for_speech("a \n\n  b\t c"), "a b c")
        self.assertEqual(clean_for_speech(""), "")

    def test_short_text_is_unchanged(self):
        self.assertEqual(clean_for_speech("Salom. Qalaysiz?"), "Salom. Qalaysiz?")

    def test_long_text_is_cut_at_a_sentence_end(self):
        text = "Birinchi gap. " + "Ikkinchi gap. " * 20
        cut = clean_for_speech(text, max_chars=60)
        self.assertLessEqual(len(cut), 60)
        self.assertTrue(cut.endswith("."))

    def test_long_text_without_sentences_is_hard_cut(self):
        self.assertEqual(clean_for_speech("a" * 100, max_chars=10), "a" * 10)


if __name__ == "__main__":
    unittest.main()
