import io
import json
import unittest
import urllib.error

from brain.openai_provider import OpenAIProvider, _NoRedirect
from brain.types import Message
from core.errors import ProviderError, ProviderNotConfiguredError

KEY = "sk-unittest-secret-key-123456"
MESSAGES = [Message("system", "rules"), Message("user", "Salom")]


class FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    """Replays outcomes: bytes -> a response, Exception -> raised."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        self.timeouts.append(timeout)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)


def ok_body(text="Salom!", model="m-1", usage=None):
    body = {"model": model, "choices": [{"message": {"role": "assistant", "content": text}}]}
    if usage is not None:
        body["usage"] = usage
    return json.dumps(body).encode()


def http_error(code, message=""):
    body = json.dumps({"error": {"message": message}}).encode()
    return urllib.error.HTTPError("https://api.test/v1", code, "err", {}, io.BytesIO(body))


def make_provider(*outcomes, **kwargs):
    opener = FakeOpener(*outcomes)
    sleeps = []
    provider = OpenAIProvider(
        api_key=kwargs.pop("api_key", KEY),
        model=kwargs.pop("model", "test-model"),
        base_url=kwargs.pop("base_url", "https://api.test/v1/"),
        opener=opener,
        sleep=sleeps.append,
        **kwargs,
    )
    return provider, opener, sleeps


class SuccessTests(unittest.TestCase):
    def test_parses_reply_model_and_usage(self):
        provider, _, _ = make_provider(
            ok_body("  Javob  ", model="served-model", usage={"total_tokens": 9, "x": "no"})
        )
        reply = provider.generate(MESSAGES)
        self.assertEqual(reply.text, "Javob")
        self.assertEqual(reply.model, "served-model")
        self.assertEqual(reply.usage, {"total_tokens": 9})

    def test_request_shape_and_headers(self):
        provider, opener, _ = make_provider(ok_body())
        provider.generate(MESSAGES)
        request = opener.requests[0]
        self.assertEqual(request.full_url, "https://api.test/v1/chat/completions")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {KEY}")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        body = json.loads(request.data)
        self.assertEqual(body["model"], "test-model")
        self.assertEqual(body["messages"][1], {"role": "user", "content": "Salom"})
        self.assertNotIn("max_completion_tokens", body)
        self.assertNotIn("temperature", body)
        self.assertEqual(opener.timeouts, [30])

    def test_authorization_is_not_forwarded_on_redirect(self):
        provider, opener, _ = make_provider(ok_body())
        provider.generate(MESSAGES)
        request = opener.requests[0]
        self.assertNotIn("Authorization", request.headers)  # only in unredirected headers
        self.assertIn("Authorization", request.unredirected_hdrs)

    def test_optional_parameters_are_sent_only_when_given(self):
        provider, opener, _ = make_provider(ok_body())
        provider.generate(MESSAGES, max_tokens=50, temperature=0.2)
        body = json.loads(opener.requests[0].data)
        self.assertEqual(body["max_completion_tokens"], 50)
        self.assertEqual(body["temperature"], 0.2)

    def test_redirects_are_refused(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil"))


class SetupTests(unittest.TestCase):
    def test_missing_key_or_model(self):
        with self.assertRaises(ProviderNotConfiguredError) as ctx:
            OpenAIProvider(api_key="", model="m")
        self.assertEqual(ctx.exception.code, "no_api_key")
        with self.assertRaises(ProviderNotConfiguredError) as ctx:
            OpenAIProvider(api_key=KEY, model="")
        self.assertEqual(ctx.exception.code, "no_model")

    def test_key_is_not_in_repr(self):
        provider, _, _ = make_provider()
        self.assertNotIn(KEY, repr(provider))
        self.assertNotIn(KEY, str(provider))


class ErrorTests(unittest.TestCase):
    def assert_error(self, outcomes, code, retryable, calls, sleeps_expected=None, **kwargs):
        provider, opener, sleeps = make_provider(*outcomes, **kwargs)
        with self.assertRaises(ProviderError) as ctx:
            provider.generate(MESSAGES)
        self.assertEqual(ctx.exception.code, code)
        self.assertEqual(ctx.exception.retryable, retryable)
        self.assertEqual(len(opener.requests), calls)
        if sleeps_expected is not None:
            self.assertEqual(sleeps, sleeps_expected)
        self.assertNotIn(KEY, str(ctx.exception))
        return ctx.exception

    def test_auth_errors_are_not_retried(self):
        for status in (401, 403):
            with self.subTest(status=status):
                exc = self.assert_error([http_error(status, "bad key")], "auth", False, 1, [])
                self.assertEqual(exc.status, status)

    def test_bad_request_is_not_retried(self):
        self.assert_error([http_error(400, "nope")], "error", False, 1, [])

    def test_rate_limit_is_retried_then_succeeds(self):
        provider, opener, sleeps = make_provider(http_error(429), ok_body("OK"))
        self.assertEqual(provider.generate(MESSAGES).text, "OK")
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(sleeps, [1.0])

    def test_server_errors_exhaust_retries_with_backoff(self):
        self.assert_error(
            [http_error(500), http_error(502), http_error(503)], "server", True, 3, [1.0, 2.0]
        )

    def test_network_errors_are_retried(self):
        self.assert_error(
            [urllib.error.URLError("down"), TimeoutError(), ConnectionResetError()],
            "network", True, 3, [1.0, 2.0],
        )

    def test_max_retries_zero_means_single_attempt(self):
        self.assert_error([http_error(500)], "server", True, 1, [], max_retries=0)

    def test_malformed_replies_are_bad_response_and_not_retried(self):
        bad_bodies = [
            b"not json",
            b"{}",
            json.dumps({"choices": []}).encode(),
            json.dumps({"choices": [{"message": {"content": None}}]}).encode(),
            ok_body("   "),
        ]
        for body in bad_bodies:
            with self.subTest(body=body):
                self.assert_error([body], "bad_response", False, 1, [])

    def test_server_message_echoing_the_key_is_masked(self):
        exc = self.assert_error(
            [http_error(401, f"Incorrect API key provided: {KEY}")], "auth", False, 1
        )
        self.assertIn("***", str(exc))


if __name__ == "__main__":
    unittest.main()
