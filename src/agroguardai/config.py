"""Safe YAML loading and strict validation for model-selection configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigurationError
from .models import ModelDescriptor, ModelSelection
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


def load_selection_config(path: str | Path) -> SelectionConfig:
    """Load a YAML file with SafeLoader and validate only its selection policy."""

    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            document = yaml.safe_load(config_file)
    except OSError as exc:
        raise ConfigurationError(f"Unable to read model configuration '{config_path}'.") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in model configuration '{config_path}'.") from exc

    if not isinstance(document, dict):
        raise ConfigurationError("Model configuration must contain a YAML mapping.")
    return selection_config_from_mapping(document)
