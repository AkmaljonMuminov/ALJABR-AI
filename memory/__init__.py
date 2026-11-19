"""ALJABR MEMORY - short-term and user-approved long-term memory.

Short-term memory is ``brain.conversation.Conversation`` (current session only).
This package adds long-term memory stored in SQLite:

    models    MemoryItem
    guard     refuses to store passwords, API keys, tokens and card numbers
    store     MemoryStore: add / update / delete / search, isolated per user
    context   picks relevant notes for the AI prompt
    commands  chat commands: /remember /memories /edit /forget

A note is saved only when the user explicitly asks (``/remember``). The AI
cannot create, change or delete notes.
"""
