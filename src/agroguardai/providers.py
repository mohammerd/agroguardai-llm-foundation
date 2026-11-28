"""Provider adapter contracts shared by hosted and local model integrations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from .models import GenerationRequest, GenerationResponse, ModelDescriptor


@runtime_checkable
class ProviderAdapter(Protocol):
    """Structural interface required of every concrete provider adapter.

    Implementations must preserve the exact requested model identifier, keep
    credentials out of logs, and raise typed/authentication/rate-limit errors
    instead of switching to another provider or model.
    """

    @property
    def provider_id(self) -> str:
        """Return the stable provider identifier used in configuration."""

    async def discover_models(self) -> Sequence[ModelDescriptor]:
        """Return current metadata for models the provider makes available."""

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Run the explicitly selected model and return normalized text output."""
