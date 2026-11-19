"""Shared exception types for ALJABR AI."""


class AljabrError(Exception):
    """Base class for all expected, handled ALJABR errors."""


class ConfigError(AljabrError):
    """Raised when configuration is missing, malformed or invalid."""


class InputError(AljabrError):
    """Raised when user input is rejected (``code``: ``empty`` or ``too_long``)."""

    def __init__(self, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.code = code


class ProviderError(AljabrError):
    """Raised when an AI provider call fails.

    ``code`` is a stable identifier used to pick a user-facing message:
    ``no_api_key``, ``no_model``, ``auth``, ``rate_limit``, ``network``,
    ``server``, ``bad_response`` or ``error``.
    """

    def __init__(
        self,
        message: str,
        code: str = "error",
        retryable: bool = False,
        status=None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.status = status


class VoiceError(AljabrError):
    """Raised when speech input or output fails.

    ``code``: ``unavailable`` (tool not installed), ``permission`` (no microphone
    access), ``timeout``, ``failed``, or ``closed`` (text input ended; not a fault).
    """

    def __init__(self, message: str, code: str = "failed") -> None:
        super().__init__(message)
        self.code = code


class DatabaseError(AljabrError):
    """Raised when the SQLite database cannot be opened, migrated or used."""


class MemoryStoreError(AljabrError):
    """Raised when a memory operation is rejected or fails.

    ``code``: ``empty``, ``too_long``, ``secret`` (looks like a password/key/
    token/card number), ``limit`` (too many notes), ``not_found`` or
    ``storage`` (database problem).
    """

    def __init__(self, message: str, code: str = "storage") -> None:
        super().__init__(message)
        self.code = code


class ProviderNotConfiguredError(ProviderError):
    """Raised when the provider cannot be used because settings are missing."""
