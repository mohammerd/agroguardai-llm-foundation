"""Safe YAML loading and runtime construction for model selection and providers."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import httpx
import yaml

from .errors import ConfigurationError
from .models import ModelDescriptor, ModelSelection
from .openai_compatible import OpenAICompatibleAdapter
from .registry import ModelRegistry


@dataclass(frozen=True, slots=True)
class FallbackModel:
    """One explicitly ordered fallback candidate for the same operation."""

    provider_id: str
    model_id: str

    def __post_init__(self) -> None:
        for field_name in ("provider_id", "model_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ConfigurationError(f"Fallback {field_name} must be a non-empty string.")
            if value != value.strip() or any(character.isspace() for character in value):
                raise ConfigurationError(
                    f"Fallback {field_name} must not contain whitespace."
                )


@dataclass(frozen=True, slots=True)
class SelectionConfig:
    """Validated primary selection and an opt-in ordered fallback policy."""

    primary: ModelSelection
    fallback_enabled: bool = False
    ordered_fallbacks: tuple[FallbackModel, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.primary, ModelSelection):
            raise ConfigurationError("selection.primary must be a ModelSelection.")
        if not isinstance(self.fallback_enabled, bool):
            raise ConfigurationError("fallback.enabled must be a boolean.")
        fallbacks = tuple(self.ordered_fallbacks)
        if any(not isinstance(item, FallbackModel) for item in fallbacks):
            raise ConfigurationError("ordered_fallbacks must contain FallbackModel entries.")
        object.__setattr__(self, "ordered_fallbacks", fallbacks)

        if not self.fallback_enabled and fallbacks:
            raise ConfigurationError(
                "Fallback candidates were provided while fallback is disabled. "
                "Remove them or explicitly set fallback.enabled to true."
            )
        if self.fallback_enabled and not fallbacks:
            raise ConfigurationError(
                "Fallback is enabled but ordered_candidates is empty. "
                "Provide an explicit ordered list or disable fallback."
            )
        keys = [(item.provider_id, item.model_id) for item in fallbacks]
        primary_key = (self.primary.provider_id, self.primary.model_id)
        if primary_key in keys or len(keys) != len(set(keys)):
            raise ConfigurationError(
                "Fallback candidates must be unique and cannot repeat the primary model."
            )

    def resolve_candidates(self, registry: ModelRegistry) -> tuple[ModelDescriptor, ...]:
        """Validate the explicit candidate order before execution.

        This method does not execute candidates or perform fallback. A future
        execution layer may use the returned order only when the user enabled it.
        """

        selections = [self.primary]
        if self.fallback_enabled:
            selections.extend(
                ModelSelection(
                    provider_id=item.provider_id,
                    model_id=item.model_id,
                    operation=self.primary.operation,
                )
                for item in self.ordered_fallbacks
            )
        return tuple(registry.resolve(selection) for selection in selections)


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Provider identity, protocol, and non-secret configuration values."""

    provider_id: str
    protocol: str
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.provider_id, str)
            or not self.provider_id.strip()
            or self.provider_id != self.provider_id.strip()
            or any(character.isspace() for character in self.provider_id)
        ):
            raise ConfigurationError("Provider IDs must be non-empty identifiers without spaces.")
        if not isinstance(self.protocol, str) or not self.protocol.strip():
            raise ConfigurationError(
                f"Provider '{self.provider_id}' must define a non-empty protocol."
            )
        if not isinstance(self.values, Mapping):
            raise ConfigurationError(f"Provider '{self.provider_id}' settings must be a mapping.")
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


