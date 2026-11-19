import unittest

from brain.brain import Brain
from core.errors import VoiceError
from core.messages import MESSAGES
from tests.helpers import FakeProvider, network_error
from tests.helpers_voice import FakeSTT, FakeTTS, ScriptedTrigger, voice_error
from voice.session import VoiceSession, describe_voice_error
from voice.state import VoiceState

UZ = MESSAGES["uz"]


def make_session(stt, tts=None, trigger=None, provider=None, **kwargs):
    out = []
    brain = Brain(provider or FakeProvider(), language="uz")
    session = VoiceSession(
        brain, stt, tts or FakeTTS(), trigger or ScriptedTrigger(True, False),
        language="uz", output=out.append, **kwargs,
    )
    return session, out


class SessionTests(unittest.TestCase):
    def test_one_turn_listens_answers_and_speaks(self):
        tts = FakeTTS()
        session, out = make_session(FakeSTT("salom"), tts)
        session.run()
        self.assertEqual(tts.spoken, ["echo:salom"])
        self.assertIn(UZ["voice_intro"], out)
        self.assertIn(UZ["voice_listening"], out)
        self.assertIn("Siz: salom", out)
        self.assertIn("echo:salom", out)  # reply is shown as text too
        self.assertTrue(session.machine.stopped)

    def test_typed_input_is_not_echoed_back(self):
        session, out = make_session(FakeSTT("salom", echoes_input=True))
        session.run()
        self.assertFalse(any(line.startswith("Siz:") for line in out))

    def test_context_is_kept_between_turns(self):
        provider = FakeProvider()
        session, _ = make_session(FakeSTT("bir", "ikki"), trigger=ScriptedTrigger(True, True, False),
                                  provider=provider)
        session.run()
        self.assertEqual([m.role for m in provider.calls[1]],
                         ["system", "user", "assistant", "user"])

    def test_nothing_heard_does_not_call_the_ai(self):
        provider = FakeProvider()
        session, out = make_session(FakeSTT(""), provider=provider)
        session.run()
        self.assertEqual(provider.calls, [])
        self.assertIn(UZ["voice_no_speech"], out)

    def test_reply_is_cleaned_for_speech_but_shown_in_full(self):
        tts = FakeTTS()
        session, out = make_session(FakeSTT("**qalin**"), tts)
        session.run()
        self.assertEqual(tts.spoken, ["echo:qalin"])
        self.assertIn("echo:**qalin**", out)


class WakeTests(unittest.TestCase):
    def test_speech_without_wake_phrase_is_ignored(self):
        provider = FakeProvider()
        session, out = make_session(FakeSTT("bugun havo yaxshi"), provider=provider,
                                    require_wake=True)
        session.run()
        self.assertEqual(provider.calls, [])

    def test_wake_phrase_with_command(self):
        tts = FakeTTS()
        session, _ = make_session(FakeSTT("Salom, ALJABR, soat nechchi?"), tts, require_wake=True)
        session.run()
        self.assertEqual(tts.spoken, ["echo:soat nechchi?"])

    def test_wake_phrase_alone_asks_for_the_command(self):
        tts = FakeTTS()
        stt = FakeSTT("Salom, ALJABR", "bugun nima qilamiz")
        session, _ = make_session(stt, tts, require_wake=True)
        session.run()
        self.assertEqual(tts.spoken, [UZ["voice_ready_phrase"], "echo:bugun nima qilamiz"])
        self.assertEqual(stt.calls, 2)

    def test_custom_wake_phrase(self):
        tts = FakeTTS()
        session, _ = make_session(FakeSTT("hey jabr salom"), tts, require_wake=True,
                                  wake_phrase="Hey Jabr")
        session.run()
        self.assertEqual(tts.spoken, ["echo:salom"])


class ErrorHandlingTests(unittest.TestCase):
    def test_timeout_is_reported_and_session_continues(self):
        tts = FakeTTS()
        stt = FakeSTT(voice_error("timeout"), "salom")
        session, out = make_session(stt, tts, trigger=ScriptedTrigger(True, True, False))
        session.run()
        self.assertIn(UZ["voice_timeout"], out)
        self.assertEqual(tts.spoken, ["echo:salom"])

    def test_generic_failure_is_reported_and_session_continues(self):
        stt = FakeSTT(voice_error("failed"), "salom")
        session, out = make_session(stt, trigger=ScriptedTrigger(True, True, False))
        session.run()
        self.assertIn(UZ["voice_failed"], out)

    def test_fatal_errors_end_the_session_and_are_raised(self):
        for code in ("unavailable", "permission"):
            with self.subTest(code=code):
                session, _ = make_session(FakeSTT(voice_error(code)))
                with self.assertRaises(VoiceError) as ctx:
                    session.run()
                self.assertEqual(ctx.exception.code, code)
                self.assertTrue(session.machine.stopped)

    def test_closed_input_ends_quietly(self):
        session, out = make_session(FakeSTT(voice_error("closed")))
        session.run()
        self.assertTrue(session.machine.stopped)
        self.assertNotIn(UZ["voice_failed"], out)

    def test_speech_output_failure_still_shows_text(self):
        tts = FakeTTS(failures=[voice_error("failed")])
        session, out = make_session(FakeSTT("salom", "ikki"), tts,
                                    trigger=ScriptedTrigger(True, True, False))
        session.run()
        self.assertIn("echo:salom", out)
        self.assertIn(UZ["voice_failed"], out)
        self.assertEqual(tts.spoken, ["echo:ikki"])  # next turn works again

    def test_ai_failure_is_spoken_and_shown_and_history_is_clean(self):
        tts = FakeTTS()
        provider = FakeProvider(failures=[network_error()])
        session, out = make_session(FakeSTT("salom"), tts, provider=provider)
        session.run()
        self.assertIn(UZ["provider_network"], out)
        self.assertEqual(tts.spoken, [UZ["provider_network"]])
        self.assertEqual(len(session.brain.conversation), 0)

    def test_state_is_idle_between_turns(self):
        states = []

        class Spy(ScriptedTrigger):
            def wait(inner):
                states.append(session.machine.state)
                return super().wait()

        session, _ = make_session(FakeSTT("bir", "ikki"), trigger=Spy(True, True, False))
        session.run()
        self.assertEqual(states, [VoiceState.IDLE] * 3)


class PrivacyTests(unittest.TestCase):
    def test_spoken_text_is_not_logged(self):
        session, _ = make_session(FakeSTT("mening-maxfiy-gapim"))
        with self.assertLogs("aljabr.voice", level="INFO") as logs:
            session.run()
        joined = "\n".join(logs.output)
        self.assertNotIn("maxfiy", joined)
        self.assertIn("chars", joined)


class DescribeErrorTests(unittest.TestCase):
    def test_known_and_unknown_codes_in_every_language(self):
        for lang in MESSAGES:
            for code in ("unavailable", "permission", "timeout", "failed", "weird"):
                with self.subTest(lang=lang, code=code):
                    text = describe_voice_error(voice_error(code), lang)
                    self.assertFalse(text.startswith("voice_"))
                    self.assertTrue(text)


if __name__ == "__main__":
    unittest.main()
