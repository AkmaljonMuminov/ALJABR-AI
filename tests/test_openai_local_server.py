"""Run the real OpenAIProvider (real urllib code path) against a local test server."""

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from brain.openai_provider import OpenAIProvider
from brain.types import Message
from core.errors import ProviderError

KEY = "sk-localserver-test-key-123456"


class Handler(BaseHTTPRequestHandler):
    log = []          # (path, authorization header, parsed JSON body)
    script = []       # list of (status, headers, body) answers, consumed in order

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        Handler.log.append((self.path, self.headers.get("Authorization"), body))
        status, headers, payload = Handler.script.pop(0)
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        data = json.dumps(payload).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # keep test output quiet
        pass


def reply(text):
    return (200, {}, {"model": "local-model", "choices": [{"message": {"content": text}}]})


class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.log = []
        Handler.script = []
        patcher = mock.patch.dict(os.environ, {"no_proxy": "127.0.0.1,localhost", "NO_PROXY": "127.0.0.1,localhost"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sleeps = []
        self.provider = OpenAIProvider(
            api_key=KEY, model="local-model", base_url=self.base_url,
            timeout=5, sleep=self.sleeps.append,
        )
        self.messages = [Message("system", "rules"), Message("user", "Salom")]

    def test_successful_round_trip_sends_key_and_json(self):
        Handler.script = [reply("Assalomu alaykum")]
        result = self.provider.generate(self.messages)
        self.assertEqual(result.text, "Assalomu alaykum")
        path, auth, body = Handler.log[0]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(auth, f"Bearer {KEY}")
        self.assertEqual(body["model"], "local-model")
        self.assertEqual(body["messages"][1], {"role": "user", "content": "Salom"})

    def test_server_error_is_retried_then_succeeds(self):
        Handler.script = [(503, {}, {"error": {"message": "busy"}}), reply("OK")]
        self.assertEqual(self.provider.generate(self.messages).text, "OK")
        self.assertEqual(len(Handler.log), 2)
        self.assertEqual(self.sleeps, [1.0])

    def test_auth_error_is_not_retried(self):
        Handler.script = [(401, {}, {"error": {"message": "bad key"}})]
        with self.assertRaises(ProviderError) as ctx:
            self.provider.generate(self.messages)
        self.assertEqual(ctx.exception.code, "auth")
        self.assertEqual(len(Handler.log), 1)

    def test_redirect_is_refused_and_not_followed(self):
        Handler.script = [(302, {"Location": f"{self.base_url}/elsewhere"}, {}), reply("never")]
        with self.assertRaises(ProviderError) as ctx:
            self.provider.generate(self.messages)
        self.assertEqual(ctx.exception.status, 302)
        self.assertEqual(len(Handler.log), 1)  # the redirect target was never requested

    def test_connection_failure_is_a_retryable_network_error(self):
        dead = OpenAIProvider(
            api_key=KEY, model="m", base_url="http://127.0.0.1:1/v1",
            timeout=5, max_retries=1, sleep=self.sleeps.append,
        )
        with self.assertRaises(ProviderError) as ctx:
            dead.generate(self.messages)
        self.assertEqual(ctx.exception.code, "network")
        self.assertEqual(self.sleeps, [1.0])
        self.assertNotIn(KEY, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
