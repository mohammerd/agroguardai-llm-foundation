"""Explicit hosted-model orchestration on top of config, registry, and adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

import httpx

from .config import ModelRuntimeConfig, build_selected_adapter
from .errors import ConfigurationError, ProviderRequestMismatchError, UnsupportedOperationError
from .models import (
    GenerationRequest,
    GenerationResponse,
    ModelDescriptor,
    Operation,
    validate_provider_response,
)
from .providers import ProviderAdapter
from .registry import ModelRegistry


class HostedModelRuntime:
    """Orchestrate catalog discovery, exact model validation, and hosted inference.

    The runtime is intentionally single-provider and single-model per instance.
    It never chooses defaults, retries with another model, or executes fallback.
    Explicit fallback execution will require a separate auditable policy.
    """

    def __init__(
        self,
        config: ModelRuntimeConfig,
        adapter: ProviderAdapter,
    ) -> None:
        if not isinstance(config, ModelRuntimeConfig):
            raise ConfigurationError("config must be a ModelRuntimeConfig.")
        if config.selection.fallback_enabled:
            raise ConfigurationError(
                "HostedModelRuntime does not execute fallback yet. Disable fallback or use "
                "a runtime with an explicitly implemented fallback policy."
            )
        selected = config.selection.primary
        if selected.operation is not Operation.HOSTED_INFERENCE:
            raise UnsupportedOperationError(
                "HostedModelRuntime supports hosted_inference only."
            )
        if not isinstance(adapter, ProviderAdapter):
            raise ConfigurationError("adapter must implement the ProviderAdapter protocol.")
        if adapter.provider_id != selected.provider_id:
            raise ProviderRequestMismatchError(
                f"Configured provider '{selected.provider_id}' does not match adapter "
                f"'{adapter.provider_id}'."
            )

        self._config = config
        self._adapter = adapter
        self._registry = ModelRegistry()
        self._catalog: tuple[ModelDescriptor, ...] = ()
        self._catalog_loaded = False
        self._catalog_lock = asyncio.Lock()

    @classmethod
    def from_config(
        cls,
        config: ModelRuntimeConfig,
        *,
        environment: Mapping[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> HostedModelRuntime:
        """Build the selected adapter and runtime from a parsed model config."""

        adapter = build_selected_adapter(config, environment=environment, client=client)
        return cls(config, adapter)

    @property
    def selected_provider(self) -> str:
        """Return the explicitly configured provider ID."""

        return self._config.selection.primary.provider_id

    @property
    def selected_model(self) -> str:
        """Return the exact configured model ID."""

        return self._config.selection.primary.model_id

    @property
    def catalog(self) -> tuple[ModelDescriptor, ...]:
        """Return the last successfully validated catalog snapshot."""

        return self._catalog

    async def refresh_catalog(self) -> tuple[ModelDescriptor, ...]:
        """Refresh the selected provider's catalog and validate the selected model.

        The existing catalog remains intact if discovery or validation fails.
        """

        async with self._catalog_lock:
            discovered = tuple(await self._adapter.discover_models())
            new_registry = ModelRegistry()
            new_registry.register_provider_catalog(self.selected_provider, discovered)
            new_registry.resolve(self._config.selection.primary)

            # Replace the snapshot only after the complete new catalog is valid.
            self._registry = new_registry
            self._catalog = new_registry.list_models(self.selected_provider)
            self._catalog_loaded = True
            return self._catalog

    async def _ensure_catalog(self) -> None:
        if self._catalog_loaded:
            return
        async with self._catalog_lock:
            if self._catalog_loaded:
                return
            discovered = tuple(await self._adapter.discover_models())
            new_registry = ModelRegistry()
            new_registry.register_provider_catalog(self.selected_provider, discovered)
            new_registry.resolve(self._config.selection.primary)
            self._registry = new_registry
            self._catalog = new_registry.list_models(self.selected_provider)
            self._catalog_loaded = True

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Execute only the provider/model named in the loaded runtime configuration."""

        if not isinstance(request, GenerationRequest):
            raise ConfigurationError("request must be a GenerationRequest.")
        if request.selection != self._config.selection.primary:
            raise ProviderRequestMismatchError(
                "Generation request must match the exact provider, model, and operation "
                "selected in the runtime configuration."
            )

        await self._ensure_catalog()
        self._registry.resolve(request.selection)

        response = await self._adapter.generate(request)
        validate_provider_response(request, response)
        return response
