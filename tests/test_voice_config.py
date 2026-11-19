import datetime
import tempfile
import unittest
from pathlib import Path

from brain.brain import Brain
from brain.prompts import build_system_prompt
from config.settings import load_settings
from core.errors import ConfigError, VoiceError
from tests.helpers import FakeProvider
from tests.helpers_voice import FakeRunner
from voice.activation import AlwaysActiveTrigger, PushToTalkTrigger
from voice.console import ConsoleSTT, ConsoleTTS
from voice.factory import MODE_CONSOLE, MODE_TERMUX, create_voice, detect_mode
from voice.termux import TermuxSTT, TermuxTTS

TODAY = datetime.date(2026, 11, 18)


def settings_for(**env):
    with tempfile.TemporaryDirectory() as tmp:
        return load_settings(environ=env, base_dir=Path(tmp))


def which_with(*present):
    return lambda name: f"/bin/{name}" if name in present else None


BOTH = which_with("termux-speech-to-text", "termux-tts-speak")


class VoiceSettingsTests(unittest.TestCase):
    def test_defaults(self):
        s = settings_for()
        self.assertEqual(s.voice_backend, "auto")
        self.assertEqual((s.tts_language, s.tts_region, s.tts_engine), ("uz", "", ""))
        self.assertEqual((s.tts_pitch, s.tts_rate, s.stt_timeout), (1.1, 0.95, 20))
        self.assertFalse(s.voice_require_wake)

    def test_overrides(self):
        s = settings_for(ALJABR_VOICE_BACKEND="Termux", ALJABR_TTS_LANGUAGE="ru",
                         ALJABR_TTS_REGION="RU", ALJABR_TTS_ENGINE="com.google.android.tts",
                         ALJABR_TTS_PITCH="1.4", ALJABR_TTS_RATE="1", ALJABR_STT_TIMEOUT="30",
                         ALJABR_VOICE_REQUIRE_WAKE="yes")
        self.assertEqual(s.voice_backend, "termux")
        self.assertEqual((s.tts_language, s.tts_region), ("ru", "RU"))
        self.assertEqual(s.tts_engine, "com.google.android.tts")
        self.assertEqual((s.tts_pitch, s.tts_rate, s.stt_timeout), (1.4, 1.0, 30))
        self.assertTrue(s.voice_require_wake)

    def test_boolean_spellings(self):
        for raw, expected in (("true", True), ("1", True), ("ON", True),
                              ("false", False), ("0", False), ("off", False), ("", False)):
            with self.subTest(raw=raw):
                self.assertEqual(settings_for(ALJABR_VOICE_REQUIRE_WAKE=raw).voice_require_wake,
                                 expected)

    def test_invalid_values_are_rejected(self):
        bad = [
            {"ALJABR_VOICE_BACKEND": "alexa"},
            {"ALJABR_TTS_PITCH": "0.4"}, {"ALJABR_TTS_PITCH": "2.1"}, {"ALJABR_TTS_PITCH": "high"},
            {"ALJABR_TTS_RATE": "0.4"}, {"ALJABR_TTS_RATE": "3"},
            {"ALJABR_STT_TIMEOUT": "4"}, {"ALJABR_STT_TIMEOUT": "61"},
            {"ALJABR_VOICE_REQUIRE_WAKE": "maybe"},
            {"ALJABR_TTS_LANGUAGE": "uz; rm -rf"}, {"ALJABR_TTS_ENGINE": "a b"},
            {"ALJABR_TTS_REGION": "-n"[:1] + "x" * 70},
        ]
        for env in bad:
            with self.subTest(env=env):
                with self.assertRaises(ConfigError):
                    settings_for(**env)


class FactoryTests(unittest.TestCase):
    def test_auto_uses_termux_only_when_both_tools_exist(self):
        s = settings_for()
        self.assertEqual(detect_mode(s, BOTH), MODE_TERMUX)
        self.assertEqual(detect_mode(s, which_with("termux-tts-speak")), MODE_CONSOLE)
        self.assertEqual(detect_mode(s, which_with("termux-speech-to-text")), MODE_CONSOLE)
        self.assertEqual(detect_mode(s, which_with()), MODE_CONSOLE)

    def test_console_is_forced_even_when_tools_exist(self):
        self.assertEqual(detect_mode(settings_for(ALJABR_VOICE_BACKEND="console"), BOTH),
                         MODE_CONSOLE)

    def test_termux_backend_applies_settings(self):
        runner = FakeRunner()
        s = settings_for(ALJABR_TTS_LANGUAGE="ru", ALJABR_TTS_PITCH="1.3", ALJABR_STT_TIMEOUT="9",
                         ALJABR_TTS_ENGINE="eng.x")
        backend = create_voice(s, runner=runner, which=BOTH)
        self.assertEqual(backend.mode, MODE_TERMUX)
        self.assertIsInstance(backend.stt, TermuxSTT)
        self.assertIsInstance(backend.tts, TermuxTTS)
        self.assertIsInstance(backend.trigger, PushToTalkTrigger)
        self.assertEqual(backend.stt.timeout, 9)
        self.assertEqual(backend.tts.build_args()[:5], ["termux-tts-speak", "-l", "ru", "-p", "1.3"])
        self.assertIn("eng.x", backend.tts.build_args())

    def test_console_backend(self):
        backend = create_voice(settings_for(), which=which_with())
        self.assertEqual(backend.mode, MODE_CONSOLE)
        self.assertIsInstance(backend.stt, ConsoleSTT)
        self.assertIsInstance(backend.tts, ConsoleTTS)
        self.assertIsInstance(backend.trigger, AlwaysActiveTrigger)

    def test_forced_termux_without_tools_is_an_error(self):
        with self.assertRaises(VoiceError) as ctx:
            create_voice(settings_for(ALJABR_VOICE_BACKEND="termux"), which=which_with())
        self.assertEqual(ctx.exception.code, "unavailable")


class SpokenPromptTests(unittest.TestCase):
    def test_default_prompt_has_no_speech_instructions(self):
        self.assertNotIn("read aloud", build_system_prompt("uz", TODAY))

    def test_spoken_prompt_asks_for_short_plain_replies(self):
        prompt = build_system_prompt("uz", TODAY, spoken=True)
        self.assertIn("read aloud", prompt)
        self.assertIn("do not use markdown", prompt)
        self.assertIn("instead of guessing.\nYour reply", prompt)  # separated by a newline

    def test_brain_sends_the_spoken_prompt_to_the_provider(self):
        provider = FakeProvider()
        Brain(provider, spoken=True, today=lambda: TODAY).ask("salom")
        self.assertIn("read aloud", provider.calls[0][0].content)
        provider2 = FakeProvider()
        Brain(provider2, today=lambda: TODAY).ask("salom")
        self.assertNotIn("read aloud", provider2.calls[0][0].content)


if __name__ == "__main__":
    unittest.main()
