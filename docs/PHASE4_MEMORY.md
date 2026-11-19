# Phase 4: ALJABR MEMORY

## What it does

ALJABR can keep **notes that survive restarts** (long-term memory) and use them
when it answers. Short-term memory (the recent turns of the current chat) already
existed in Phase 2 (`brain/conversation.py`).

In `python main.py --chat`:

| Command | Effect |
|---------|--------|
| `/remember <text>` | Save a note (the only way a note is created) |
| `/memories [words]` | List notes, or search them |
| `/edit <id> <text>` | Change a note |
| `/forget <id>` | Delete one note |
| `/forget all` | Ask for confirmation; `/forget all ha` (uz) / `yes` (en) / `да` (ru) deletes everything |

Saved notes are also used by `--ask` and `--voice`.

## Consent: the user decides what is stored

* A note is created **only** when you type `/remember`. The AI cannot create,
  change or delete notes, and its system prompt tells it never to claim it did.
* Deleting everything needs a second, explicit confirmation.
* `ALJABR_MEMORY_ENABLED=false` turns long-term memory off completely (no
  database file is created and the commands are not available).
* `ALJABR_MEMORY_IN_PROMPT=false` keeps saving notes but stops sending them to
  the AI.

## What is never stored

The guard (`memory/guard.py`) refuses text that looks like a password, API key,
token, bearer header, PIN, payment card number (Luhn-checked) or a long random
string. Uzbek, Russian and English keywords are covered (`parol`, `пароль`,
`password`, ...) and `OPENAI_API_KEY=...` style names are caught.

It is a **safety net, not a guarantee**: it is a heuristic, it may refuse a
harmless note ("token 5000 so'm"), and it can miss an unusual secret. Do not put
secrets in notes at all.

## How notes reach the AI

For each question, `memory/context.py` selects up to
`ALJABR_MEMORY_MAX_PROMPT_ITEMS` notes (default 10): all of them if they fit,
otherwise those sharing the most words with the question (substring matching, so
Uzbek and Russian word endings still match), newest first on ties. They are
appended to the system message under a header that marks them as stored data,
not instructions. Notes are **not** added to the conversation history.

**Privacy:** the selected notes are sent to your AI provider together with your
question, exactly like chat messages. Only save what you are comfortable sending
there.

## Data and isolation

* Storage: SQLite file `data/aljabr.db` (inside `ALJABR_DATA_DIR`), created
  readable by its owner only (`600`).
* Every row has a `user_id` (`ALJABR_USER_ID`, default `owner`) and **every
  query is parameterised and filtered by it**. A note id belonging to another
  user behaves as "not found" for read, edit and delete, and limits are per user.
  This is what Phase 8 (multi-user) builds on; no data migration will be needed.
* Schema versions live in `PRAGMA user_version` (`database/migrations.py`). A
  failed migration is rolled back. A database created by a newer program is
  refused with a clear message instead of being damaged.
* Limits: 500 notes per user, 500 characters per note. Saving the same text twice
  keeps one note.
* Search runs in Python on the user's own notes, because SQLite `LIKE` is
  case-insensitive for ASCII only (not for Cyrillic or Uzbek letters).
* Note contents and spoken text are never written to the log.

## Failure behaviour

If the database cannot be opened (corrupt file, no permission), ALJABR tells you
("xotirasiz ishlayapman") and carries on **without memory**. A failing memory
lookup never blocks an answer. `python main.py --check` shows the database path
and note count.

## Components

| File | Responsibility |
|------|----------------|
| `database/migrations.py`, `database/connection.py` | Schema, migrations, private file |
| `memory/models.py` | `MemoryItem` |
| `memory/guard.py` | Refuses secrets |
| `memory/store.py` | `MemoryStore`: add/get/list/search/update/delete, per user |
| `memory/context.py` | Chooses and formats notes for the prompt |
| `memory/commands.py` | `/remember /memories /edit /forget` |

Memory does not import the brain or the voice package; the brain receives a plain
`memory_context(question) -> text` function.

## Tests

`python -m unittest discover -s tests -t .` (254 tests). They cover migrations
(including rollback, newer and corrupt files), the guard, the store (limits,
duplicates, isolation between users, persistence, SQL text stored as plain data,
database failure), search in Cyrillic, prompt selection, the commands in two
languages, and full runs through `main.py` (save, restart, use, edit, forget,
two users, disabled memory, broken database, no note text in the log). The
isolation and guard tests were checked by deliberately breaking the code and
confirming that the tests fail.

## Known limits

* Not tested on a phone. SQLite comes with Python in Termux; this was not
  verified on a device.
* Notes are **not encrypted** inside the file (only owner-readable). Anyone who
  can read your phone's Termux storage can read them.
* No automatic "should I remember this?" suggestions, no export or backup
  command (copy `data/aljabr.db` yourself), no semantic search.
* Memory commands work in text chat only. Voice commands arrive with
  Phase 5 (ALJABR COMMANDS).
* The guard is heuristic (see above).

## Next: Phase 5 (ALJABR COMMANDS)

A command registry with risk levels and explicit approval before sending
messages, deleting files, purchases or other destructive actions.
