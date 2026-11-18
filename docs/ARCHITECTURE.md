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
main.py -> core.app -> config, core.*, (later) brain, voice, memory, commands, security
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
  error, 3 a required check failed.

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
