"""Core model, operation, and provider request contracts.

These types intentionally do not implement any vendor-specific network calls.
Provider adapters must implement the shared protocol in :mod:`agroguardai.providers`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Iterable
from urllib.parse import urlparse

from .errors import ConfigurationError, ProviderResponseMismatchError


class Operation(str, Enum):
    """Operations a model may explicitly support."""

    HOSTED_INFERENCE = "hosted_inference"
    LOCAL_INFERENCE = "local_inference"
    FINE_TUNING = "fine_tuning"
    WEIGHT_EXPORT = "weight_export"


class Modality(str, Enum):
    """Input/output modalities advertised by a model."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class TermsStatus(str, Enum):
    """Project review state for the upstream model's terms."""

    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    RESTRICTED = "restricted"


class MessageRole(str, Enum):
    """Roles supported by the initial text-generation contract."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


def _require_identifier(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{field_name} must be a non-empty string.")
    if value != value.strip():
        raise ConfigurationError(f"{field_name} must not have leading or trailing whitespace.")
    if any(character.isspace() for character in value):
        raise ConfigurationError(f"{field_name} must not contain whitespace.")
    return value


def _enum_values(
    values: Iterable[Enum | str] | Enum | str,
    enum_type: type[Enum],
    field_name: str,
) -> frozenset:
    if isinstance(values, (str, Enum)):
        values = (values,)
    try:
        return frozenset(enum_type(value) for value in values)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(item.value for item in enum_type)
        raise ConfigurationError(f"{field_name} must contain values from: {allowed}.") from exc


def _validate_terms_evidence(terms_url: str | None, reviewed_at: str | None) -> None:
    if terms_url is None or reviewed_at is None:
        raise ConfigurationError(
            "A reviewed or restricted model must include terms_url and terms_reviewed_at."
        )
    parsed_url = urlparse(terms_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ConfigurationError("terms_url must be an absolute HTTPS URL.")
    if not isinstance(reviewed_at, str):
        raise ConfigurationError("terms_reviewed_at must be an ISO 8601 timestamp.")
    try:
        timestamp = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConfigurationError("terms_reviewed_at must be a valid ISO 8601 timestamp.") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ConfigurationError("terms_reviewed_at must include a timezone offset.")


@dataclass(frozen=True, slots=True)
class ModelDescriptor:
    """Verified metadata for one exact provider/model identifier.

    `operations` must describe capabilities that have actually been checked.
    Unknown capabilities must not be advertised. Fine-tuning and weight export
    are additionally blocked until the upstream terms have been reviewed.
    """

    provider_id: str
    model_id: str
    display_name: str
    operations: frozenset[Operation]
    input_modalities: frozenset[Modality] = frozenset({Modality.TEXT})
    output_modalities: frozenset[Modality] = frozenset({Modality.TEXT})
    context_window: int | None = None
    terms_status: TermsStatus = TermsStatus.UNREVIEWED
    terms_url: str | None = None
    terms_reviewed_at: str | None = None
    available: bool = True

    def __post_init__(self) -> None:
        _require_identifier(self.provider_id, "provider_id")
        _require_identifier(self.model_id, "model_id")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ConfigurationError("display_name must be a non-empty string.")

        operations = _enum_values(self.operations, Operation, "operations")
        if not operations:
            raise ConfigurationError("A model must advertise at least one supported operation.")
        object.__setattr__(self, "operations", operations)
        object.__setattr__(
            self,
            "input_modalities",
            _enum_values(self.input_modalities, Modality, "input_modalities"),
        )
        object.__setattr__(
            self,
            "output_modalities",
            _enum_values(self.output_modalities, Modality, "output_modalities"),
        )

        try:
            terms_status = TermsStatus(self.terms_status)
        except (TypeError, ValueError) as exc:
            allowed = ", ".join(item.value for item in TermsStatus)
            raise ConfigurationError(f"terms_status must be one of: {allowed}.") from exc
        object.__setattr__(self, "terms_status", terms_status)

        if terms_status in {TermsStatus.REVIEWED, TermsStatus.RESTRICTED}:
            _validate_terms_evidence(self.terms_url, self.terms_reviewed_at)
        elif self.terms_reviewed_at is not None:
            raise ConfigurationError(
                "terms_reviewed_at must be omitted while terms_status is 'unreviewed'."
            )
        elif self.terms_url is not None and (
            not isinstance(self.terms_url, str) or not self.terms_url.strip()
        ):
            raise ConfigurationError("terms_url must be a non-empty HTTPS URL or None.")

        if self.context_window is not None and (
            isinstance(self.context_window, bool)
            or not isinstance(self.context_window, int)
            or self.context_window <= 0
        ):
            raise ConfigurationError("context_window must be a positive integer or None.")
        if not isinstance(self.available, bool):
            raise ConfigurationError("available must be a boolean.")


@dataclass(frozen=True, slots=True)
class ModelSelection:
    """An explicit request for one provider, exact model, and operation."""

    provider_id: str
    model_id: str
    operation: Operation

    def __post_init__(self) -> None:
        _require_identifier(self.provider_id, "provider_id")
        _require_identifier(self.model_id, "model_id")
        try:
            object.__setattr__(self, "operation", Operation(self.operation))
        except (TypeError, ValueError) as exc:
            allowed = ", ".join(item.value for item in Operation)
            raise ConfigurationError(f"operation must be one of: {allowed}.") from exc

    @classmethod
    def from_mapping(cls, values: dict[str, object]) -> ModelSelection:
        """Build a selection from a mapping, rejecting missing and unknown keys."""

        if not isinstance(values, dict):
            raise ConfigurationError("Model selection must be a mapping.")
        if any(not isinstance(key, str) for key in values):
            raise ConfigurationError("Model selection field names must be strings.")
        required = {"provider", "model_id", "operation"}
        missing = required - values.keys()
        unknown = values.keys() - required
        if missing:
            raise ConfigurationError(
                f"Model selection is missing required fields: {sorted(missing)}."
            )
        if unknown:
            raise ConfigurationError(f"Unknown model-selection fields: {sorted(unknown)}.")
        return cls(
            provider_id=values["provider"],  # type: ignore[arg-type]
            model_id=values["model_id"],  # type: ignore[arg-type]
            operation=values["operation"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One text message for the initial text-generation contract."""

    role: MessageRole
    content: str

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "role", MessageRole(self.role))
        except (TypeError, ValueError) as exc:
            allowed = ", ".join(item.value for item in MessageRole)
            raise ConfigurationError(f"role must be one of: {allowed}.") from exc
        if not isinstance(self.content, str) or not self.content.strip():
            raise ConfigurationError("Message content must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """A text-generation request that pins the exact model selection."""

    selection: ModelSelection
    messages: tuple[ChatMessage, ...]
    max_output_tokens: int | None = None
    temperature: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.selection, ModelSelection):
            raise ConfigurationError("selection must be a ModelSelection.")
        try:
            messages = tuple(self.messages)
        except TypeError as exc:
            raise ConfigurationError("messages must be an iterable of ChatMessage objects.") from exc
        if not messages or any(not isinstance(message, ChatMessage) for message in messages):
            raise ConfigurationError("messages must contain one or more ChatMessage objects.")
        object.__setattr__(self, "messages", messages)
        if not any(message.role is MessageRole.USER for message in messages):
            raise ConfigurationError("A generation request must contain a user message.")
        if self.max_output_tokens is not None and (
            isinstance(self.max_output_tokens, bool)
            or not isinstance(self.max_output_tokens, int)
            or self.max_output_tokens <= 0
        ):
            raise ConfigurationError("max_output_tokens must be a positive integer or None.")
        if self.temperature is not None and (
            isinstance(self.temperature, bool)
            or not isinstance(self.temperature, (int, float))
            or not 0.0 <= self.temperature <= 2.0
        ):
            raise ConfigurationError("temperature must be between 0.0 and 2.0 or None.")


@dataclass(frozen=True, slots=True)
class GenerationResponse:
    """Normalized text response returned by a provider adapter."""

    provider_id: str
    model_id: str
    output_text: str
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.provider_id, "provider_id")
        _require_identifier(self.model_id, "model_id")
        if not isinstance(self.output_text, str):
            raise ConfigurationError("output_text must be a string.")
        if self.finish_reason is not None and not isinstance(self.finish_reason, str):
            raise ConfigurationError("finish_reason must be a string or None.")
        for field_name in ("input_tokens", "output_tokens"):
            value = getattr(self, field_name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ConfigurationError(f"{field_name} must be a non-negative integer or None.")


def validate_provider_response(
    request: GenerationRequest,
    response: GenerationResponse,
) -> None:
    """Reject provider responses that do not match the explicitly selected model."""

    selected = request.selection
    if (response.provider_id, response.model_id) != (selected.provider_id, selected.model_id):
        raise ProviderResponseMismatchError(
            "Provider returned "
            f"{response.provider_id}/{response.model_id}, but the request selected "
            f"{selected.provider_id}/{selected.model_id}. Silent model substitution is forbidden."
        )
