# ALJABR AI

*O'zbekcha versiya: [README.md](README.md)*

**Intelligence. Control. Independence.**

ALJABR AI is a modular, voice-controlled personal AI assistant. It starts as a
private assistant for one user on an Android smartphone (Uzbek first, with
Russian and English) and is designed to grow into a public AI platform later.

## Status

| Phase | Module | State |
|-------|--------|-------|
| 1 | ALJABR CORE (config, logging, entry point) | **Implemented and unit-tested** |
| 2 | ALJABR BRAIN (AI provider, conversations) | **Implemented and unit-tested** (not yet run against the real OpenAI service) |
| 3 | ALJABR VOICE (push-to-talk, speech in/out) | **Implemented and unit-tested** (not yet tried on a phone) |
| 4 | ALJABR MEMORY (SQLite, user-approved memory) | **Implemented and unit-tested** (not yet tried on a phone) |
| 5 | ALJABR COMMANDS (permission-checked actions) | Planned |
| 6 | ALJABR SECURITY (authorized defensive monitoring) | Planned |
| 7 | Android interface | Planned |
| 8 | Public multi-user platform (disabled at first) | Planned |

Phases 1-4 have been tested on Linux with Python 3.13. They have **not yet been
verified on an Android device**; see `docs/ANDROID_SETUP.md`. The AI calls were
tested against fake and local test servers only; a first real call with your own
key and model is still to be confirmed. Voice was tested with fake speech engines
and fake `termux-*` programs; real microphone, speaker and Uzbek speech quality
still need a test on your phone.

## Quick start (Termux on Android, or any Python 3.9+)

```bash
git clone https://github.com/AkmaljonMuminov/ALJABR-AI.git
cd ALJABR-AI
cp .env.example .env          # then set OPENAI_API_KEY and ALJABR_AI_MODEL in .env
python main.py --check        # system check
python main.py --chat         # chat with the AI (type /exit to quit)
python main.py --ask "Salom!" # ask a single question
python main.py --voice        # push-to-talk voice chat (text mode without Termux:API)
python -m unittest discover -s tests -t .   # run the tests
```

No third-party packages are needed.

## Memory (Phase 4)

Inside the chat (`python main.py --chat`):

```
/remember My favorite color is blue   # save a note (only when you say so)
/memories                             # list; /memories word  searches
/edit 1 New text                      # change
/forget 1                             # delete; /forget all deletes everything (confirmed)
```

Notes survive restarts and are used when ALJABR answers. Passwords, keys, tokens and
card numbers are refused. Details: `docs/PHASE4_MEMORY.md`.

## Project layout

```
main.py            entry point (--check, --chat, --ask, --voice, --version, --env-file)
config/            .env parsing and validated settings
core/              app lifecycle, secure logging, messages (uz/ru/en), errors
brain/             AI provider interface, OpenAI adapter, conversation, chat loop
voice/             speech input/output, wake phrase, push-to-talk session
memory/            long-term notes: store, search, secret guard, chat commands
database/          SQLite connection and migrations
commands/ security/ api/   (later phases)
tests/             unit tests
docs/              architecture, phase plans, Android setup
```

## Security and privacy rules

* Secrets live only in your local `.env` (git-ignored). Never commit it.
* Logs redact API keys, bearer tokens and `password=...` values. Message
  contents are not written to the log.
* The API key is sent only to the configured HTTPS address and is never
  forwarded on redirects (redirects are refused).
* **Your messages are sent to the AI provider you configure** (OpenAI by
  default) and are subject to its privacy policy. Do not type passwords or keys
  into the chat.
* The microphone is used only after you press Enter (push-to-talk); there is no
  background listening. What you say is never written to the log.
* Conversation history lives in memory only and disappears when the program
  ends. Long-term notes are saved only when you type `/remember`; the AI cannot
  create, change or delete notes.
* Passwords, API keys, tokens and card numbers are refused as notes (the filter is
  a heuristic, not a guarantee - do not write such data at all).
* Relevant notes are **sent to the AI provider** with your question. Set
  `ALJABR_MEMORY_IN_PROMPT=false` to stop that.
* Notes live in `data/aljabr.db` (owner-readable only) and are not encrypted. Every
  row carries a `user_id`, for the future multi-user mode.
* Sensitive actions (sending messages, deleting files, purchases, destructive
  commands) will require explicit user approval (Phase 5).
* Security scanning is limited to systems you explicitly authorize (Phase 6).

## Documentation

* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
* [`docs/PHASE1_PLAN.md`](docs/PHASE1_PLAN.md)
* [`docs/PHASE2_BRAIN.md`](docs/PHASE2_BRAIN.md)
* [`docs/PHASE3_VOICE.md`](docs/PHASE3_VOICE.md)
* [`docs/PHASE4_MEMORY.md`](docs/PHASE4_MEMORY.md)
* [`docs/ANDROID_SETUP.md`](docs/ANDROID_SETUP.md)
