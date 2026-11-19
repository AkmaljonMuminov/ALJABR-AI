# Android Setup (Termux)

Termux is a terminal app that runs real Python on Android. Install it from
**F-Droid** (https://f-droid.org); the Google Play version is outdated.

> Phases 1-3 were tested on Linux. Running these steps on your phone is the first
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
nano .env
```

For AI chat set these two lines in `.env` (save in nano with Ctrl+O, Enter, then
exit with Ctrl+X):

```
OPENAI_API_KEY=your key here
ALJABR_AI_MODEL=the model name you want to use
```

Never share `.env`, never paste the key into a chat, and never commit it (it is
in `.gitignore`).

## 4. Run and test

```bash
python main.py --check
python main.py
python -m unittest discover -s tests -t .
python main.py --chat
```

Expected: `--check` prints `[OK]` lines and ends with
"Barcha majburiy tekshiruvlar muvaffaqiyatli."; the unit tests end with `OK`.
The model and API key lines show `[ixtiyoriy]` (optional) until you set them.
In `--chat`, type a message and press Enter; `/clear` forgets the conversation
and `/exit` quits. If the key or model is missing, the app tells you in Uzbek
what to add to `.env`.

Optional: `pip install pytest` and run `pytest`.

## 5. Voice (optional, Phase 3)

```bash
pkg install termux-api      # plus the Termux:API app from F-Droid
```

Then allow the **Microphone** for the Termux:API app (Android settings -> Apps ->
Termux:API -> Permissions) and test:

```bash
termux-tts-speak -l uz "Salom, men ALJABR"
termux-speech-to-text
python main.py --check      # should show [OK] Ovoz tizimi
python main.py --voice      # press Enter, speak; q quits
```

Without Termux:API, `--voice` runs in text mode. Details, including what depends
on your phone's speech engines, are in `docs/PHASE3_VOICE.md`.

## 6. Update later

```bash
cd ALJABR-AI
git pull
```

## 7. Publishing your changes from the phone

Use a **fine-grained personal access token** limited to this one repository
with "Contents: read and write". Never paste the token into a chat or a file in
the repository.

```bash
git config user.name "Your Name"
git config user.email "you@example.com"
git add .
git status              # confirm .env is NOT listed
git commit -m "Describe your change here"
git push
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python: command not found` | `pkg install python` |
| `ModuleNotFoundError: config` | Run from the project folder, or use `python /full/path/to/main.py` |
| Cannot write to data folder | Set `ALJABR_DATA_DIR` in `.env` to a folder you own |
| "AI xizmatiga ulanib bo'lmadi" (cannot reach AI service) | Check the phone's internet connection; try again |
| "AI kaliti qabul qilinmadi" (key rejected) | Re-check `OPENAI_API_KEY` in `.env` for typos or extra spaces |
| `--voice` says Termux:API not found | Install the Termux:API app and `pkg install termux-api` |
| "Mikrofon ruxsati yo'q" (no microphone permission) | Allow Microphone for the Termux:API app in Android settings |
| Speech is not Uzbek or sounds wrong | Check Android settings -> Text-to-speech; adjust `ALJABR_TTS_*` in `.env` |
| Termux is killed in the background | Disable battery optimization for Termux (needed from Phase 3) |
