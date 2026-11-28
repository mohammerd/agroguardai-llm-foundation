"""Deterministic registry for provider-published model metadata."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import (
    DuplicateModelError,
    ModelTermsError,
    ModelUnavailableError,
    UnknownModelError,
    UnknownProviderError,
    UnsupportedOperationError,
)
from .models import ModelDescriptor, ModelSelection, Operation, TermsStatus


class ModelRegistry:
    """In-memory registry keyed by the exact provider and model identifiers.

    The registry never chooses a default model and never substitutes another
    provider/model. Catalog data must be registered from a verified provider
    discovery response or an explicitly reviewed local catalog.
    """

    def __init__(self) -> None:
        self._models: dict[tuple[str, str], ModelDescriptor] = {}

    def register(self, descriptor: ModelDescriptor) -> None:
        """Register one descriptor without replacing an existing entry."""

        key = (descriptor.provider_id, descriptor.model_id)
        if key in self._models:
            raise DuplicateModelError(
                f"Model {descriptor.provider_id}/{descriptor.model_id} is already registered."
            )
        self._models[key] = descriptor

    def register_many(self, descriptors: Iterable[ModelDescriptor]) -> None:
        """Register a batch atomically, rejecting duplicates before mutation."""

        batch = list(descriptors)
        keys = [(item.provider_id, item.model_id) for item in batch]
        if len(keys) != len(set(keys)):
            raise DuplicateModelError("The model batch contains duplicate provider/model IDs.")
        existing = set(self._models)
        duplicate_keys = existing.intersection(keys)
        if duplicate_keys:
            provider_id, model_id = sorted(duplicate_keys)[0]
            raise DuplicateModelError(f"Model {provider_id}/{model_id} is already registered.")
        for descriptor in batch:
            self._models[(descriptor.provider_id, descriptor.model_id)] = descriptor

    def list_models(self, provider_id: str | None = None) -> tuple[ModelDescriptor, ...]:
        """Return a stable, sorted snapshot of registered model descriptors."""

        models = self._models.values()
        if provider_id is not None:
            models = (item for item in models if item.provider_id == provider_id)
        return tuple(sorted(models, key=lambda item: (item.provider_id, item.model_id)))

    def resolve(self, selection: ModelSelection) -> ModelDescriptor:
        """Resolve exactly one selected model and enforce advertised capabilities."""

        provider_models = {
            model_id: descriptor
            for (registered_provider, model_id), descriptor in self._models.items()
            if registered_provider == selection.provider_id
        }
        if not provider_models:
            raise UnknownProviderError(
                f"Provider '{selection.provider_id}' has no registered models. "
                "Refresh or register its catalog; no alternative provider will be selected."
            )

        descriptor = provider_models.get(selection.model_id)
        if descriptor is None:
            raise UnknownModelError(
                f"Exact model '{selection.model_id}' is not registered for provider "
                f"'{selection.provider_id}'. No substitute will be selected."
            )
        if not descriptor.available:
            raise ModelUnavailableError(
                f"Model {selection.provider_id}/{selection.model_id} is marked unavailable."
            )
        if selection.operation not in descriptor.operations:
            supported = ", ".join(sorted(item.value for item in descriptor.operations))
            raise UnsupportedOperationError(
                f"Model {selection.provider_id}/{selection.model_id} does not support "
                f"'{selection.operation.value}'. Supported operations: {supported}."
            )
        if descriptor.terms_status is TermsStatus.RESTRICTED:
            raise ModelTermsError(
                f"Model {selection.provider_id}/{selection.model_id} is restricted by its "
                "upstream terms review."
            )
        if (
            selection.operation in {Operation.FINE_TUNING, Operation.WEIGHT_EXPORT}
            and descriptor.terms_status is not TermsStatus.REVIEWED
        ):
            raise ModelTermsError(
                f"Fine-tuning or weight export for {selection.provider_id}/{selection.model_id} "
                "is blocked until its upstream terms have been reviewed."
            )
        return descriptor
