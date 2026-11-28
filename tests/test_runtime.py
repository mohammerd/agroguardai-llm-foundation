import asyncio
import json

import httpx
import pytest

from agroguardai.config import model_runtime_config_from_mapping
from agroguardai.errors import (
    ConfigurationError,
    ProviderIdentityMismatchError,
    ProviderRequestMismatchError,
    ProviderResponseMismatchError,
    UnsupportedOperationError,
    UnknownModelError,
)
from agroguardai.models import (
    ChatMessage,
    GenerationRequest,
    GenerationResponse,
    ModelDescriptor,
    ModelSelection,
    Operation,
)
from agroguardai.runtime import HostedModelRuntime


def run(coroutine):
    return asyncio.run(coroutine)


def runtime_document(
    *,
    model_id="agro-reasoner",
    operation="hosted_inference",
    fallback=None,
):
    selection = {
        "provider": "deepseek",
        "model_id": model_id,
        "operation": operation,
    }
    if fallback is not None:
        selection["fallback"] = fallback
    return {
        "selection": selection,
        "providers": {
            "deepseek": {
                "protocol": "openai-compatible",
                "base_url": "https://api.deepseek.example/v1",
                "api_key_env": "DEEPSEEK_TEST_KEY",
                "discovery": {"endpoint": "models"},
            },
            "moonshot": {
                "protocol": "openai-compatible",
                "base_url": "https://api.moonshot.example/v1",
                "api_key_env": "MOONSHOT_TEST_KEY",
                "discovery": {"endpoint": "models"},
            },
        },
    }


def text_catalog(model_id="agro-reasoner"):
    return {
        "data": [
            {
                "id": model_id,
                "name": "Agro Reasoner",
                "context_window": 65536,
                "input_modalities": ["text"],
                "output_modalities": ["text"],
            }
        ]
    }


def chat_payload(model_id="agro-reasoner", text="Check the symptoms and local context."):
    return {
        "model": model_id,
        "choices": [
            {
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 12},
    }


def request_for(model_id="agro-reasoner", provider_id="deepseek"):
    return GenerationRequest(
        selection=ModelSelection(
            provider_id=provider_id,
            model_id=model_id,
            operation=Operation.HOSTED_INFERENCE,
        ),
        messages=(ChatMessage("user", "How can I inspect maize leaf spots?"),),
    )


def test_runtime_discovers_resolves_and_generates_with_the_configured_model():
    counts = {"models": 0, "completions": 0}

    def handler(request):
        if request.method == "GET":
            counts["models"] += 1
            assert request.url.path == "/v1/models"
            assert request.headers["authorization"] == "Bearer test-deepseek-key"
            return httpx.Response(200, json=text_catalog())

        counts["completions"] += 1
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-deepseek-key"
        body = json.loads(request.content)
        assert body["model"] == "agro-reasoner"
        return httpx.Response(200, json=chat_payload())

    async def scenario():
        config = model_runtime_config_from_mapping(runtime_document())
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            runtime = HostedModelRuntime.from_config(
                config,
                environment={"DEEPSEEK_TEST_KEY": "test-deepseek-key"},
                client=client,
            )
            response = await runtime.generate(request_for())
            assert runtime.selected_provider == "deepseek"
            assert runtime.selected_model == "agro-reasoner"
            assert [item.model_id for item in runtime.catalog] == ["agro-reasoner"]
            return response

    response = run(scenario())

    assert response.provider_id == "deepseek"
    assert response.model_id == "agro-reasoner"
    assert response.output_text == "Check the symptoms and local context."
    assert counts == {"models": 1, "completions": 1}


def test_runtime_reuses_validated_catalog_for_subsequent_requests():
    catalog_calls = 0
    completion_calls = 0

    def handler(request):
        nonlocal catalog_calls, completion_calls
        if request.method == "GET":
            catalog_calls += 1
            return httpx.Response(200, json=text_catalog())
        completion_calls += 1
        return httpx.Response(200, json=chat_payload())

    async def scenario():
        config = model_runtime_config_from_mapping(runtime_document())
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            runtime = HostedModelRuntime.from_config(
                config,
                environment={"DEEPSEEK_TEST_KEY": "test-key"},
                client=client,
            )
            await runtime.generate(request_for())
            await runtime.generate(request_for())

    run(scenario())

    assert catalog_calls == 1
    assert completion_calls == 2


def test_runtime_rejects_request_for_a_different_model_before_network_call():
    def handler(request):
        pytest.fail("A mismatched model request must not reach the provider.")

    async def scenario():
        config = model_runtime_config_from_mapping(runtime_document())
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            runtime = HostedModelRuntime.from_config(
                config,
                environment={"DEEPSEEK_TEST_KEY": "test-key"},
                client=client,
            )
            with pytest.raises(ProviderRequestMismatchError, match="exact provider, model"):
                await runtime.generate(request_for(model_id="another-model"))

    run(scenario())


def test_runtime_rejects_selected_model_missing_from_provider_catalog():
    def handler(request):
        return httpx.Response(200, json=text_catalog(model_id="different-model"))

    async def scenario():
        config = model_runtime_config_from_mapping(runtime_document())
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            runtime = HostedModelRuntime.from_config(
                config,
                environment={"DEEPSEEK_TEST_KEY": "test-key"},
                client=client,
            )
            with pytest.raises(UnknownModelError, match="No substitute"):
                await runtime.generate(request_for())

    run(scenario())


def test_runtime_rejects_provider_response_that_names_another_model():
    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json=text_catalog())
        return httpx.Response(200, json=chat_payload(model_id="substituted-model"))

    async def scenario():
        config = model_runtime_config_from_mapping(runtime_document())
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            runtime = HostedModelRuntime.from_config(
                config,
                environment={"DEEPSEEK_TEST_KEY": "test-key"},
                client=client,
            )
            with pytest.raises(ProviderResponseMismatchError, match="Silent model substitution"):
                await runtime.generate(request_for())

    run(scenario())


