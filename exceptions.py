class CustomTlgError(Exception):
    """Base class for custom errors with tlg notification."""


class CustomNoTlgError(Exception):
    """Base class for custom errors without tlg notification."""


class CustomRequestError(CustomTlgError):
    """Class for API request errors."""


class CustomTypeError(CustomTlgError):
    """Class for type errors."""


class CustomKeyError(CustomTlgError):
    """Class for key errors."""


class CustomTokenValidationError(CustomNoTlgError):
    """Class for token validation errors."""


class CustomTlgSendMessageError(CustomNoTlgError):
    """Class for telegram send message errors."""
