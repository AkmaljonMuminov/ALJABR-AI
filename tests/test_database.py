import os
import sqlite3
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from core.errors import DatabaseError
from database.connection import migrate, open_database, schema_version
from database.migrations import MIGRATIONS


def table_names(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_in_memory_database_is_migrated(self):
        conn = open_database(":memory:")
        self.addCleanup(conn.close)
        self.assertEqual(schema_version(conn), len(MIGRATIONS))
        self.assertIn("memories", table_names(conn))

    def test_memories_table_has_user_id_for_future_multi_user_support(self):
        conn = open_database(":memory:")
        self.addCleanup(conn.close)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(memories)")}
        self.assertEqual(columns, {"id", "user_id", "content", "created_at", "updated_at"})

    def test_creates_missing_folders_and_persists_data(self):
        path = self.root / "deep" / "dir" / "aljabr.db"
        conn = open_database(path)
        conn.execute("INSERT INTO memories (user_id, content, created_at, updated_at) "
                     "VALUES ('u', 'x', 't', 't')")
        conn.commit()
        conn.close()
        again = open_database(path)  # reopening must not re-run migrations or lose data
        self.addCleanup(again.close)
        self.assertEqual(again.execute("SELECT COUNT(*) FROM memories").fetchone()[0], 1)
        self.assertEqual(schema_version(again), len(MIGRATIONS))

    @unittest.skipIf(sys.platform.startswith("win"), "POSIX permissions")
    def test_database_file_is_private(self):
        path = self.root / "aljabr.db"
        open_database(path).close()
        mode = stat.S_IMODE(os.stat(path).st_mode)
        self.assertEqual(mode, 0o600)

    def test_database_from_a_newer_program_is_refused(self):
        path = self.root / "new.db"
        conn = sqlite3.connect(path)
        conn.execute("PRAGMA user_version = 99")
        conn.commit()
        conn.close()
        with self.assertRaises(DatabaseError) as ctx:
            open_database(path)
        self.assertIn("newer", str(ctx.exception))

    def test_unusable_location_raises_database_error(self):
        blocker = self.root / "file"
        blocker.write_text("not a folder", encoding="utf-8")
        with self.assertRaises(DatabaseError):
            open_database(blocker / "aljabr.db")

    def test_corrupt_file_raises_database_error(self):
        path = self.root / "bad.db"
        path.write_bytes(b"this is definitely not a sqlite database " * 50)
        with self.assertRaises(DatabaseError):
            open_database(path)

    def test_failed_migration_is_rolled_back_and_earlier_ones_are_kept(self):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        with self.assertRaises(sqlite3.Error):
            migrate(conn, ["CREATE TABLE a (x);", "CREATE TABLE b (x); THIS IS NOT SQL;"])
        self.assertEqual(schema_version(conn), 1)
        self.assertIn("a", table_names(conn))
        self.assertNotIn("b", table_names(conn))


if __name__ == "__main__":
    unittest.main()
