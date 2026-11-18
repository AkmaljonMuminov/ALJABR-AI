"""ALJABR CORE: application lifecycle, logging, messages and shared errors.

This package must stay free of imports from ``config`` so that ``config`` can
depend on ``core.errors`` without creating an import cycle.
"""

__version__ = "0.2.0"
APP_NAME = "ALJABR AI"
