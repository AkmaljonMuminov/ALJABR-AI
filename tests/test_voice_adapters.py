import sys
import unittest
from unittest import mock

from core.errors import VoiceError
from tests.helpers_voice import FakeRunner, fail, ok
from voice.activation import BackgroundWakeTrigger, PushToTalkTrigger
from voice.console import ConsoleSTT, ConsoleTTS
from voice.runner import CommandRunner
from voice.termux import TermuxSTT, TermuxTTS


class TermuxSTTTests(unittest.TestCase):
    def test_returns_last_non_empty_line_and_uses_timeout(self):
        runner = FakeRunner(ok("\nbugun\nbugun havo qanday\n\n"))
        self.assertEqual(TermuxSTT(runner, timeout=7).listen(), "bugun havo qanday")
        self.assertEqual(runner.calls[0]["args"], ["termux-speech-to-text"])
        self.assertEqual(runner.calls[0]["timeout"], 7)

    def test_nothing_recognised_is_empty_string(self):
        self.assertEqual(TermuxSTT(FakeRunner(ok("  \n"))).listen(), "")

    def test_failure_codes(self):
        cases = [
            (fail("Permission denied: RECORD_AUDIO"), "permission"),
            (fail("something else"), "failed"),
        ]
        for result, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(VoiceError) as ctx:
                    TermuxSTT(FakeRunner(result)).listen()
                self.assertEqual(ctx.exception.code, code)

    def test_runner_errors_propagate(self):
        for code in ("unavailable", "timeout"):
            with self.subTest(code=code):
                with self.assertRaises(VoiceError) as ctx:
                    TermuxSTT(FakeRunner(VoiceError("x", code=code))).listen()
                self.assertEqual(ctx.exception.code, code)


class TermuxTTSTests(unittest.TestCase):
    def test_default_arguments(self):
        self.assertEqual(
            TermuxTTS(FakeRunner()).build_args(),
            ["termux-tts-speak", "-l", "uz", "-p", "1.1", "-r", "0.95"],
        )

    def test_region_and_engine_are_added(self):
        tts = TermuxTTS(FakeRunner(), language="ru", region="RU", engine="com.x.tts",
                        pitch=1.3, rate=1.0)
        self.assertEqual(
            tts.build_args(),
            ["termux-tts-speak", "-l", "ru", "-p", "1.3", "-r", "1.0",
             "-n", "RU", "-e", "com.x.tts"],
        )

    def test_text_goes_through_stdin_never_as_an_argument(self):
        runner = FakeRunner(ok())
        TermuxTTS(runner).speak("-e evil --rm hello")
        call = runner.calls[0]
        self.assertEqual(call["input"], "-e evil --rm hello")
        self.assertNotIn("-e evil --rm hello", call["args"])
        self.assertNotIn("evil", " ".join(call["args"]))

    def test_empty_text_does_nothing(self):
        runner = FakeRunner()
        TermuxTTS(runner).speak("   ")
        self.assertEqual(runner.calls, [])

    def test_failure_raises_voice_error(self):
        with self.assertRaises(VoiceError) as ctx:
            TermuxTTS(FakeRunner(fail("boom"))).speak("salom")
        self.assertEqual(ctx.exception.code, "failed")


class ConsoleTests(unittest.TestCase):
    def test_reads_typed_line(self):
        self.assertEqual(ConsoleSTT(lambda prompt: "  salom ").listen(), "salom")
        self.assertTrue(ConsoleSTT.echoes_input)

    def test_quit_words_and_eof_close_the_session(self):
        def eof(prompt):
            raise EOFError

        for reader in (lambda p: "q", lambda p: "/EXIT", eof):
            with self.subTest():
                with self.assertRaises(VoiceError) as ctx:
                    ConsoleSTT(reader).listen()
                self.assertEqual(ctx.exception.code, "closed")

    def test_uses_builtin_input_by_default(self):
        with mock.patch("builtins.input", return_value="hi"):
            self.assertEqual(ConsoleSTT().listen(), "hi")

    def test_console_tts_is_silent(self):
        self.assertIsNone(ConsoleTTS().speak("salom"))


class TriggerTests(unittest.TestCase):
    def test_push_to_talk(self):
        self.assertTrue(PushToTalkTrigger("> ", lambda p: "").wait())
        self.assertFalse(PushToTalkTrigger("> ", lambda p: "Q").wait())

    def test_push_to_talk_eof_and_ctrl_c_end_session(self):
        for exc in (EOFError(), KeyboardInterrupt()):
            def reader(prompt, exc=exc):
                raise exc
            self.assertFalse(PushToTalkTrigger("> ", reader).wait())

    def test_background_wake_is_not_available_yet(self):
        with self.assertRaises(VoiceError) as ctx:
            BackgroundWakeTrigger()
        self.assertEqual(ctx.exception.code, "unavailable")


class RealRunnerTests(unittest.TestCase):
    """Exercise the real subprocess path with Python itself as the command."""

    def test_runs_command_and_passes_stdin(self):
        result = CommandRunner().run(
            [sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"],
            input_text="salom",
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "SALOM")

    def test_nonzero_exit_is_returned_not_raised(self):
        result = CommandRunner().run([sys.executable, "-c", "import sys; sys.exit(3)"])
        self.assertEqual(result.returncode, 3)

    def test_missing_command_is_unavailable(self):
        with self.assertRaises(VoiceError) as ctx:
            CommandRunner().run(["definitely-not-a-real-command-xyz"])
        self.assertEqual(ctx.exception.code, "unavailable")

    def test_timeout(self):
        with self.assertRaises(VoiceError) as ctx:
            CommandRunner().run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.3)
        self.assertEqual(ctx.exception.code, "timeout")

    def test_text_is_never_interpreted_by_a_shell(self):
        result = CommandRunner().run(
            [sys.executable, "-c", "import sys; print(sys.stdin.read())"],
            input_text="$(echo pwned); `echo pwned`",
        )
        self.assertEqual(result.stdout.strip(), "$(echo pwned); `echo pwned`")


if __name__ == "__main__":
    unittest.main()
