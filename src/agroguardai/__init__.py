"""AgroGuardAI research infrastructure."""

from .config import SelectionConfig, load_selection_config, selection_config_from_mapping
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

__version__ = "0.3.0"

__all__ = [
    "ChatMessage",
    "GenerationRequest",
    "GenerationResponse",
    "Modality",
    "ModelDescriptor",
    "ModelRegistry",
    "ModelSelection",
    "OpenAICompatibleAdapter",
    "Operation",
    "ProviderAdapter",
    "SelectionConfig",
    "TermsStatus",
    "load_selection_config",
    "selection_config_from_mapping",
    "validate_provider_response",
]
