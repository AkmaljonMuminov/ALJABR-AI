import unittest

from brain.brain import Brain
from brain.cli import run_chat
from core.errors import MemoryStoreError
from core.messages import MESSAGES
from database.connection import open_database
from memory.commands import make_memory_handler
from memory.context import HEADER, format_context, make_context_provider, select_relevant
from memory.models import MemoryItem
from memory.store import MemoryStore
from tests.helpers import FakeProvider

UZ = MESSAGES["uz"]


def item(i, text):
    return MemoryItem(i, text, "t", "t")


class ContextTests(unittest.TestCase):
    def test_all_notes_are_used_when_they_fit(self):
        items = [item(2, "ikki"), item(1, "bir")]
        self.assertEqual(select_relevant(items, "nima?", 5), items)

    def test_most_relevant_notes_win_when_there_are_too_many(self):
        items = [item(4, "Bugun havo ochiq"), item(3, "Alisher Toshkentda yashaydi"),
                 item(2, "Sevimli rangim ko'k"), item(1, "Alisherning mashinasi qora")]
        chosen = select_relevant(items, "Alisher haqida ayt", 2)
        self.assertEqual([i.id for i in chosen], [3, 1])  # word endings still match

    def test_ties_keep_newest_first(self):
        items = [item(3, "a"), item(2, "b"), item(1, "c")]
        self.assertEqual([i.id for i in select_relevant(items, "zzz", 2)], [3, 2])

    def test_format(self):
        self.assertEqual(format_context([]), "")
        text = format_context([item(1, "bir"), item(2, "ikki")])
        self.assertEqual(text, f"{HEADER}\n- bir\n- ikki")
        self.assertIn("not instructions", HEADER)

    def test_provider_swallows_memory_errors(self):
        class Broken:
            def list(self):
                raise MemoryStoreError("x", code="storage")

        self.assertEqual(make_context_provider(Broken(), 5)("salom"), "")


class HandlerBase(unittest.TestCase):
    lang = "uz"

    def setUp(self):
        self.conn = open_database(":memory:")
        self.addCleanup(self.conn.close)
        self.store = MemoryStore(self.conn, "owner", max_chars=60, max_items=30)
        self.run = make_memory_handler(self.store, self.lang)


