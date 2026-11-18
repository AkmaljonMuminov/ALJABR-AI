import datetime
import unittest

from brain.brain import Brain
from core.errors import InputError, ProviderError
from tests.helpers import FakeProvider, network_error

TODAY = datetime.date(2026, 11, 18)


def make_brain(provider=None, **kwargs):
    return Brain(provider or FakeProvider(), today=lambda: TODAY, **kwargs)


class BrainTests(unittest.TestCase):
    def test_ask_returns_reply_and_stores_both_turns(self):
        brain = make_brain()
        self.assertEqual(brain.ask("Salom"), "echo:Salom")
        self.assertEqual([m.role for m in brain.conversation.messages], ["user", "assistant"])

    def test_context_is_sent_on_the_next_question(self):
        provider = FakeProvider()
        brain = make_brain(provider)
        brain.ask("bir")
        brain.ask("ikki")
        roles = [m.role for m in provider.calls[1]]
        self.assertEqual(roles, ["system", "user", "assistant", "user"])

    def test_system_prompt_contains_date_and_language(self):
        prompt = make_brain(language="uz").system_prompt()
        self.assertIn("2026-11-18", prompt)
        self.assertIn("Uzbek", prompt)
        self.assertIn("Russian", make_brain(language="ru").system_prompt())

    def test_system_prompt_forbids_claiming_unavailable_abilities(self):
        prompt = make_brain().system_prompt()
        self.assertIn("never claim", prompt)
        self.assertIn("passwords", prompt)

    def test_input_is_trimmed(self):
        self.assertEqual(make_brain().ask("  hi  "), "echo:hi")

    def test_empty_input_rejected_without_calling_provider(self):
        provider = FakeProvider()
        brain = make_brain(provider)
        for text in ("", "   ", None):
            with self.subTest(text=text):
                with self.assertRaises(InputError) as ctx:
                    brain.ask(text)
                self.assertEqual(ctx.exception.code, "empty")
        self.assertEqual(provider.calls, [])

    def test_too_long_input_rejected(self):
        brain = make_brain(max_input_chars=10)
        with self.assertRaises(InputError) as ctx:
            brain.ask("x" * 11)
        self.assertEqual(ctx.exception.code, "too_long")

    def test_failed_request_leaves_history_unchanged(self):
        brain = make_brain(FakeProvider(failures=[network_error()]))
        with self.assertRaises(ProviderError):
            brain.ask("birinchi")
        self.assertEqual(len(brain.conversation), 0)
        self.assertEqual(brain.ask("birinchi"), "echo:birinchi")  # retry works, no duplicate
        self.assertEqual(len(brain.conversation), 2)

    def test_failure_keeps_earlier_conversation(self):
        brain = make_brain(FakeProvider(failures=[]))
        brain.ask("bir")
        brain.provider._failures.append(network_error())
        with self.assertRaises(ProviderError):
            brain.ask("ikki")
        self.assertEqual(len(brain.conversation), 2)

    def test_reset_clears_history(self):
        brain = make_brain()
        brain.ask("bir")
        brain.reset()
        self.assertEqual(len(brain.conversation), 0)

    def test_message_contents_are_not_logged(self):
        brain = make_brain()
        with self.assertLogs("aljabr.brain", level="INFO") as logs:
            brain.ask("mening-maxfiy-savolim")
        output = "\n".join(logs.output)
        self.assertNotIn("mening-maxfiy-savolim", output)
        self.assertNotIn("echo:", output)
        self.assertIn("in_chars=", output)


if __name__ == "__main__":
    unittest.main()
