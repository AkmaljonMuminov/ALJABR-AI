# Phase 3: ALJABR VOICE

## What it does

```bash
python main.py --voice
```

Push-to-talk voice chat: press **Enter**, speak, and ALJABR answers aloud (and
shows the text). Type `q` to quit. Without Termux:API it falls back to **text
mode** so the whole loop still works on any computer.

## How a turn works

```
trigger (Enter) -> listen -> [wake phrase check] -> brain -> speak
   IDLE            LISTENING                          THINKING   SPEAKING -> IDLE
```

* The microphone opens **only after you press Enter**. There is no background
  listening.
* With `ALJABR_VOICE_REQUIRE_WAKE=true`, speech must start with the wake phrase
  ("Salom, ALJABR"). Saying only the phrase makes ALJABR answer "Eshitaman." and
  listen once more for the command. Matching ignores case, punctuation and
  spacing ("salom al jabr" works).
* The wake phrase is matched on text the recogniser already produced. It is a
  filter on a push-to-talk turn, **not** a hands-free wake-word detector.
* Replies are shown in full on screen; for speech, markdown, code blocks and
  links are removed and very long answers are cut at a sentence end.
* The AI is told its reply will be read aloud, so it keeps answers short.

## Components

| File | Responsibility |
|------|----------------|
| `voice/interfaces.py` | `SpeechToText` / `TextToSpeech` interfaces |
| `voice/runner.py` | Runs external tools: no shell, timeout, errors become `VoiceError` |
| `voice/termux.py` | Termux:API adapters (`termux-speech-to-text`, `termux-tts-speak`) |
| `voice/console.py` | Text fallback (typed input, silent output) |
| `voice/wake.py` | Wake phrase matcher |
| `voice/state.py` | State machine: idle, listening, thinking, speaking, stopped |
| `voice/activation.py` | What starts listening: `PushToTalkTrigger` now |
| `voice/text.py` | Prepares replies for speech |
| `voice/session.py` | The conversation loop and error handling |
| `voice/factory.py` | Chooses the backend from settings |

## Setup on Android (Termux)

1. Install the **Termux:API** app (from F-Droid, same source as Termux).
2. In Termux: `pkg install termux-api`.
3. Android settings -> Apps -> Termux:API -> Permissions -> allow **Microphone**.
4. Test each tool on its own:
   ```bash
   termux-tts-speak -l uz "Salom, men ALJABR"
   termux-speech-to-text
   ```
5. `python main.py --check` should show `[OK] Ovoz tizimi`.

## Female voice and Uzbek: what is and is not guaranteed

* `termux-tts-speak` cannot pick a named voice. The voice comes from the TTS
  engine installed on the phone (Android settings -> Text-to-speech). ALJABR
  raises the pitch slightly (`ALJABR_TTS_PITCH=1.1`) and slows the speed a bit
  (`ALJABR_TTS_RATE=0.95`); change these on your phone until it sounds right.
* Uzbek speech output and recognition depend on the phone's engines. If your
  TTS engine has no Uzbek voice, `-l uz` may fall back to another language.
  Speech *recognition* uses the phone's own recognition language (it cannot be
  set from ALJABR). **This must be tested on your phone.**
* If Uzbek speech is poor, the text mode and the Russian/English settings keep
  everything usable while we look at other engines.

## Privacy

* Microphone use is explicit (one press, one phrase).
* What you say is never written to the log, only its length.
* Speech recognition is done by your phone's engine; check its privacy settings.
  The recognised text is then sent to your AI provider like any chat message.

## Background wake-word (future)

Designed for, **not implemented**. `ActivationTrigger` is the extension point;
`BackgroundWakeTrigger` is a placeholder that raises "unavailable". Doing it
properly on Android needs a foreground service with a visible notification, the
microphone permission, a battery plan, and an easy off switch. It will be a
separate, opt-in step.

## Tests

`python -m unittest discover -s tests -t .` (180 tests). Voice tests use fake
speech engines. `tests/test_main_voice.py` also runs the real subprocess path
with fake `termux-*` programs placed on `PATH`. No microphone, speaker or
internet is needed.

## Known limits

* Not tested on a real phone: the exact output format of
  `termux-speech-to-text` (ALJABR uses the last non-empty line) and the audio
  quality are unverified.
* No interruption ("barge-in") while ALJABR is speaking.
* One phrase per press; no continuous conversation yet.
