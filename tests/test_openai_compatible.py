import asyncio
import json

import httpx
import pytest

from agroguardai.errors import (
    ConfigurationError,
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderProtocolError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderRequestMismatchError,
    ProviderResponseMismatchError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from agroguardai.models import (
    ChatMessage,
    GenerationRequest,
    MessageRole,
    ModelSelection,
    Operation,
)
from agroguardai.openai_compatible import OpenAICompatibleAdapter


def run(coroutine):
    return asyncio.run(coroutine)


def make_adapter(handler, **kwargs):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = OpenAICompatibleAdapter(
        provider_id="deepseek",
        base_url="https://api.deepseek.com",
        api_key="test-secret",
        client=client,
        **kwargs,
    )
    return adapter, client


def test_constructor_rejects_remote_http_and_embedded_credentials():
    with pytest.raises(ConfigurationError, match="must use HTTPS"):
        OpenAICompatibleAdapter(
            provider_id="provider",
            base_url="http://api.provider.example",
        )

    with pytest.raises(ConfigurationError, match="embedded credentials"):
        OpenAICompatibleAdapter(
            provider_id="provider",
            base_url="https://user:password@api.provider.example",
        )


def test_constructor_allows_local_http_for_self_hosted_runtime():
    adapter = OpenAICompatibleAdapter(
        provider_id="local",
        base_url="http://localhost:8000/v1",
    )

    assert adapter.provider_id == "local"


def test_constructor_rejects_unsafe_api_paths():
    with pytest.raises(ConfigurationError, match="safe relative API path"):
        OpenAICompatibleAdapter(
            provider_id="provider",
            base_url="https://api.provider.example",
            model_list_path="../secrets",
        )


def test_from_env_requires_named_secret(monkeypatch):
    monkeypatch.delenv("PROVIDER_TEST_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="PROVIDER_TEST_KEY"):
        OpenAICompatibleAdapter.from_env(
            api_key_env="PROVIDER_TEST_KEY",
            provider_id="provider",
            base_url="https://api.provider.example",
        )

    monkeypatch.setenv("PROVIDER_TEST_KEY", "runtime-secret")
    adapter = OpenAICompatibleAdapter.from_env(
        api_key_env="PROVIDER_TEST_KEY",
        provider_id="provider",
        base_url="https://api.provider.example",
    )
    assert adapter.provider_id == "provider"


def test_discovery_reads_deepseek_style_text_model_metadata():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/models"
        assert request.headers["authorization"] == "Bearer test-secret"
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {
                        "id": "deepseek-flash",
                        "name": "DeepSeek V4.1 Flash",
                        "context_window": 1048576,
                        "input_modalities": ["text", "image"],
                        "output_modalities": ["text"],
                    },
                    {
                        "id": "embedding-only",
                        "input_modalities": ["text"],
                        "output_modalities": ["embedding"],
                    },
                    {"id": "unknown-capabilities"},
                ],
            },
        )

    async def scenario():
        adapter, client = make_adapter(handler)
        try:
            models = await adapter.discover_models()
        finally:
            await client.aclose()

        assert len(models) == 1
        assert models[0].model_id == "deepseek-flash"
        assert models[0].display_name == "DeepSeek V4.1 Flash"
        assert models[0].context_window == 1048576
        assert models[0].operations == frozenset({Operation.HOSTED_INFERENCE})

    run(scenario())


def test_discovery_reads_openrouter_style_architecture_metadata():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "qwen/qwen-text",
                        "name": "Qwen Text",
                        "context_length": 32768,
                        "architecture": {
                            "input_modalities": ["text"],
                            "output_modalities": ["text"],
                        },
                    }
                ]
            },
        )

    async def scenario():
        adapter, client = make_adapter(
            handler,
            provider_id_override=None,
        )
        try:
            models = await adapter.discover_models()
        finally:
            await client.aclose()

        assert models[0].model_id == "qwen/qwen-text"
        assert models[0].context_window == 32768

    run(scenario())


def test_discovery_rejects_duplicate_model_ids():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "same-model",
                        "input_modalities": ["text"],
                        "output_modalities": ["text"],
                    },
                    {
                        "id": "same-model",
                        "input_modalities": ["text"],
                        "output_modalities": ["text"],
                    },
                ]
            },
        )

    async def scenario():
        adapter, client = make_adapter(handler)
        try:
            with pytest.raises(ProviderProtocolError, match="duplicate model ID"):
                await adapter.discover_models()
        finally:
            await client.aclose()

    run(scenario())


def test_discovery_rejects_invalid_catalog_shape():
    def handler(request):
        return httpx.Response(200, json={"models": []})

    async def scenario():
        adapter, client = make_adapter(handler)
        try:
            with pytest.raises(ProviderProtocolError, match="invalid model catalog"):
                await adapter.discover_models()
        finally:
            await client.aclose()

    run(scenario())