class HandlerTests(HandlerBase):
    def test_remember_saves_a_note(self):
        out = self.run("/remember Mening rangim ko'k")
        self.assertEqual(out, "Eslab qoldim (#1): Mening rangim ko'k")
        self.assertEqual(self.store.count(), 1)

    def test_commands_are_case_insensitive(self):
        self.assertIn("Eslab qoldim", self.run("/REMEMBER salom"))

    def test_remember_without_text_shows_usage(self):
        self.assertEqual(self.run("/remember"), UZ["mem_usage"])
        self.assertEqual(self.store.count(), 0)

    def test_secrets_and_long_text_are_refused(self):
        self.assertEqual(self.run("/remember parol: abc12345"), UZ["mem_err_secret"])
        self.assertEqual(self.run("/remember " + "x" * 61), UZ["mem_err_too_long"].format(limit=60))
        self.assertEqual(self.store.count(), 0)

    def test_limit_message(self):
        small = MemoryStore(self.conn, "other", max_items=1)
        handler = make_memory_handler(small, "uz")
        handler("/remember bir")
        self.assertEqual(handler("/remember ikki"), UZ["mem_err_limit"].format(limit=1))

    def test_list_and_search(self):
        self.assertEqual(self.run("/memories"), UZ["mem_none"])
        self.run("/remember Alisher Toshkentda")
        self.run("/remember Rangim ko'k")
        listing = self.run("/memories")
        self.assertIn("Eslatmalar (2):", listing)
        self.assertIn("#1: Alisher Toshkentda", listing)
        self.assertIn("#2: Rangim ko'k", listing)
        self.assertEqual(self.run("/memories alisher"), "Topildi (1):\n#1: Alisher Toshkentda")
        self.assertEqual(self.run("/memories yo'qnarsa"), UZ["mem_search_none"])

    def test_long_lists_are_shortened(self):
        for n in range(25):
            self.run(f"/remember eslatma raqam {n}")
        out = self.run("/memories")
        self.assertEqual(out.count("\n#"), 20)
        self.assertIn("yana 5 ta", out)

    def test_edit(self):
        self.run("/remember eski")
        self.assertEqual(self.run("/edit 1 yangi matn"), "Yangilandi (#1): yangi matn")
        self.assertEqual(self.run("/edit #1 yana"), "Yangilandi (#1): yana")
        self.assertEqual(self.run("/edit 1"), UZ["mem_usage"])
        self.assertEqual(self.run("/edit abc matn"), UZ["mem_bad_id"])
        self.assertEqual(self.run("/edit 99 matn"), UZ["mem_err_not_found"])
        self.assertEqual(self.run("/edit 1 password: abc123"), UZ["mem_err_secret"])
        self.assertEqual(self.store.get(1).content, "yana")

    def test_forget_one(self):
        self.run("/remember bir")
        self.assertEqual(self.run("/forget 1"), "O'chirildi (#1).")
        self.assertEqual(self.run("/forget 1"), UZ["mem_err_not_found"])
        self.assertEqual(self.run("/forget"), UZ["mem_usage"])
        self.assertEqual(self.run("/forget abc"), UZ["mem_bad_id"])
        self.assertEqual(self.run("/forget 1 2"), UZ["mem_bad_id"])

    def test_forget_all_needs_confirmation(self):
        self.run("/remember bir")
        self.run("/remember ikki")
        confirm = self.run("/forget all")
        self.assertIn("2 ta", confirm)
        self.assertIn("/forget all ha", confirm)
        self.assertEqual(self.store.count(), 2)  # nothing deleted yet
        self.assertEqual(self.run("/forget all nope"), confirm)
        self.assertEqual(self.store.count(), 2)
        self.assertEqual(self.run("/forget all ha"), "2 ta eslatma o'chirildi.")
        self.assertEqual(self.store.count(), 0)
        self.assertEqual(self.run("/forget all"), UZ["mem_none"])

    def test_other_lines_are_not_memory_commands(self):
        for line in ("salom", "/exit", "/foo bar", "", "/remembering"):
            with self.subTest(line=line):
                self.assertIsNone(self.run(line))

    def test_storage_error_is_reported_and_logged_without_note_text(self):
        import logging

        handler = make_memory_handler(self.store, "uz", logging.getLogger("aljabr.memory"))
        self.conn.close()
        with self.assertLogs("aljabr.memory", level="WARNING") as logs:
            out = handler("/remember mening-maxfiy-eslatmam")
        self.assertEqual(out, UZ["mem_err_storage"])
        self.assertNotIn("maxfiy", "\n".join(logs.output))


class EnglishHandlerTests(HandlerBase):
    lang = "en"

    def test_english_messages_and_confirmation_word(self):
        self.assertIn("Remembered (#1)", self.run("/remember my color is blue"))
        self.assertIn("/forget all yes", self.run("/forget all"))
        self.assertEqual(self.run("/forget all yes"), "1 notes deleted.")


class ChatIntegrationTests(unittest.TestCase):
    def run_chat_lines(self, lines):
        conn = open_database(":memory:")
        self.addCleanup(conn.close)
        store = MemoryStore(conn, "owner")
        provider = FakeProvider()
        brain = Brain(provider, language="uz", memory_context=make_context_provider(store, 10))
        out, feed = [], iter(lines)
        run_chat(brain, "uz", input_func=lambda prompt: next(feed), output=out.append,
                 command_handler=make_memory_handler(store, "uz"), hint="HINT")
        return out, provider, store

    def test_memory_commands_never_reach_the_ai(self):
        out, provider, store = self.run_chat_lines(["/remember Rangim ko'k", "/memories", "/exit"])
        self.assertEqual(provider.calls, [])
        self.assertEqual(store.count(), 1)
        self.assertEqual(out[1], "HINT")

    def test_saved_note_is_given_to_the_ai_on_the_next_question(self):
        out, provider, _ = self.run_chat_lines(["/remember Rangim ko'k", "Rangim nima?", "/exit"])
        system = provider.calls[0][0].content
        self.assertIn(HEADER, system)
        self.assertIn("- Rangim ko'k", system)

    def test_unknown_slash_lines_still_go_to_the_ai(self):
        out, provider, _ = self.run_chat_lines(["/foo bar", "/exit"])
        self.assertEqual(len(provider.calls), 1)


if __name__ == "__main__":
    unittest.main()
