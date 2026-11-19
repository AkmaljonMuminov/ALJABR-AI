# ALJABR AI Architecture

## Principles

1. **Modular**: one clear responsibility per package; no giant files.
2. **Android-first**: standard library by default; every third-party package
   must be verified on Android/Termux before it is added to `requirements.txt`.
3. **Provider-independent**: AI, speech and storage sit behind small interfaces
   so vendors can be swapped.
4. **Private by default**: secrets only in environment/`.env`; logs are redacted;
   sensitive actions need explicit approval.
5. **Single user now, multi-user later**: nothing in Phase 1-7 may block Phase 8.

## Package map

| Package | Responsibility | Phase |
|---------|----------------|-------|
| `config/` | Read `.env` and environment, validate, expose immutable `Settings` | 1 |
| `core/` | App lifecycle, secure logging, user-facing messages, shared errors | 1 |
| `brain/` | AI provider interface, OpenAI adapter, conversation/context management | 2 |
| `voice/` | Speech-to-text, text-to-speech, push-to-talk, wake phrase state machine | 3 |
| `database/` | SQLite connection, migrations, shared access layer | 4 |
| `memory/` | Short-term and approved long-term memory, search, update, delete | 4 |
| `commands/` | Command registry, permission checks, approval prompts | 5 |
| `security/` | Authorized monitoring: health, file integrity, network diagnostics, reports | 6 |
| `api/` | Authenticated local HTTP API for the mobile UI | 7 |
| `tests/` | Unit tests for every critical component | all |

## Dependency direction

```
main.py -> core.app, brain.*, voice.*, memory.*, database.*, config, core.*   (later also commands, security)
voice   -> brain (Brain, describe_error), core; never imports config or main
brain   -> core (errors, logging); never imports config, voice, memory or main
memory  -> core, database; never imports brain, voice, config or main
config  -> core.errors only
core/__init__.py and core/errors.py import nothing from the project
```

`config` may import `core.errors`, so `core/__init__.py` must never import
`config` (this prevents an import cycle).

## Phase 1 components

* `config/env_loader.py` - dependency-free `.env` parser.
* `config/settings.py` - validation, defaults, `Secret` wrapper that hides values
  from `repr()`/`str()`.
* `core/logging_setup.py` - rotating private log file, quiet console, redaction of
  secrets in every line and traceback, console falls back gracefully if the log
  folder is unusable.
* `core/messages.py` - all user-facing text in Uzbek, Russian and English.
* `core/app.py` - `Application` (start/stop, banner, system checks).
* `main.py` - CLI with exit codes: 0 ok, 1 unexpected error, 2 configuration
  error, 3 a required check failed, 4 the AI request could not be completed,
  5 the voice system is unavailable (missing tools or microphone permission).

## Phase 2 components (ALJABR BRAIN)

See [`PHASE2_BRAIN.md`](PHASE2_BRAIN.md) for details.

* `brain/provider.py` - `LLMProvider` interface; the rest of the app depends only on this.
* `brain/openai_provider.py` - OpenAI-compatible adapter (standard library, retries,
  no redirects, key masked everywhere).
* `brain/conversation.py` - short-term in-memory history with trimming.
* `brain/brain.py` - `Brain.ask()`: validation, system prompt, history, rollback on failure.
* `brain/factory.py` - `create_provider(settings)`; add new providers to `PROVIDERS`.
* `brain/cli.py` - text chat loop and localized error messages.

## Phase 3 components (ALJABR VOICE)

See [`PHASE3_VOICE.md`](PHASE3_VOICE.md) for details.

* `voice/interfaces.py` - `SpeechToText` / `TextToSpeech`; the session depends only on these.
* `voice/termux.py`, `voice/console.py` - Android (Termux:API) and text-mode backends.
* `voice/runner.py` - shell-free command runner with timeout.
* `voice/wake.py`, `voice/state.py` - wake phrase matching and the state machine.
* `voice/activation.py` - `ActivationTrigger`: push-to-talk now, background wake later.
* `voice/session.py` - the turn loop; `voice/factory.py` - backend selection.

## Phase 4 components (ALJABR MEMORY)

See [`PHASE4_MEMORY.md`](PHASE4_MEMORY.md) for details.

* `database/` - `open_database(path)`: private SQLite file, versioned migrations with rollback.
* `memory/store.py` - `MemoryStore`, every query filtered by `user_id`.
* `memory/guard.py` - refuses passwords, keys, tokens, card numbers.
* `memory/context.py` - picks notes for the prompt; the brain only receives a
  `memory_context(question) -> text` function, so it never imports `memory`.
* `memory/commands.py` - `/remember /memories /edit /forget` for the chat loop.

## Design decisions for later phases

* **Voice (Phase 3)**: start with push-to-talk. Android restricts background
  microphone access and drains battery, so continuous wake-phrase detection needs
  a foreground service with a visible notification. Termux:API offers
  `termux-tts-speak` and `termux-speech-to-text`; whether they support Uzbek
  well on a given phone must be tested on the device before relying on them.
* **Memory (Phase 4)**: every table carries a `user_id` from day one so Phase 8
  needs no data migration. Passwords, API keys and tokens are rejected before
  storage. Long-term memory is saved only after user approval.
* **Commands (Phase 5)**: allow-list of commands; each has a risk level. Sending
  messages, deleting files, purchases and destructive actions always ask first.
* **Security (Phase 6)**: targets must be listed in an explicit authorized-scope
  file; anything outside it is refused. Defensive monitoring only.
* **API (Phase 7)**: token authentication, input validation, bound to localhost
  by default.
* **Public platform (Phase 8)**: registration disabled by a configuration flag in
  the first version.
