from pathlib import Path

import pytest

from agroguardai.config import (
    FallbackModel,
    SelectionConfig,
    load_selection_config,
    selection_config_from_mapping,
)
from agroguardai.errors import ConfigurationError
from agroguardai.models import ModelDescriptor, ModelSelection, Operation, TermsStatus
from agroguardai.registry import ModelRegistry


def make_registry() -> ModelRegistry:
    registry = ModelRegistry()
    registry.register_many(
        [
            ModelDescriptor(
                provider_id="primary-provider",
                model_id="primary-model",
                display_name="Primary",
                operations=frozenset({Operation.HOSTED_INFERENCE}),
                terms_status=TermsStatus.REVIEWED,
            ),
            ModelDescriptor(
                provider_id="backup-provider",
                model_id="backup-model",
                display_name="Backup",
                operations=frozenset({Operation.HOSTED_INFERENCE}),
                terms_status=TermsStatus.REVIEWED,
            ),
        ]
    )
    return registry


def test_loads_repository_model_example():
    config_path = Path(__file__).parents[1] / "configs" / "models.example.yaml"

    config = load_selection_config(config_path)

    assert config.primary == ModelSelection(
        provider_id="PROVIDER_ID",
        model_id="EXACT_PROVIDER_MODEL_ID",
        operation=Operation.HOSTED_INFERENCE,
    )
    assert config.fallback_enabled is False
    assert config.ordered_fallbacks == ()


def test_missing_primary_field_is_rejected():
    with pytest.raises(ConfigurationError, match="missing required fields"):
        selection_config_from_mapping(
            {"selection": {"provider": "provider", "operation": "hosted_inference"}}
        )


def test_unknown_selection_field_is_rejected():
    with pytest.raises(ConfigurationError, match="Unknown fields"):
        selection_config_from_mapping(
            {
                "selection": {
                    "provider": "provider",
                    "model_id": "model",
                    "operation": "hosted_inference",
                    "random": True,
                }
            }
        )


def test_fallback_is_disabled_by_default():
    config = selection_config_from_mapping(
        {
            "selection": {
                "provider": "primary-provider",
                "model_id": "primary-model",
                "operation": "hosted_inference",
            }
        }
    )

    assert config.fallback_enabled is False
    assert config.ordered_fallbacks == ()


def test_disabled_fallback_cannot_hide_candidates():
    with pytest.raises(ConfigurationError, match="while fallback is disabled"):
        SelectionConfig(
            primary=ModelSelection("primary-provider", "primary-model", Operation.HOSTED_INFERENCE),
            fallback_enabled=False,
            ordered_fallbacks=(FallbackModel("backup-provider", "backup-model"),),
        )


def test_enabled_fallback_requires_an_explicit_ordered_list():
    with pytest.raises(ConfigurationError, match="ordered_candidates is empty"):
        SelectionConfig(
            primary=ModelSelection("primary-provider", "primary-model", Operation.HOSTED_INFERENCE),
            fallback_enabled=True,
        )


def test_explicit_fallback_order_is_preserved_and_resolved():
    config = selection_config_from_mapping(
        {
            "selection": {
                "provider": "primary-provider",
                "model_id": "primary-model",
                "operation": "hosted_inference",
                "fallback": {
                    "enabled": True,
                    "ordered_candidates": [
                        {"provider": "backup-provider", "model_id": "backup-model"}
                    ],
                },
            }
        }
    )

    resolved = config.resolve_candidates(make_registry())

    assert [(item.provider_id, item.model_id) for item in resolved] == [
        ("primary-provider", "primary-model"),
        ("backup-provider", "backup-model"),
    ]


def test_fallback_candidates_must_be_unique_and_not_repeat_primary():
    primary = ModelSelection("primary-provider", "primary-model", Operation.HOSTED_INFERENCE)

    with pytest.raises(ConfigurationError, match="unique"):
        SelectionConfig(
            primary=primary,
            fallback_enabled=True,
            ordered_fallbacks=(
                FallbackModel("backup-provider", "backup-model"),
                FallbackModel("backup-provider", "backup-model"),
            ),
        )


def test_invalid_yaml_is_reported_as_configuration_error(tmp_path):
    config_path = tmp_path / "broken.yaml"
    config_path.write_text("selection: [broken", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        load_selection_config(config_path)


def test_missing_config_file_is_reported_as_configuration_error(tmp_path):
    with pytest.raises(ConfigurationError, match="Unable to read"):
        load_selection_config(tmp_path / "missing.yaml")
