"""OpenAI-compatible chat provider using only the Python standard library.

No ``openai`` package is needed, which keeps installation on Android simple.
Works with any server that implements the ``/chat/completions`` endpoint.

Security notes:
* The API key is sent in an *unredirected* header and redirects are refused,
  so the key cannot be forwarded to another host.
* The key is never part of ``repr()`` or of any exception message.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Callable, List, Optional

from brain.provider import LLMProvider
from brain.types import ChatResponse, Message
from core.errors import ProviderError, ProviderNotConfiguredError

USER_AGENT = "ALJABR-AI/0.2"
MAX_ERROR_DETAIL = 200


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects so credentials are never sent to a different URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


def _default_opener() -> Callable:
    return urllib.request.build_opener(_NoRedirect).open


def _error_detail(body: bytes) -> str:
    """Extract a short, safe error message from an API error body."""
    try:
        data = json.loads(body.decode("utf-8", errors="replace"))
        message = data["error"]["message"]
        if isinstance(message, str):
            return message[:MAX_ERROR_DETAIL]
    except (ValueError, KeyError, TypeError):
        pass
    return ""


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30,
        max_retries: int = 2,
        backoff: float = 1.0,
        opener: Optional[Callable] = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise ProviderNotConfiguredError("API key is not set", code="no_api_key")
        if not model:
            raise ProviderNotConfiguredError("AI model is not set", code="no_model")
        self._api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.backoff = backoff
        self._opener = opener or _default_opener()
        self._sleep = sleep

    def __repr__(self) -> str:
        return f"OpenAIProvider(model={self.model!r}, base_url={self.base_url!r})"

    # -- public API -------------------------------------------------------

    def generate(
        self,
        messages: List[Message],
        *,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ChatResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if max_tokens is not None:
            payload["max_completion_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        body = json.dumps(payload).encode("utf-8")

        for attempt in range(self.max_retries + 1):
            try:
                return self._send_once(body)
            except ProviderError as exc:
                if exc.retryable and attempt < self.max_retries:
                    self._sleep(self.backoff * (2 ** attempt))
                    continue
                raise
        raise ProviderError("request failed")  # pragma: no cover - loop always returns/raises

    # -- internals --------------------------------------------------------

    def _build_request(self, body: bytes) -> urllib.request.Request:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        )
        request.add_unredirected_header("Authorization", f"Bearer {self._api_key}")
        return request

    def _send_once(self, body: bytes) -> ChatResponse:
        request = self._build_request(body)
        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise self._http_error(exc) from None  # key-free message, no chained cause
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderError(
                f"network error: {type(exc).__name__}", code="network", retryable=True
            ) from None
        return self._parse(raw)

    def _http_error(self, exc: urllib.error.HTTPError) -> ProviderError:
        status = exc.code
        try:
            detail = _error_detail(exc.read())
        except OSError:
            detail = ""
        if detail:
            detail = detail.replace(self._api_key, "***")  # a server may echo the key back
        suffix = f": {detail}" if detail else ""
        message = f"HTTP {status}{suffix}"
        if status in (401, 403):
            return ProviderError(message, code="auth", status=status)
        if status == 429:
            return ProviderError(message, code="rate_limit", retryable=True, status=status)
        if status >= 500:
            return ProviderError(message, code="server", retryable=True, status=status)
        return ProviderError(message, code="error", status=status)

    def _parse(self, raw: bytes) -> ChatResponse:
        try:
            data = json.loads(raw.decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError("unexpected response format", code="bad_response") from None
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("empty reply from provider", code="bad_response")

        usage = {}
        raw_usage = data.get("usage")
        if isinstance(raw_usage, dict):
            usage = {k: v for k, v in raw_usage.items() if isinstance(v, int)}
        model = data.get("model") if isinstance(data.get("model"), str) else self.model
        return ChatResponse(text=text.strip(), model=model, usage=usage)
