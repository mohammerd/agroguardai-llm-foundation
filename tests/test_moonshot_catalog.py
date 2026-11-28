import asyncio

import httpx
import pytest

from agroguardai.errors import ConfigurationError
from agroguardai.models import Modality, Operation
from agroguardai.openai_compatible import OpenAICompatibleAdapter


def run(coroutine):
    return asyncio.run(coroutine)


def test_moonshot_catalog_uses_only_explicit_provider_defaults_when_fields_are_omitted():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/models"
        return httpx.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {
                        "id": "kimi-k3.1-pro",
                        "object": "model",
                        "owned_by": "moonshot",
                        "context_length": 1048576,
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
                base_url="https://api.moonshot.ai",
                model_list_path="v1/models",
                catalog_default_input_modalities=(Modality.TEXT,),
                catalog_default_output_modalities=("text",),
                client=client,
            )
            models = await adapter.discover_models()

        assert len(models) == 1
        assert models[0].provider_id == "moonshot"
        assert models[0].model_id == "kimi-k3.1-pro"
        assert models[0].context_window == 1048576
        assert models[0].operations == frozenset({Operation.HOSTED_INFERENCE})
        # The adapter exposes only the text capability it currently implements.
        assert models[0].input_modalities == frozenset({Modality.TEXT})
        assert models[0].output_modalities == frozenset({Modality.TEXT})

    run(scenario())


def test_provider_defaults_never_override_explicit_catalog_capabilities():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "non-text-model",
                        "input_modalities": ["image"],
                        "output_modalities": ["text"],
                    },
                    {
                        "id": "text-model",
                        "input_modalities": ["text"],
                        "output_modalities": ["text"],
                    },
                ]
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenAICompatibleAdapter(
                provider_id="moonshot",
                base_url="https://api.moonshot.ai",
                catalog_default_input_modalities=("text",),
                catalog_default_output_modalities=("text",),
                client=client,
            )
            models = await adapter.discover_models()

        assert [model.model_id for model in models] == ["text-model"]

    run(scenario())


@pytest.mark.parametrize(
    "kwargs",
    [
        {"catalog_default_input_modalities": "text"},
        {"catalog_default_output_modalities": ()},
        {"catalog_default_input_modalities": ("telepathy",)},
    ],
)
def test_invalid_provider_catalog_defaults_are_rejected(kwargs):
    with pytest.raises(ConfigurationError):
        OpenAICompatibleAdapter(
            provider_id="moonshot",
            base_url="https://api.moonshot.ai/v1",
            **kwargs,
        )


def test_without_provider_defaults_missing_modality_fields_remain_excluded():
    def handler(request):
        return httpx.Response(200, json={"data": [{"id": "catalog-model"}]})

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = OpenAICompatibleAdapter(
                provider_id="unknown-compatible",
                base_url="https://api.example.test/v1",
                client=client,
            )
            models = await adapter.discover_models()

        assert models == ()

    run(scenario())
