# Phase 2: ALJABR BRAIN

## What it does

`Brain.ask(text)` sends the user's text, the recent conversation and a system
prompt to an AI provider and returns the reply. Use it from the command line:

```bash
python main.py --chat            # interactive; /clear forgets, /exit quits
python main.py --ask "Salom!"    # one question, prints the answer
```

## Components

| File | Responsibility |
|------|----------------|
| `brain/types.py` | `Message`, `ChatResponse` data types |
| `brain/provider.py` | `LLMProvider` interface (`generate(messages) -> ChatResponse`) |
| `brain/openai_provider.py` | OpenAI-compatible adapter using `urllib` (no extra packages) |
| `brain/conversation.py` | In-memory history, trimmed to `ALJABR_AI_MAX_HISTORY` messages |
| `brain/prompts.py` | System prompt (language, date, honesty and secrecy rules) |
| `brain/brain.py` | Validation, history, rollback on failure, safe logging |
| `brain/factory.py` | `create_provider(settings)`; registry of providers |
| `brain/cli.py` | Chat loop and localized error messages |

## Configuration

Set in `.env` (see `.env.example`): `ALJABR_AI_PROVIDER`, `ALJABR_AI_MODEL`,
`OPENAI_API_KEY`, `ALJABR_AI_BASE_URL`, `ALJABR_AI_TIMEOUT`,
`ALJABR_AI_MAX_HISTORY`. The model is deliberately not hardcoded.

## Behaviour and design decisions

* **Provider-independent**: only `brain/openai_provider.py` knows about OpenAI.
  To add a provider, implement `LLMProvider` and register it in
  `brain/factory.py`. Any server with an OpenAI-compatible `/chat/completions`
  endpoint also works by changing `ALJABR_AI_BASE_URL`.
* **Errors**: every failure becomes a `ProviderError` with a stable `code`
  (`no_api_key`, `no_model`, `auth`, `rate_limit`, `network`, `server`,
  `bad_response`, `error`) that maps to an Uzbek/Russian/English message.
* **Retries**: network errors, HTTP 429 and 5xx are retried twice with
  1 s then 2 s waits. Authentication and bad-request errors are not retried.
* **Failed requests leave no trace**: if a call fails, the question is removed
  from the history so the user can simply retry.
* **Input limits**: empty input and input over 4000 characters are rejected
  before any network call.
* **Context**: the last `ALJABR_AI_MAX_HISTORY` messages (default 20) are sent
  with each question. History is in memory only (persistent memory is Phase 4).
* **Honest assistant**: the system prompt tells the model it can only chat, so
  it must not claim to have run commands, sent messages or saved memories.
* **Secrets**: the key is sent in an unredirected `Authorization` header,
  redirects are refused, the key is masked in errors, logs and `repr()`.
  Message contents are never logged (only sizes and timing).
* **HTTPS only**: `ALJABR_AI_BASE_URL` must be `https://`, except `http://`
  for `localhost`/`127.0.0.1`.
* **Privacy**: messages are sent to the configured provider.

## Tests

`python -m unittest discover -s tests -t .` (105 tests). AI tests use a fake
provider, a fake transport, and a throwaway local HTTP server
(`tests/test_openai_local_server.py`) that exercises the real `urllib` code
path. No internet or API key is needed to run them.

## Known limits

* Not yet run against the real OpenAI service or on an Android device.
* Replies arrive whole (no streaming) and there is no usage/cost tracking yet.
* HTTP 429 caused by an exhausted quota is retried like a temporary limit.
* The model's quality in Uzbek depends on the model you choose; compare a few.

## Next: Phase 3 (ALJABR VOICE)

Push-to-talk speech input and female voice output, behind provider interfaces
like the brain. Whether the phone's speech engines handle Uzbek well must be
tested on the device first.
