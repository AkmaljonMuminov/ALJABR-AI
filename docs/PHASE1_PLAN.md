# Phase 1 Plan: ALJABR CORE

## 1. Repository analysis

Inspected: `https://github.com/AkmaljonMuminov/ALJABR-AI` (branch `main`,
single commit "Initial commit").

| Item | Finding |
|------|---------|
| Files | Only `README.md`, containing a single line: `# ALJABR-AI` |
| Code, tests, docs | None |
| `.gitignore` | Missing |
| Dependency file | Missing |
| License | Missing |

Nothing existing needed to be preserved except the project name; `README.md`
was replaced with a full README after being inspected.

## 2. Missing files and architectural issues

1. **No `.gitignore`**: a local `.env` with an API key, SQLite memory database
   or logs could be committed by accident. Added first.
2. **No configuration layer**: secrets and options need one validated source.
3. **No logging policy**: logs could leak keys. Redaction is built in from the start.
4. **No tests**: added with Phase 1 so later phases build on a verified base.
5. **No dependency policy**: Android lacks wheels for many desktop packages.
   Phase 1 uses only the standard library.
6. **No documented Android path**: added `docs/ANDROID_SETUP.md`.
7. **No place for Uzbek text**: centralised in `core/messages.py` so the code
   stays English and user-facing text stays Uzbek/Russian/English.

## 3. Proposed project structure

```
ALJABR-AI/
  main.py
  requirements.txt
  .env.example
  .gitignore
  pytest.ini
  README.md
  config/       __init__.py  env_loader.py  settings.py
  core/         __init__.py  app.py  errors.py  logging_setup.py  messages.py
  brain/        (Phase 2)
  voice/        (Phase 3)
  memory/       (Phase 4)
  commands/     (Phase 5)
  security/     (Phase 6)
  api/          (Phase 7)
  database/     (Phase 4)
  tests/        test_app.py  test_env_loader.py  test_logging.py
                test_messages.py  test_settings.py
  docs/         ARCHITECTURE.md  PHASE1_PLAN.md  ANDROID_SETUP.md
```

## 4. Phase 1 scope

In scope: project structure, configuration, secure logging, entry point,
system checks, Uzbek/Russian/English messages, tests, documentation.

Out of scope (later phases): AI calls, voice, memory, commands, security
monitoring, UI. The empty packages exist only to fix the structure.

## 5. Acceptance criteria and results

| Criterion | Result |
|-----------|--------|
| `python main.py` prints the Uzbek greeting | Verified |
| `python main.py --check` reports Python, data dir, log dir, API key | Verified |
| Invalid configuration gives a clear message and exit code 2 | Verified |
| Secrets never appear in `repr()`, reports or the log file | Verified (unit tests and a manual run with a fake key) |
| Unexpected errors are logged with details, but not shown as a traceback on screen | Verified (this was a bug found during testing and fixed) |
| Log folder unusable: app keeps running with console logging | Verified |
| Works from any working directory | Verified |
| No third-party dependencies | Verified |
| Unit tests | 43 tests pass with `unittest` and `pytest` |

**Test environment**: Linux, Python 3.13. **Not yet tested on Android.** The
code avoids syntax newer than Python 3.9, but 3.9-3.12 was not run here.

## 6. Next step

After Phase 1 is confirmed on the phone, start Phase 2 (ALJABR BRAIN):
provider interface, OpenAI adapter, conversation manager, tests with a fake
provider so no API key is needed for testing.
