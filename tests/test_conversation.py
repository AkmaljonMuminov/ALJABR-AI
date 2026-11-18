import unittest

from brain.conversation import Conversation
from brain.types import Message


class ConversationTests(unittest.TestCase):
    def test_stores_messages_in_order(self):
        c = Conversation()
        c.add_user("q1")
        c.add_assistant("a1")
        self.assertEqual(c.messages, [Message("user", "q1"), Message("assistant", "a1")])
        self.assertEqual(len(c), 2)

    def test_messages_returns_a_copy(self):
        c = Conversation()
        c.add_user("q1")
        c.messages.append(Message("user", "hack"))
        self.assertEqual(len(c), 1)

    def test_trims_oldest_and_history_starts_with_user(self):
        c = Conversation(max_messages=4)
        for text, role in [("u1", "user"), ("a1", "assistant"), ("u2", "user"),
                           ("a2", "assistant"), ("u3", "user")]:
            (c.add_user if role == "user" else c.add_assistant)(text)
        self.assertEqual([m.content for m in c.messages], ["u2", "a2", "u3"])

    def test_pop_last_and_clear(self):
        c = Conversation()
        c.add_user("q")
        c.add_assistant("a")
        c.pop_last()
        self.assertEqual([m.content for m in c.messages], ["q"])
        c.clear()
        self.assertEqual(len(c), 0)
        c.pop_last()  # no error on empty history

    def test_with_system_prepends_system_prompt(self):
        c = Conversation()
        c.add_user("q")
        msgs = c.with_system("rules")
        self.assertEqual([m.role for m in msgs], ["system", "user"])
        self.assertEqual(msgs[0].content, "rules")

    def test_minimum_size_enforced(self):
        with self.assertRaises(ValueError):
            Conversation(max_messages=1)

    def test_invalid_role_rejected(self):
        with self.assertRaises(ValueError):
            Message("robot", "x")


if __name__ == "__main__":
    unittest.main()
