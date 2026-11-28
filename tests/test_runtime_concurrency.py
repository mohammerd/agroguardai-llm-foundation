import asyncio
import json

import httpx

from agroguardai.config import model_runtime_config_from_mapping
from agroguardai.models import ChatMessage, GenerationRequest, ModelSelection, Operation
from agroguardai.runtime import HostedModelRuntime


def runtime_config():
    return model_runtime_config_from_mapping(
        {
            "selection": {
                "provider": "deepseek",
                "model_id": "agro-reasoner",
                "operation": "hosted_inference",
            },
            "providers": {
                "deepseek": {
                    "protocol": "openai-compatible",
                    "base_url": "https://api.deepseek.example/v1",
                    "discovery": {"endpoint": "models"},
                }
            },
        }
    )


def request():
    return GenerationRequest(
        selection=ModelSelection(
            "deepseek",
            "agro-reasoner",
            Operation.HOSTED_INFERENCE,
        ),
        messages=(ChatMessage("user", "How should I inspect this crop?"),),
    )


def test_concurrent_generations_share_one_initial_catalog_discovery():
    counts = {"catalog": 0, "generation": 0}

    def handler(http_request):
        if http_request.method == "GET":
            counts["catalog"] += 1
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "agro-reasoner",
                            "input_modalities": ["text"],
                            "output_modalities": ["text"],
                        }
                    ]
                },
            )

        counts["generation"] += 1
        body = json.loads(http_request.content)
        return httpx.Response(
            200,
            json={
                "model": body["model"],
                "choices": [
                    {"message": {"content": "Inspect symptoms and field conditions."}}
                ],
            },
        )

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            runtime = HostedModelRuntime.from_config(runtime_config(), client=client)
            responses = await asyncio.gather(
                *(runtime.generate(request()) for _ in range(6))
            )

        assert all(response.model_id == "agro-reasoner" for response in responses)

    asyncio.run(scenario())

    assert counts == {"catalog": 1, "generation": 6}
