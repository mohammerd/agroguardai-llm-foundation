import pytest

from agroguardai.errors import (
    ConfigurationError,
    ProviderResponseMismatchError,
)
from agroguardai.models import (
    ChatMessage,
    GenerationRequest,
    GenerationResponse,
    MessageRole,
    ModelSelection,
    Operation,
    validate_provider_response,
)
from agroguardai.providers import ProviderAdapter


class ExampleAdapter:
    provider_id = "example"

    async def discover_models(self):
        return ()

    async def generate(self, request):
        return GenerationResponse(
            provider_id=request.selection.provider_id,
            model_id=request.selection.model_id,
            output_text="Example response",
        )


def make_request() -> GenerationRequest:
    return GenerationRequest(
        selection=ModelSelection("example", "example-model", Operation.HOSTED_INFERENCE),
        messages=(ChatMessage(MessageRole.USER, "How do I identify leaf blight?"),),
    )


def test_provider_adapter_protocol_is_structural():
    assert isinstance(ExampleAdapter(), ProviderAdapter)


def test_generation_request_requires_a_user_message():
    with pytest.raises(ConfigurationError, match="user message"):
        GenerationRequest(
            selection=ModelSelection("example", "example-model", Operation.HOSTED_INFERENCE),
            messages=(ChatMessage(MessageRole.SYSTEM, "Be concise."),),
        )


def test_generation_request_rejects_invalid_temperature():
    with pytest.raises(ConfigurationError, match="temperature"):
        GenerationRequest(
            selection=ModelSelection("example", "example-model", Operation.HOSTED_INFERENCE),
            messages=(ChatMessage(MessageRole.USER, "Hello"),),
            temperature=2.5,
        )


def test_exact_model_response_is_accepted():
    request = make_request()
    response = GenerationResponse(
        provider_id="example",
        model_id="example-model",
        output_text="Check the leaf symptoms and consult local extension guidance.",
    )

    validate_provider_response(request, response)


def test_provider_cannot_silently_return_another_model():
    request = make_request()
    response = GenerationResponse(
        provider_id="other-provider",
        model_id="other-model",
        output_text="A substituted response",
    )

    with pytest.raises(ProviderResponseMismatchError, match="Silent model substitution"):
        validate_provider_response(request, response)