def test_generate_sends_exact_model_and_normalizes_response():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/chat/completions"
        assert request.headers["authorization"] == "Bearer test-secret"
        body = json.loads(request.content)
        assert body["model"] == "deepseek-flash"
        assert body["stream"] is False
        assert body["max_tokens"] == 256
        assert body["temperature"] == 0.2
        assert body["messages"] == [
            {"role": "system", "content": "Be precise."},
            {"role": "user", "content": "What causes maize leaf blight?"},
        ]
        return httpx.Response(
            200,
            json={
                "model": "deepseek-flash",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Several pathogens can cause it."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 18, "completion_tokens": 9},
            },
        )

    async def scenario():
        adapter, client = make_adapter(handler)
        request = GenerationRequest(
            selection=ModelSelection(
                "deepseek",
                "deepseek-flash",
                Operation.HOSTED_INFERENCE,
            ),
            messages=(
                ChatMessage(MessageRole.SYSTEM, "Be precise."),
                ChatMessage(MessageRole.USER, "What causes maize leaf blight?"),
            ),
            max_output_tokens=256,
            temperature=0.2,
        )
        try:
            response = await adapter.generate(request)
        finally:
            await client.aclose()

        assert response.provider_id == "deepseek"
        assert response.model_id == "deepseek-flash"
        assert response.output_text == "Several pathogens can cause it."
        assert response.input_tokens == 18
        assert response.output_tokens == 9

    run(scenario())


def test_generate_rejects_request_for_another_provider_before_network_call():
    def handler(request):
        pytest.fail("No HTTP request should be sent for a mismatched provider.")

    async def scenario():
        adapter, client = make_adapter(handler)
        request = GenerationRequest(
            selection=ModelSelection("moonshot", "kimi-model", Operation.HOSTED_INFERENCE),
            messages=(ChatMessage(MessageRole.USER, "Hello"),),
        )
        try:
            with pytest.raises(ProviderRequestMismatchError, match="cannot execute"):
                await adapter.generate(request)
        finally:
            await client.aclose()

    run(scenario())


def test_generate_rejects_unsupported_operation_before_network_call():
    def handler(request):
        pytest.fail("No HTTP request should be sent for local inference.")

    async def scenario():
        adapter, client = make_adapter(handler)
        request = GenerationRequest(
            selection=ModelSelection("deepseek", "deepseek-flash", Operation.LOCAL_INFERENCE),
            messages=(ChatMessage(MessageRole.USER, "Hello"),),
        )
        try:
            with pytest.raises(ProviderRequestMismatchError, match="hosted_inference only"):
                await adapter.generate(request)
        finally:
            await client.aclose()

    run(scenario())


def test_generate_rejects_provider_model_substitution():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "model": "different-model",
                "choices": [{"message": {"content": "Unexpected model"}, "finish_reason": "stop"}],
            },
        )

    async def scenario():
        adapter, client = make_adapter(handler)
        request = GenerationRequest(
            selection=ModelSelection("deepseek", "deepseek-flash", Operation.HOSTED_INFERENCE),
            messages=(ChatMessage(MessageRole.USER, "Hello"),),
        )
        try:
            with pytest.raises(ProviderResponseMismatchError, match="Silent model substitution"):
                await adapter.generate(request)
        finally:
            await client.aclose()

    run(scenario())


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (401, ProviderAuthenticationError),
        (403, ProviderAuthenticationError),
        (404, ProviderRequestError),
        (429, ProviderRateLimitError),
        (503, ProviderUnavailableError),
    ],
)
def test_http_status_codes_map_to_typed_errors(status_code, expected_error):
    def handler(request):
        return httpx.Response(status_code, text="Do not expose provider error bodies.")

    async def scenario():
        adapter, client = make_adapter(handler)
        try:
            with pytest.raises(expected_error):
                await adapter.discover_models()
        finally:
            await client.aclose()

    run(scenario())


def test_invalid_json_is_a_protocol_error():
    def handler(request):
        return httpx.Response(200, text="not-json")

    async def scenario():
        adapter, client = make_adapter(handler)
        try:
            with pytest.raises(ProviderProtocolError, match="invalid JSON"):
                await adapter.discover_models()
        finally:
            await client.aclose()

    run(scenario())


def test_timeout_is_reported_without_retry_or_substitution():
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    async def scenario():
        adapter, client = make_adapter(handler)
        try:
            with pytest.raises(ProviderTimeoutError):
                await adapter.discover_models()
        finally:
            await client.aclose()

    run(scenario())


def test_connection_error_is_reported_without_retry_or_substitution():
    def handler(request):
        raise httpx.ConnectError("connection failed", request=request)

    async def scenario():
        adapter, client = make_adapter(handler)
        try:
            with pytest.raises(ProviderConnectionError):
                await adapter.discover_models()
        finally:
            await client.aclose()

    run(scenario())