@dataclass(frozen=True, slots=True)
class ModelRuntimeConfig:
    """Complete selection plus provider configuration for one runtime."""

    selection: SelectionConfig
    providers: Mapping[str, ProviderConfig]

    def __post_init__(self) -> None:
        if not isinstance(self.selection, SelectionConfig):
            raise ConfigurationError("selection must be a SelectionConfig.")
        if not isinstance(self.providers, Mapping):
            raise ConfigurationError("providers must be a mapping.")

        providers = dict(self.providers)
        for provider_id, provider in providers.items():
            if not isinstance(provider, ProviderConfig) or provider.provider_id != provider_id:
                raise ConfigurationError(
                    f"Provider entry '{provider_id}' must contain matching ProviderConfig data."
                )

        required_provider_ids = {self.selection.primary.provider_id}
        if self.selection.fallback_enabled:
            required_provider_ids.update(
                candidate.provider_id for candidate in self.selection.ordered_fallbacks
            )
        missing = required_provider_ids - providers.keys()
        if missing:
            raise ConfigurationError(
                f"No provider configuration exists for selected provider(s): {sorted(missing)}."
            )

        object.__setattr__(self, "providers", MappingProxyType(providers))


def _expect_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"'{field_name}' must be a YAML mapping.")
    if any(not isinstance(key, str) for key in value):
        raise ConfigurationError(f"'{field_name}' field names must be strings.")
    return value


def _reject_unknown_keys(values: dict[str, Any], allowed: set[str], field_name: str) -> None:
    unknown = set(values) - allowed
    if unknown:
        raise ConfigurationError(f"Unknown fields in '{field_name}': {sorted(unknown)}.")


def selection_config_from_mapping(document: dict[str, Any]) -> SelectionConfig:
    """Validate the selection portion of an already parsed YAML document."""

    root = _expect_mapping(document, "document")
    _reject_unknown_keys(root, {"selection", "providers"}, "document")
    if "selection" not in root:
        raise ConfigurationError("Configuration is missing the required 'selection' section.")
    if "providers" in root:
        _expect_mapping(root["providers"], "providers")

    selection_values = _expect_mapping(root["selection"], "selection")
    _reject_unknown_keys(
        selection_values,
        {"provider", "model_id", "operation", "fallback"},
        "selection",
    )
    primary_values = {
        key: selection_values[key]
        for key in ("provider", "model_id", "operation")
        if key in selection_values
    }
    primary = ModelSelection.from_mapping(primary_values)

    fallback_values = selection_values.get("fallback", {"enabled": False, "ordered_candidates": []})
    fallback_values = _expect_mapping(fallback_values, "selection.fallback")
    _reject_unknown_keys(fallback_values, {"enabled", "ordered_candidates"}, "selection.fallback")

    enabled = fallback_values.get("enabled", False)
    candidates_values = fallback_values.get("ordered_candidates", [])
    if not isinstance(candidates_values, list):
        raise ConfigurationError("selection.fallback.ordered_candidates must be a list.")

    candidates: list[FallbackModel] = []
    for index, candidate in enumerate(candidates_values):
        candidate_values = _expect_mapping(
            candidate,
            f"selection.fallback.ordered_candidates[{index}]",
        )
        _reject_unknown_keys(candidate_values, {"provider", "model_id"}, "fallback candidate")
        missing = {"provider", "model_id"} - candidate_values.keys()
        if missing:
            raise ConfigurationError(
                f"Fallback candidate {index} is missing fields: {sorted(missing)}."
            )
        candidates.append(
            FallbackModel(
                provider_id=candidate_values["provider"],
                model_id=candidate_values["model_id"],
            )
        )

    return SelectionConfig(
        primary=primary,
        fallback_enabled=enabled,
        ordered_fallbacks=tuple(candidates),
    )


def model_runtime_config_from_mapping(document: dict[str, Any]) -> ModelRuntimeConfig:
    """Parse model selection and provider definitions without reading secrets."""

    root = _expect_mapping(document, "document")
    _reject_unknown_keys(root, {"selection", "providers"}, "document")
    selection = selection_config_from_mapping(root)

    provider_values = _expect_mapping(root.get("providers", {}), "providers")
    providers: dict[str, ProviderConfig] = {}
    for provider_id, raw_values in provider_values.items():
        values = _expect_mapping(raw_values, f"providers.{provider_id}")
        protocol = values.get("protocol")
        if not isinstance(protocol, str) or not protocol.strip():
            raise ConfigurationError(
                f"Provider '{provider_id}' must define a non-empty protocol."
            )
        settings = {key: value for key, value in values.items() if key != "protocol"}
        providers[provider_id] = ProviderConfig(
            provider_id=provider_id,
            protocol=protocol,
            values=settings,
        )

    return ModelRuntimeConfig(selection=selection, providers=providers)


