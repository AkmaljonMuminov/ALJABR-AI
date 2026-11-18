"""ALJABR BRAIN - AI provider integration and conversation management.

Modules:
    types            Message and ChatResponse data types
    provider         LLMProvider interface (provider-independent)
    openai_provider  OpenAI-compatible adapter (standard library only)
    conversation     short-term in-memory history
    prompts          system prompt
    brain            Brain: provider + conversation + validation
    factory          create_provider(settings)
    cli              text chat loop used by main.py
"""
