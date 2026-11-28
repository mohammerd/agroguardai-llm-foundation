"""AgroGuardAI research infrastructure."""

from .config import SelectionConfig, load_selection_config, selection_config_from_mapping
from .models import (
    ChatMessage,
    GenerationRequest,
    GenerationResponse,
    ModelDescriptor,
    ModelSelection,
    Modality,
    Operation,
    TermsStatus,
    validate_provider_response,
)
from .providers import ProviderAdapter
from .registry import ModelRegistry

__version__ = "0.2.0"

__all__ = [
    "ChatMessage",
    "GenerationRequest",
    "GenerationResponse",
    "ModelDescriptor",
    "ModelRegistry",
    "ModelSelection",
    "Modality",
    "Operation",
    "ProviderAdapter",
    "SelectionConfig",
    "TermsStatus",
    "load_selection_config",
    "selection_config_from_mapping",
    "validate_provider_response",
]
