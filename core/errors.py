"""Shared exception types for ALJABR AI."""


class AljabrError(Exception):
    """Base class for all expected, handled ALJABR errors."""


class ConfigError(AljabrError):
    """Raised when configuration is missing, malformed or invalid."""
