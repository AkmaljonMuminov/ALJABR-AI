import unittest
from unittest import mock

from brain.brain import Brain
from brain.cli import describe_error, run_chat
from brain.factory import create_provider
from brain.openai_provider import OpenAIProvider
from config.settings import load_settings
from core.errors import ConfigError, InputError, ProviderError, ProviderNotConfiguredError
from core.messages import MESSAGES
from tests.helpers import FakeProvider, network_error

import tempfile
from pathlib import Path


def settings_for(**env):
    with tempfile.TemporaryDirectory() as tmp:
        return load_settings(environ=env, base_dir=Path(tmp))


class FactoryTests(unittest.TestCase):
    def test_creates_openai_provider_from_settings(self):
        s = settings_for(OPENAI_API_KEY="sk-abcdefgh1234", ALJABR_AI_MODEL="m1",
                         ALJABR_AI_BASE_URL="https://example.test/v1/", ALJABR_AI_TIMEOUT="12")
        provider = create_provider(s)
        self.assertIsInstance(provider, OpenAIProvider)
        self.assertEqual(provider.model, "m1")
        self.assertEqual(provider.base_url, "https://example.test/v1")
        self.assertEqual(provider.timeout, 12)

    def test_missing_key_and_model(self):
        with self.assertRaises(ProviderNotConfiguredError) as ctx:
            create_provider(settings_for(ALJABR_AI_MODEL="m1"))
        self.assertEqual(ctx.exception.code, "no_api_key")
        with self.assertRaises(ProviderNotConfiguredError) as ctx:
            create_provider(settings_for(OPENAI_API_KEY="sk-abcdefgh1234"))
        self.assertEqual(ctx.exception.code, "no_model")

    def test_unknown_provider_is_a_config_error(self):
        with self.assertRaises(ConfigError) as ctx:
            create_provider(settings_for(ALJABR_AI_PROVIDER="other"))
        self.assertIn("unknown AI provider", str(ctx.exception))


class DescribeErrorTests(unittest.TestCase):
    def test_every_provider_and_input_code_is_translated(self):
        provider_codes = ["no_api_key", "no_model", "auth", "rate_limit", "network",
                          "server", "bad_response", "error"]
        for lang in MESSAGES:
            for code in provider_codes:
                with self.subTest(lang=lang, code=code):
                    text = describe_error(ProviderError("x", code=code), lang)
                    self.assertFalse(text.startswith("provider_"))
            for code in ("empty", "too_long"):
                with self.subTest(lang=lang, code=code):
                    text = describe_error(InputError("x", code=code), lang)
                    self.assertFalse(text.startswith("input_"))

    def test_unknown_codes_fall_back_to_generic_messages(self):
        self.assertEqual(
            describe_error(ProviderError("x", code="weird"), "en"), MESSAGES["en"]["provider_error"]
        )
        self.assertEqual(
            describe_error(InputError("x", code="weird"), "en"), MESSAGES["en"]["input_empty"]
        )


class ChatLoopTests(unittest.TestCase):
    def run_loop(self, lines, provider=None):
        feed = iter(lines)
        out = []

        def fake_input(prompt):
            item = next(feed)
            if isinstance(item, BaseException):
                raise item
            return item

        brain = Brain(provider or FakeProvider(), language="en")
        run_chat(brain, "en", input_func=fake_input, output=out.append)
        return out, brain

    def test_basic_conversation_and_exit(self):
        out, brain = self.run_loop(["Salom", "", "/exit", "never-read"])
        self.assertEqual(out[0], MESSAGES["en"]["chat_intro"])
        self.assertEqual(out[1], "echo:Salom")
        self.assertEqual(len(out), 2)
        self.assertEqual(len(brain.conversation), 2)

    def test_clear_command(self):
        out, brain = self.run_loop(["bir", "/CLEAR", "ikki", "/quit"])
        self.assertIn(MESSAGES["en"]["history_cleared"], out)
        self.assertEqual([m.content for m in brain.conversation.messages], ["ikki", "echo:ikki"])

    def test_eof_and_ctrl_c_end_the_loop(self):
        for ending in (EOFError(), KeyboardInterrupt()):
            with self.subTest(ending=type(ending).__name__):
                out, _ = self.run_loop(["bir", ending])
                self.assertEqual(out[1], "echo:bir")

    def test_provider_error_is_shown_and_loop_continues(self):
        out, brain = self.run_loop(["bir", "ikki", "/exit"], FakeProvider(failures=[network_error()]))
        self.assertEqual(out[1], MESSAGES["en"]["provider_network"])
        self.assertEqual(out[2], "echo:ikki")
        self.assertEqual(len(brain.conversation), 2)

    def test_uses_builtin_input_and_print_by_default(self):
        brain = Brain(FakeProvider(), language="en")
        with mock.patch("builtins.input", side_effect=["hi", "/exit"]), \
                mock.patch("builtins.print") as fake_print:
            run_chat(brain, "en")
        printed = [call.args[0] for call in fake_print.call_args_list]
        self.assertIn("echo:hi", printed)


if __name__ == "__main__":
    unittest.main()