def test_runtime_does_not_execute_fallback_even_if_explicitly_configured():
    config = model_runtime_config_from_mapping(
        runtime_document(
            fallback={
                "enabled": True,
                "ordered_candidates": [
                    {"provider": "moonshot", "model_id": "kimi-model"}
                ],
            }
        )
    )

    with pytest.raises(ConfigurationError, match="does not execute fallback yet"):
        HostedModelRuntime.from_config(
            config,
            environment={
                "DEEPSEEK_TEST_KEY": "test-key",
                "MOONSHOT_TEST_KEY": "moonshot-key",
            },
        )


def test_runtime_rejects_local_inference_operation():
    config = model_runtime_config_from_mapping(
        runtime_document(operation="local_inference")
    )

    with pytest.raises(UnsupportedOperationError, match="hosted_inference only"):
        HostedModelRuntime.from_config(
            config,
            environment={"DEEPSEEK_TEST_KEY": "test-key"},
        )


class WrongProviderAdapter:
    provider_id = "moonshot"

    async def discover_models(self):
        return ()

    async def generate(self, request):
        return GenerationResponse(
            provider_id="moonshot",
            model_id="kimi-model",
            output_text="This must not be returned.",
        )


def test_runtime_rejects_adapter_for_a_different_provider():
    config = model_runtime_config_from_mapping(runtime_document())

    with pytest.raises(ProviderRequestMismatchError, match="does not match adapter"):
        HostedModelRuntime(config, WrongProviderAdapter())


def test_catalog_refresh_does_not_replace_previous_snapshot_on_identity_failure():
    class MutableCatalogAdapter:
        provider_id = "deepseek"

        def __init__(self):
            self.calls = 0

        async def discover_models(self):
            self.calls += 1
            provider_id = "deepseek" if self.calls == 1 else "moonshot"
            return (
                ModelDescriptor(
                    provider_id=provider_id,
                    model_id="agro-reasoner",
                    display_name="Agro Reasoner",
                    operations=frozenset({Operation.HOSTED_INFERENCE}),
                ),
            )

        async def generate(self, request):
            return GenerationResponse(
                provider_id="deepseek",
                model_id="agro-reasoner",
                output_text="OK",
            )

    async def scenario():
        config = model_runtime_config_from_mapping(runtime_document())
        adapter = MutableCatalogAdapter()
        runtime = HostedModelRuntime(config, adapter)
        original = await runtime.refresh_catalog()

        with pytest.raises(ProviderIdentityMismatchError):
            await runtime.refresh_catalog()

        assert runtime.catalog == original

    run(scenario())
