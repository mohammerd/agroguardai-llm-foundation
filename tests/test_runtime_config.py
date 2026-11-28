import asyncio
from pathlib import Path

import httpx
import pytest

from agroguardai.config import (
    build_selected_adapter,
    load_model_config,
    model_runtime_config_from_mapping,
)
from agroguardai.errors import ConfigurationError
from agroguardai.openai_compatible import OpenAICompatibleAdapter


def run(coroutine):
    return asyncio.run(coroutine)


def make_document(provider_id="moonshot", protocol="openai-compatible"):
    return {
        "selection": {
            "provider": provider_id,
            "model_id": "kimi-k3.1-pro",
            "operation": "hosted_inference",
        },
        "providers": {
            provider_id: {
                "protocol": protocol,
                "base_url": "https://api.moonshot.ai/v1",
                "api_key_env": "MOONSHOT_API_KEY",
                "discovery": {
                    "endpoint": "models",
                    "default_input_modalities": ["text"],
                    "default_output_modalities": ["text"],
                },
            }
        },
    }


def test_load_model_config_reads_all_provider_profiles_from_example():
    path = Path(__file__).parents[1] / "configs" / "models.example.yaml"

    config = load_model_config(path)

    assert config.selection.primary.provider_id == "deepseek"
    assert config.providers["deepseek"].protocol == "openai-compatible"
    assert config.providers["moonshot"].protocol == "openai-compatible"
    assert config.providers["openrouter"].protocol == "openai-compatible"
    # The local runtime protocol can be documented without being claimed as integrated.
    assert config.providers["huggingface"].protocol == "transformers"


def test_build_selected_adapter_uses_only_the_selected_provider_and_environment():
    document = {
        "selection": {
            "provider": "deepseek",
            "model_id": "deepseek-flash",
            "operation": "hosted_inference",
        },
        "providers": {
            "deepseek": {
                "protocol": "openai-compatible",
                "base_url": "https://api.deepseek.com",
                "api_key_env": "DEEPSEEK_API_KEY",
                "discovery": {"endpoint": "models"},
            },
            "huggingface": {
                "protocol": "transformers",
                "model_id": "some/local-model",
                "revision": "main",
            },
        },
    }
    config = model_runtime_config_from_mapping(document)

    adapter = build_selected_adapter(
        config,
        environment={"DEEPSEEK_API_KEY": "test-secret"},
    )

    assert isinstance(adapter, OpenAICompatibleAdapter)
    assert adapter.provider_id == "deepseek"


def test_build_selected_moonshot_adapter_loads_endpoint_and_catalog_defaults():
    config = model_runtime_config_from_mapping(make_document())

    def handler(request):
        assert request.method == "GET"
        assert request.url == "https://api.moonshot.ai/v1/models"
        assert request.headers["authorization"] == "Bearer moonshot-secret"
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {
                        "id": "kimi-k3.1-pro",
                        "context_length": 1048576,
                        "supports_image_in": True,
                        "supports_video_in": True,
                    }
                ],
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = build_selected_adapter(
                config,
                environment={"MOONSHOT_API_KEY": "moonshot-secret"},
                client=client,
            )
            return await adapter.discover_models()

    models = run(scenario())

    assert len(models) == 1
    assert models[0].provider_id == "moonshot"
    assert models[0].model_id == "kimi-k3.1-pro"
    assert models[0].context_window == 1048576


def test_selected_provider_requires_its_named_environment_secret():
    config = model_runtime_config_from_mapping(make_document())

    with pytest.raises(ConfigurationError, match="MOONSHOT_API_KEY"):
        build_selected_adapter(config, environment={})


def test_selected_provider_rejects_unimplemented_protocol():
    config = model_runtime_config_from_mapping(make_document(provider_id="hf", protocol="transformers"))

    with pytest.raises(ConfigurationError, match="unsupported protocol 'transformers'"):
        build_selected_adapter(config, environment={})


def test_selected_provider_must_exist_in_provider_catalog():
    document = {
        "selection": {
            "provider": "missing",
            "model_id": "some-model",
            "operation": "hosted_inference",
        },
        "providers": {
            "deepseek": {
                "protocol": "openai-compatible",
                "base_url": "https://api.deepseek.com",
            }
        },
    }

    with pytest.raises(ConfigurationError, match="No provider configuration"):
        model_runtime_config_from_mapping(document)


def test_every_explicit_fallback_provider_must_have_configuration():
    document = {
        "selection": {
            "provider": "deepseek",
            "model_id": "deepseek-flash",
            "operation": "hosted_inference",
            "fallback": {
                "enabled": True,
                "ordered_candidates": [
                    {"provider": "moonshot", "model_id": "kimi-k3.1-pro"}
                ],
            },
        },
        "providers": {
            "deepseek": {
                "protocol": "openai-compatible",
                "base_url": "https://api.deepseek.com",
            }
        },
    }

    with pytest.raises(ConfigurationError, match="moonshot"):
        model_runtime_config_from_mapping(document)


def test_unknown_selected_provider_configuration_fields_are_rejected():
    document = make_document()
    document["providers"]["moonshot"]["silent_fallback"] = True
    config = model_runtime_config_from_mapping(document)

    with pytest.raises(ConfigurationError, match="Unknown fields"):
        build_selected_adapter(config, environment={"MOONSHOT_API_KEY": "test-secret"})


def test_invalid_environment_variable_name_is_rejected():
    document = make_document()
    document["providers"]["moonshot"]["api_key_env"] = "MOONSHOT KEY"
    config = model_runtime_config_from_mapping(document)

    with pytest.raises(ConfigurationError, match="valid environment variable name"):
        build_selected_adapter(config, environment={"MOONSHOT KEY": "test-secret"})


def test_selected_provider_requires_a_base_url():
    document = make_document()
    document["providers"]["moonshot"].pop("base_url")
    config = model_runtime_config_from_mapping(document)

    with pytest.raises(ConfigurationError, match="base_url"):
        build_selected_adapter(config, environment={"MOONSHOT_API_KEY": "test-secret"})


def test_non_mapping_provider_config_is_rejected():
    document = {
        "selection": {
            "provider": "moonshot",
            "model_id": "kimi-k3.1-pro",
            "operation": "hosted_inference",
        },
        "providers": {"moonshot": "not-a-mapping"},
    }

    with pytest.raises(ConfigurationError, match="YAML mapping"):
        model_runtime_config_from_mapping(document)
