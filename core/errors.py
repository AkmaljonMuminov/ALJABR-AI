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


class ProviderNotConfiguredError(ProviderError):
    """Raised when the provider cannot be used because settings are missing."""
