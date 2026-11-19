import contextlib
import io
import logging
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main as main_module
from core.errors import DatabaseError
from core.logging_setup import LOGGER_NAME, close_logging
from memory.context import HEADER
from tests.helpers import FakeProvider


class MainMemoryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(close_logging, logging.getLogger(LOGGER_NAME))
        self.db = self.base / "data" / "aljabr.db"
        self.set_env()

    def set_env(self, **extra):
        env = {
            "ALJABR_DATA_DIR": str(self.base / "data"),
            "ALJABR_LANGUAGE": "uz",
            "OPENAI_API_KEY": "",
            "ALJABR_AI_MODEL": "",
            "ALJABR_VOICE_BACKEND": "console",
            "ALJABR_MEMORY_ENABLED": "true",
            "ALJABR_MEMORY_IN_PROMPT": "true",
            "ALJABR_USER_ID": "owner",
        }
        env.update(extra)
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, argv, inputs=(), provider=None):
        provider = provider or FakeProvider()
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(main_module, "create_provider", return_value=provider), \
                mock.patch("builtins.input", side_effect=list(inputs)):
            code = main_module.main(argv)
        return code, out.getvalue(), err.getvalue(), provider

    def rows(self):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute("SELECT user_id, content FROM memories ORDER BY id").fetchall()
        finally:
            conn.close()

    # -- saving and using notes --------------------------------------------

    def test_note_is_saved_and_used_in_the_same_chat(self):
        code, out, _, provider = self.run_main(
            ["--chat"], ["/remember Mening sevimli rangim ko'k", "Rangim nima?", "/exit"]
        )
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("Eslab qoldim (#1)", out)
        self.assertIn("/remember", out)  # the memory hint is shown
        self.assertEqual(len(provider.calls), 1)  # /remember was not sent to the AI
        system = provider.calls[0][0].content
        self.assertIn(HEADER, system)
        self.assertIn("- Mening sevimli rangim ko'k", system)
        self.assertEqual(self.rows(), [("owner", "Mening sevimli rangim ko'k")])

    def test_note_survives_a_restart_and_is_used_by_ask(self):
        self.run_main(["--chat"], ["/remember Do'stimning ismi Alisher", "/exit"])
        code, out, _, provider = self.run_main(["--ask", "Do'stim kim?"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("- Do'stimning ismi Alisher", provider.calls[0][0].content)

    def test_edit_and_forget_change_what_the_ai_sees(self):
        _, out, _, provider = self.run_main(
            ["--chat"],
            ["/remember eski matn", "/edit 1 yangi matn", "savol bir", "/forget 1", "savol ikki",
             "/exit"],
        )
        self.assertIn("Yangilandi (#1)", out)
        self.assertIn("O'chirildi (#1)", out)
        self.assertIn("- yangi matn", provider.calls[0][0].content)
        self.assertNotIn("yangi matn", provider.calls[1][0].content)
        self.assertEqual(self.rows(), [])

    def test_secret_is_refused_and_not_stored(self):
        _, out, _, _ = self.run_main(["--chat"], ["/remember parol: abc12345", "/exit"])
        self.assertIn("saqlanmadi", out)
        self.assertEqual(self.rows(), [])

    def test_voice_mode_also_uses_saved_notes(self):
        self.run_main(["--chat"], ["/remember Men Toshkentda yashayman", "/exit"])
        code, _, _, provider = self.run_main(["--voice"], ["Qayerda yashayman?", "q"])
        self.assertEqual(code, main_module.EXIT_OK)
        system = provider.calls[0][0].content
        self.assertIn("- Men Toshkentda yashayman", system)
        self.assertIn("read aloud", system)

    # -- settings ---------------------------------------------------------

    def test_notes_are_saved_but_not_sent_when_memory_in_prompt_is_off(self):
        self.set_env(ALJABR_MEMORY_IN_PROMPT="false")
        _, _, _, provider = self.run_main(["--chat"], ["/remember Rangim ko'k", "salom", "/exit"])
        self.assertEqual(len(self.rows()), 1)
        self.assertNotIn(HEADER, provider.calls[0][0].content)

    def test_memory_can_be_disabled_completely(self):
        self.set_env(ALJABR_MEMORY_ENABLED="false")
        code, out, _, provider = self.run_main(["--chat"], ["/remember bu AI ga ketadi", "/exit"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertFalse(self.db.exists())
        self.assertEqual(len(provider.calls), 1)  # no handler: the line is a normal message
        self.assertNotIn(HEADER, provider.calls[0][0].content)
        self.assertNotIn("/remember <", out)  # no hint either

    def test_limit_on_prompt_items(self):
        self.set_env(ALJABR_MEMORY_MAX_PROMPT_ITEMS="2")
        lines = [f"/remember eslatma {n}" for n in range(5)] + ["savol", "/exit"]
        _, _, _, provider = self.run_main(["--chat"], lines)
        self.assertEqual(provider.calls[0][0].content.count("\n- "), 2)

    # -- isolation --------------------------------------------------------

    def test_two_users_in_one_database_do_not_see_each_other(self):
        self.set_env(ALJABR_USER_ID="alice")
        self.run_main(["--chat"], ["/remember Alisaning sirli rejasi", "/exit"])
        self.set_env(ALJABR_USER_ID="bob")
        _, out, _, provider = self.run_main(["--chat"], ["/memories", "savol", "/exit"])
        self.assertIn("Saqlangan eslatmalar yo'q", out)
        self.assertNotIn("sirli", provider.calls[0][0].content)
        self.assertEqual(self.rows(), [("alice", "Alisaning sirli rejasi")])

    # -- failures ---------------------------------------------------------

    def test_database_failure_does_not_stop_the_assistant(self):
        with mock.patch.object(main_module, "open_database", side_effect=DatabaseError("boom")):
            code, out, err, provider = self.run_main(["--chat"], ["salom", "/exit"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("xotirasiz", err)
        self.assertIn("echo:salom", out)
        self.assertNotIn(HEADER, provider.calls[0][0].content)

    def test_corrupt_database_file_is_reported_not_crashed(self):
        self.db.parent.mkdir(parents=True)
        self.db.write_bytes(b"not a database " * 100)
        code, out, err, _ = self.run_main(["--chat"], ["salom", "/exit"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("xotirasiz", err)
        self.assertNotIn("Traceback", err)

    # -- --check ----------------------------------------------------------

    def test_check_reports_the_memory_database(self):
        code, out, _, _ = self.run_main(["--check"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("[OK] Xotira bazasi:", out)
        self.assertIn("(0 ta eslatma)", out)
        self.run_main(["--chat"], ["/remember bir", "/exit"])
        _, out, _, _ = self.run_main(["--check"])
        self.assertIn("(1 ta eslatma)", out)

    def test_check_when_memory_is_disabled(self):
        self.set_env(ALJABR_MEMORY_ENABLED="false")
        code, out, _, _ = self.run_main(["--check"])
        self.assertEqual(code, main_module.EXIT_OK)
        self.assertIn("[ixtiyoriy] Xotira bazasi: o'chirilgan", out)

    def test_log_never_contains_note_text(self):
        self.run_main(["--chat"], ["/remember mening-maxfiy-eslatmam", "maxfiy savol", "/exit"])
        log = (self.base / "data" / "logs" / "aljabr.log").read_text(encoding="utf-8")
        self.assertNotIn("maxfiy", log)


if __name__ == "__main__":
    unittest.main()