def build_selected_adapter(
    config: ModelRuntimeConfig,
    *,
    environment: Mapping[str, str] | None = None,
    client: httpx.AsyncClient | None = None,
) -> OpenAICompatibleAdapter:
    """Construct only the selected provider adapter from validated configuration.

    Secrets are resolved from the supplied environment mapping (or the process
    environment by default). Values are never loaded from YAML or logged.
    The first implementation supports the OpenAI-compatible hosted protocol.
    """

    if not isinstance(config, ModelRuntimeConfig):
        raise ConfigurationError("config must be a ModelRuntimeConfig.")

    provider_id = config.selection.primary.provider_id
    provider = config.providers.get(provider_id)
    if provider is None:
        raise ConfigurationError(f"No configuration exists for selected provider '{provider_id}'.")
    if provider.protocol != "openai-compatible":
        raise ConfigurationError(
            f"Provider '{provider_id}' uses unsupported protocol '{provider.protocol}'. "
            "This runtime currently supports 'openai-compatible' providers only."
        )

    values = dict(provider.values)
    _reject_unknown_keys(
        values,
        {"base_url", "api_key_env", "timeout", "chat_completions_path", "discovery"},
        f"providers.{provider_id}",
    )

    base_url = values.get("base_url")
    if not isinstance(base_url, str) or not base_url.strip():
        raise ConfigurationError(f"Provider '{provider_id}' must define an absolute base_url.")

    api_key_env = values.get("api_key_env")
    api_key: str | None = None
    env = os.environ if environment is None else environment
    if api_key_env is not None:
        if (
            not isinstance(api_key_env, str)
            or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", api_key_env)
        ):
            raise ConfigurationError(
                f"Provider '{provider_id}' api_key_env must be a valid environment variable name."
            )
        api_key = env.get(api_key_env)
        if not isinstance(api_key, str) or not api_key.strip():
            raise ConfigurationError(
                f"Required provider credential environment variable '{api_key_env}' is not set."
            )

    discovery = _expect_mapping(values.get("discovery", {}), f"providers.{provider_id}.discovery")
    _reject_unknown_keys(
        discovery,
        {"endpoint", "default_input_modalities", "default_output_modalities"},
        f"providers.{provider_id}.discovery",
    )
    model_list_path = discovery.get("endpoint", "models")
    chat_completions_path = values.get("chat_completions_path", "chat/completions")

    return OpenAICompatibleAdapter(
        provider_id=provider_id,
        base_url=base_url,
        api_key=api_key,
        timeout=values.get("timeout", 30.0),
        model_list_path=model_list_path,
        chat_completions_path=chat_completions_path,
        catalog_default_input_modalities=discovery.get("default_input_modalities"),
        catalog_default_output_modalities=discovery.get("default_output_modalities"),
        client=client,
    )


def _load_yaml_document(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            document = yaml.safe_load(config_file)
    except OSError as exc:
        raise ConfigurationError(f"Unable to read model configuration '{config_path}'.") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in model configuration '{config_path}'.") from exc

    return _expect_mapping(document, "document")


def load_selection_config(path: str | Path) -> SelectionConfig:
    """Load a YAML file and validate only its model-selection policy."""

    return selection_config_from_mapping(_load_yaml_document(path))


def load_model_config(path: str | Path) -> ModelRuntimeConfig:
    """Load the complete model-selection and provider configuration."""

    return model_runtime_config_from_mapping(_load_yaml_document(path))
