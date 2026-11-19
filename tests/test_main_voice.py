import contextlib
import io
import logging
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main as main_module
import voice.factory
from core.logging_setup import LOGGER_NAME, close_logging
from tests.helpers import FakeProvider


class MainVoiceTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(close_logging, logging.getLogger(LOGGER_NAME))

    def set_env(self, **extra):
        env = {
            "ALJABR_DATA_DIR": str(self.base / "data"),
            "ALJABR_LANGUAGE": "uz",
            "OPENAI_API_KEY": "",
            "ALJABR_AI_MODEL": "",
            "ALJABR_VOICE_BACKEND": "console",
            "ALJABR_VOICE_REQUIRE_WAKE": "false",
        }
        env.update(extra)
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, argv, inputs=()):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch("builtins.input", side_effect=list(inputs)):
            code = main_module.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_text_mode_voice_session(self):
        self.set_env()
        with mock.patch.object(main_module, "create_provider", return_value=FakeProvider()):
            code, out, _ = self.run_main(["--voice"], ["salom", "q"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("matn rejimida", out)
        self.assertIn("echo:salom", out)

    def test_wake_phrase_is_required_when_configured(self):
        self.set_env(ALJABR_VOICE_REQUIRE_WAKE="true")
        provider = FakeProvider()
        with mock.patch.object(main_module, "create_provider", return_value=provider):
            code, out, _ = self.run_main(
                ["--voice"], ["bugun havo", "salom aljabr, soat nechchi", "q"]
            )
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertEqual(len(provider.calls), 1)
        self.assertIn("echo:soat nechchi", out)

    def test_voice_without_ai_key_explains_what_to_do(self):
        self.set_env()
        code, _, err = self.run_main(["--voice"])
        self.assertEqual(code, main_module.EXIT_AI)
        self.assertIn("OPENAI_API_KEY", err)

    def test_forced_termux_without_tools_exits_with_voice_code(self):
        self.set_env(ALJABR_VOICE_BACKEND="termux")
        with mock.patch.object(main_module, "create_provider", return_value=FakeProvider()), \
                mock.patch.object(voice.factory, "termux_tools_present", return_value=False):
            code, _, err = self.run_main(["--voice"])
        self.assertEqual(code, main_module.EXIT_VOICE)
        self.assertIn("Termux:API", err)
        self.assertNotIn("Traceback", err)

    def test_check_reports_voice_mode(self):
        self.set_env(ALJABR_VOICE_BACKEND="console")
        code, out, _ = self.run_main(["--check"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("[ixtiyoriy] Ovoz tizimi: matn rejimi", out)
        self.set_env(ALJABR_VOICE_BACKEND="auto")
        with mock.patch.object(voice.factory, "termux_tools_present", return_value=True):
            _, out, _ = self.run_main(["--check"])
        self.assertIn("[OK] Ovoz tizimi: Termux:API topildi", out)


@unittest.skipIf(sys.platform.startswith("win"), "uses POSIX shell scripts")
class FakeTermuxEndToEndTests(unittest.TestCase):
    """Real subprocesses: fake 'termux-*' programs placed first on PATH."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.spoken = self.root / "spoken.txt"
        self.args = self.root / "args.txt"
        self._script("termux-speech-to-text", "#!/bin/sh\necho 'salom aljabr, bugun nima gap'\n")
        self._script(
            "termux-tts-speak",
            f'#!/bin/sh\necho "$@" > "{self.args}"\ncat > "{self.spoken}"\n',
        )
        patcher = mock.patch.dict(os.environ, {
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "ALJABR_DATA_DIR": str(self.root / "data"),
            "ALJABR_LANGUAGE": "uz",
            "ALJABR_VOICE_BACKEND": "auto",
            "ALJABR_VOICE_REQUIRE_WAKE": "true",
            "OPENAI_API_KEY": "",
            "ALJABR_AI_MODEL": "",
        })
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(close_logging, logging.getLogger(LOGGER_NAME))

    def _script(self, name, body):
        path = self.bin / name
        path.write_text(body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def run_main(self, argv, inputs):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch("builtins.input", side_effect=inputs):
            code = main_module.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_full_voice_turn_through_real_subprocesses(self):
        with mock.patch.object(main_module, "create_provider", return_value=FakeProvider()):
            code, out, _ = self.run_main(["--voice"], ["", "q"])  # Enter = speak, q = quit
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertNotIn("matn rejimida", out)  # real (fake) termux backend was chosen
        self.assertIn("Siz: salom aljabr, bugun nima gap", out)
        self.assertEqual(self.spoken.read_text(encoding="utf-8").strip(), "echo:bugun nima gap")
        self.assertEqual(self.args.read_text(encoding="utf-8").split(),
                         ["-l", "uz", "-p", "1.1", "-r", "0.95"])


if __name__ == "__main__":
    unittest.main()
