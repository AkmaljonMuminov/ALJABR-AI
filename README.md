# ALJABR AI

**Intelligence. Control. Independence.**

ALJABR AI is a modular, voice-controlled personal AI assistant. It starts as a
private assistant for one user on an Android smartphone (Uzbek first, with
Russian and English) and is designed to grow into a public AI platform later.

## Status

| Phase | Module | State |
|-------|--------|-------|
| 1 | ALJABR CORE (config, logging, entry point) | **Implemented and unit-tested** |
| 2 | ALJABR BRAIN (AI provider, conversations) | Planned |
| 3 | ALJABR VOICE (speech-to-text, female voice) | Planned |
| 4 | ALJABR MEMORY (SQLite, user-approved memory) | Planned |
| 5 | ALJABR COMMANDS (permission-checked actions) | Planned |
| 6 | ALJABR SECURITY (authorized defensive monitoring) | Planned |
| 7 | Android interface | Planned |
| 8 | Public multi-user platform (disabled at first) | Planned |

Phase 1 has been tested on Linux with Python 3.13. It has **not yet been
verified on an Android device**; see `docs/ANDROID_SETUP.md`.

## Quick start (Termux on Android, or any Python 3.9+)

```bash
git clone https://github.com/AkmaljonMuminov/ALJABR-AI.git
cd ALJABR-AI
cp .env.example .env          # then edit .env if you want to change settings
python main.py --check        # system check
python main.py                # greeting
python -m unittest discover -s tests -t .   # run the tests
```

Phase 1 needs **no third-party packages**.

## Project layout

```
main.py            entry point (--check, --version, --env-file)
config/            .env parsing and validated settings
core/              app lifecycle, secure logging, messages (uz/ru/en), errors
brain/ voice/ memory/ commands/ security/ api/ database/   (later phases)
tests/             unit tests
docs/              architecture, Phase 1 plan, Android setup
```

## Security and privacy rules

* Secrets live only in your local `.env` (git-ignored). Never commit it.
* Logs redact API keys, bearer tokens and `password=...` values.
* Sensitive actions (sending messages, deleting files, purchases, destructive
  commands) will require explicit user approval (Phase 5).
* Security scanning is limited to systems you explicitly authorize (Phase 6).

## Documentation

* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
* [`docs/PHASE1_PLAN.md`](docs/PHASE1_PLAN.md)
* [`docs/ANDROID_SETUP.md`](docs/ANDROID_SETUP.md)
