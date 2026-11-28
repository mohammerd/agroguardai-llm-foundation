"""AgroGuardAI research infrastructure."""

from .config import (
    ModelRuntimeConfig,
    ProviderConfig,
    SelectionConfig,
    build_selected_adapter,
    load_model_config,
    load_selection_config,
    model_runtime_config_from_mapping,
    selection_config_from_mapping,
)
from .models import (
    ChatMessage,
    GenerationRequest,
    GenerationResponse,
    Modality,
    ModelDescriptor,
    ModelSelection,
    Operation,
    TermsStatus,
    validate_provider_response,
)
from .openai_compatible import OpenAICompatibleAdapter
from .providers import ProviderAdapter
from .registry import ModelRegistry
from .runtime import HostedModelRuntime

__version__ = "0.5.0"

__all__ = [
    "ChatMessage",
    "GenerationRequest",
    "GenerationResponse",
    "HostedModelRuntime",
    "Modality",
    "ModelDescriptor",
    "ModelRegistry",
    "ModelRuntimeConfig",
    "ModelSelection",
    "OpenAICompatibleAdapter",
    "Operation",
    "ProviderAdapter",
    "ProviderConfig",
    "SelectionConfig",
    "TermsStatus",
    "build_selected_adapter",
    "load_model_config",
    "load_selection_config",
    "model_runtime_config_from_mapping",
    "selection_config_from_mapping",
    "validate_provider_response",
]
