"""ALJABR VOICE - speech-to-text, text-to-speech and wake phrase handling.

Modules:
    interfaces   SpeechToText / TextToSpeech interfaces
    runner       CommandRunner: runs external tools with a timeout (replaceable in tests)
    termux       adapters for Termux:API (termux-speech-to-text, termux-tts-speak)
    console      text fallback used when no speech tools are installed
    wake         wake phrase matching ("Salom, ALJABR")
    state        voice interaction state machine
    activation   what starts listening: push-to-talk now, background wake later
    text         prepares replies for speech
    session      VoiceSession: the push-to-talk conversation loop
    factory      picks the backend from settings
"""
