# Android Setup (Termux)

Termux is a terminal app that runs real Python on Android. Install it from
**F-Droid** (https://f-droid.org); the Google Play version is outdated.

> Phase 1 was tested on Linux. Running these steps on your phone is the first
> Android verification. Please report any error message you see.

## 1. Install tools

```bash
pkg update && pkg upgrade
pkg install python git nano
python --version        # should be 3.9 or newer
```

## 2. Get the project

```bash
git clone https://github.com/AkmaljonMuminov/ALJABR-AI.git
cd ALJABR-AI
```

## 3. Configure

```bash
cp .env.example .env
nano .env               # optional in Phase 1
```

Never share `.env` and never commit it (it is in `.gitignore`).

## 4. Run and test

```bash
python main.py --check
python main.py
python -m unittest discover -s tests -t .
```

Expected: `--check` prints `[OK]` lines and ends with
"Barcha majburiy tekshiruvlar muvaffaqiyatli."; the unit tests end with `OK`.
The API key line shows `[ixtiyoriy]` (optional) until Phase 2.

Optional: `pip install pytest` and run `pytest`.

## 5. Update later

```bash
cd ALJABR-AI
git pull
```

## 6. Publishing your changes from the phone

Use a **fine-grained personal access token** limited to this one repository
with "Contents: read and write". Never paste the token into a chat or a file in
the repository.

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
git add .
git status              # confirm .env is NOT listed
git commit -m "Phase 1: ALJABR CORE"
git push
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python: command not found` | `pkg install python` |
| `ModuleNotFoundError: config` | Run from the project folder, or use `python /full/path/to/main.py` |
| Cannot write to data folder | Set `ALJABR_DATA_DIR` in `.env` to a folder you own |
| Termux is killed in the background | Disable battery optimization for Termux (needed from Phase 3) |
