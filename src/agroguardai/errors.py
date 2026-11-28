"""Typed errors raised by AgroGuardAI configuration and model selection."""


class AgroGuardAIError(Exception):
    """Base class for expected, user-actionable AgroGuardAI errors."""


class ConfigurationError(AgroGuardAIError, ValueError):
    """Raised when project configuration is missing, malformed, or ambiguous."""


class RegistryError(AgroGuardAIError):
    """Base class for model registry failures."""


class DuplicateModelError(RegistryError):
    """Raised when a provider/model identifier is registered more than once."""


class ProviderIdentityMismatchError(RegistryError):
    """Raised when catalog records do not match the provider that supplied them."""


class UnknownProviderError(RegistryError):
    """Raised when a selection names a provider with no registered catalog."""


class UnknownModelError(RegistryError):
    """Raised when a provider does not expose the exact selected model identifier."""


class ModelUnavailableError(RegistryError):
    """Raised when a registered model is disabled or unavailable."""


class UnsupportedOperationError(RegistryError):
    """Raised when a model does not support the requested operation."""


class ModelTermsError(RegistryError):
    """Raised when model terms have not been reviewed or prohibit an operation."""


class ProviderError(AgroGuardAIError):
    """Base class for provider communication and protocol failures."""


class ProviderRequestMismatchError(ProviderError):
    """Raised when an adapter is asked to execute for a different provider."""


class ProviderAuthenticationError(ProviderError):
    """Raised when a provider rejects the supplied credentials."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider rate-limits a request."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out."""


class ProviderConnectionError(ProviderError):
    """Raised when a provider cannot be reached."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider returns a server-side failure."""


class ProviderRequestError(ProviderError):
    """Raised when a provider rejects a request for a non-authentication reason."""


class ProviderProtocolError(ProviderError):
    """Raised when a provider response does not match the expected API schema."""


class ProviderResponseMismatchError(ProviderError):
    """Raised when a provider returns a model other than the one explicitly selected."""
