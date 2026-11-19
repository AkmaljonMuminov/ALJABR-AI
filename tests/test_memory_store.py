import tempfile
import unittest
from pathlib import Path

from core.errors import MemoryStoreError
from database.connection import open_database
from memory.store import MemoryStore, normalize


def make_clock():
    counter = {"n": 0}

    def clock():
        counter["n"] += 1
        return f"2026-11-19T10:00:{counter['n']:02d}+00:00"

    return clock


class StoreBase(unittest.TestCase):
    def setUp(self):
        self.conn = open_database(":memory:")
        self.addCleanup(self.conn.close)

    def store(self, user="owner", **kwargs):
        kwargs.setdefault("clock", make_clock())
        return MemoryStore(self.conn, user, **kwargs)

    def assert_code(self, code, func, *args):
        with self.assertRaises(MemoryStoreError) as ctx:
            func(*args)
        self.assertEqual(ctx.exception.code, code)


class BasicTests(StoreBase):
    def test_add_get_list_count(self):
        s = self.store()
        a = s.add("Mening sevimli rangim ko'k")
        b = s.add("Ertaga uchrashuv bor")
        self.assertEqual(s.count(), 2)
        self.assertEqual(s.get(a.id).content, "Mening sevimli rangim ko'k")
        self.assertEqual([i.id for i in s.list()], [b.id, a.id])  # newest first
        self.assertEqual([i.id for i in s.list(limit=1)], [b.id])
        self.assertTrue(a.created_at and a.updated_at)

    def test_whitespace_is_normalized(self):
        self.assertEqual(normalize("  a \n\n b\t c  "), "a b c")
        self.assertEqual(self.store().add("  Salom \n dunyo ").content, "Salom dunyo")

    def test_adding_the_same_text_again_returns_the_existing_note(self):
        s = self.store()
        first = s.add("Mening rangim ko'k")
        again = s.add("  MENING RANGIM KO'K ")
        self.assertEqual(first.id, again.id)
        self.assertEqual(s.count(), 1)

    def test_validation_errors(self):
        s = self.store(max_chars=20)
        self.assert_code("empty", s.add, "")
        self.assert_code("empty", s.add, "   \n ")
        self.assert_code("too_long", s.add, "x" * 21)
        self.assert_code("secret", s.add, "parol: abc12345")
        self.assert_code("secret", s.add, "sk-abcdefghijkl")
        self.assertEqual(s.count(), 0)

    def test_limit(self):
        s = self.store(max_items=2)
        s.add("bir")
        s.add("ikki")
        self.assert_code("limit", s.add, "uch")
        s.delete(s.list()[0].id)
        s.add("uch")  # space again after a delete
        self.assertEqual(s.count(), 2)

    def test_update(self):
        s = self.store()
        item = s.add("eski matn")
        changed = s.update(item.id, "yangi matn")
        self.assertEqual(changed.content, "yangi matn")
        self.assertNotEqual(changed.updated_at, item.updated_at)
        self.assertEqual(changed.created_at, item.created_at)
        self.assertEqual(s.count(), 1)

    def test_update_errors_leave_the_note_unchanged(self):
        s = self.store()
        item = s.add("asl matn")
        self.assert_code("secret", s.update, item.id, "password: abc123")
        self.assert_code("empty", s.update, item.id, " ")
        self.assert_code("not_found", s.update, 999, "x")
        self.assertEqual(s.get(item.id).content, "asl matn")

    def test_delete_and_delete_all(self):
        s = self.store()
        a, b, c = s.add("bir"), s.add("ikki"), s.add("uch")
        s.delete(b.id)
        self.assert_code("not_found", s.delete, b.id)
        self.assert_code("not_found", s.get, b.id)
        self.assertEqual(s.delete_all(), 2)
        self.assertEqual(s.count(), 0)
        self.assertEqual(s.delete_all(), 0)

    def test_user_id_is_required(self):
        with self.assertRaises(ValueError):
            MemoryStore(self.conn, "")


class SearchTests(StoreBase):
    def test_search_matches_all_words_case_insensitively(self):
        s = self.store()
        s.add("Do'stim Alisher Toshkentda yashaydi")
        s.add("Alisher ertaga keladi")
        s.add("Boshqa gap")
        self.assertEqual(len(s.search("alisher")), 2)
        self.assertEqual(len(s.search("ALISHER toshkent")), 1)
        self.assertEqual(s.search("yo'q narsa"), [])

    def test_search_works_for_cyrillic_where_sql_like_would_not(self):
        s = self.store()
        s.add("Менинг дўстим Алишер")
        self.assertEqual(len(s.search("алишер")), 1)
        self.assertEqual(len(s.search("ДЎСТИМ")), 1)

    def test_empty_query_returns_everything(self):
        s = self.store()
        s.add("bir")
        s.add("ikki")
        self.assertEqual(len(s.search("")), 2)
        self.assertEqual(len(s.search("   ")), 2)


class SafetyTests(StoreBase):
    def test_sql_in_text_is_stored_as_plain_data(self):
        s = self.store()
        evil = "x'); DROP TABLE memories; --"
        item = s.add(evil)
        self.assertEqual(s.get(item.id).content, evil)
        self.assertEqual(s.count(), 1)  # table still exists and works

    def test_database_failure_becomes_storage_error(self):
        s = self.store()
        self.conn.close()
        self.assert_code("storage", s.count)
        self.assert_code("storage", s.add, "salom")


class IsolationTests(StoreBase):
    def test_users_cannot_see_or_touch_each_others_notes(self):
        alice, bob = self.store("alice"), self.store("bob")
        secret_note = alice.add("Alisaning eslatmasi")
        self.assertEqual(bob.list(), [])
        self.assertEqual(bob.search("Alisaning"), [])
        self.assertEqual(bob.count(), 0)
        self.assert_code("not_found", bob.get, secret_note.id)
        self.assert_code("not_found", bob.update, secret_note.id, "hacked")
        self.assert_code("not_found", bob.delete, secret_note.id)
        self.assertEqual(bob.delete_all(), 0)
        self.assertEqual(alice.get(secret_note.id).content, "Alisaning eslatmasi")

    def test_same_text_can_exist_for_two_users(self):
        a, b = self.store("alice"), self.store("bob")
        self.assertNotEqual(a.add("bir xil matn").id, b.add("bir xil matn").id)

    def test_limits_are_per_user(self):
        a, b = self.store("alice", max_items=1), self.store("bob", max_items=1)
        a.add("bir")
        b.add("ikki")  # not blocked by alice's note
        self.assert_code("limit", a.add, "uch")

    def test_delete_all_only_removes_own_notes(self):
        a, b = self.store("alice"), self.store("bob")
        a.add("a1")
        b.add("b1")
        b.add("b2")
        self.assertEqual(b.delete_all(), 2)
        self.assertEqual(a.count(), 1)


class PersistenceTests(unittest.TestCase):
    def test_notes_survive_reopening_the_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "aljabr.db"
            first = MemoryStore(open_database(path), "owner")
            item = first.add("Doimiy eslatma")
            first.close()
            second = MemoryStore(open_database(path), "owner")
            self.addCleanup(second.close)
            self.assertEqual(second.get(item.id).content, "Doimiy eslatma")


if __name__ == "__main__":
    unittest.main()
