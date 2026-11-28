import asyncio
import json

import httpx

from agroguardai import OpenAICompatibleAdapter


def run(coroutine):
    return asyncio.run(coroutine)


def test_moonshot_catalog_can_be_explicitly_treated_as_chat_completions_catalog():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/models"
        assert request.headers["authorization"] == "Bearer moonshot-test-key"
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {
                        "id": "kimi-k3.1-pro",
                        "object": "model",
                        "created": 123,
                        "owned_by": "moonshot",
                        "context_length": 1000000,
                        "supports_image_in": True,
                        "supports_video_in": True,
                        "supports_reasoning": True,
                    }
                ],
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenAICompatibleAdapter(
                provider_id="moonshot",
                base_url="https://api.moonshot.ai/v1",
                api_key="moonshot-test-key",
                catalog_models_support_chat_completions=True,
                client=client,
            )
            models = await adapter.discover_models()

        assert len(models) == 1
        assert models[0].model_id == "kimi-k3.1-pro"
        assert models[0].context_window == 1000000
        assert models[0].input_modalities == frozenset({__import__(
            "agroguardai"
        ).Modality.TEXT})
        assert models[0].output_modalities == frozenset({__import__(
            "agroguardai"
        ).Modality.TEXT})

    run(scenario())


def test_moonshot_catalog_without_explicit_opt_in_is_not_assumed_text_capable():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "kimi-k3.1-pro",
                        "context_length": 1000000,
                        "supports_image_in": True,
                    }
                ]
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenAICompatibleAdapter(
                provider_id="moonshot",
                base_url="https://api.moonshot.ai/v1",
                client=client,
            )
            models = await adapter.discover_models()

        assert models == ()

    run(scenario())


def test_explicit_modality_metadata_overrides_catalog_wide_chat_capability():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "text-model",
                        "input_modalities": ["text"],
                        "output_modalities": ["text"],
                    },
                    {
                        "id": "image-embedding-model",
                        "input_modalities": ["image"],
                        "output_modalities": ["embedding"],
                    },
                ]
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenAICompatibleAdapter(
                provider_id="provider",
                base_url="https://api.provider.example/v1",
                catalog_models_support_chat_completions=True,
                client=client,
            )
            models = await adapter.discover_models()

        assert [model.model_id for model in models] == ["text-model"]

    run(scenario())


def test_moonshot_chat_completion_uses_max_completion_tokens():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/v1/chat/completions"
        body = json.loads(request.content)
        assert body["model"] == "kimi-k3.1-pro"
        assert body["max_completion_tokens"] == 1024
        assert "max_tokens" not in body
        return httpx.Response(
            200,
            json={
                "model": "kimi-k3.1-pro",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "A text response."},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 22, "completion_tokens": 12},
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenAICompatibleAdapter(
                provider_id="moonshot",
                base_url="https://api.moonshot.ai/v1",
                api_key="moonshot-test-key",
                max_output_tokens_field="max_completion_tokens",
                client=client,
            )
            from agroguardai import ChatMessage, GenerationRequest, ModelSelection, Operation

            request = GenerationRequest(
                selection=ModelSelection(
                    provider_id="moonshot",
                    model_id="kimi-k3.1-pro",
                    operation=Operation.HOSTED_INFERENCE,
                ),
                messages=(ChatMessage("user", "Explain crop rotation."),),
                max_output_tokens=1024,
            )
            response = await adapter.generate(request)

        assert response.model_id == "kimi-k3.1-pro"
        assert response.output_text == "A text response."
        assert response.input_tokens == 22
        assert response.output_tokens == 12

    run(scenario())
