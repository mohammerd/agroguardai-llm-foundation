# Hosted provider adapters

## Current implementation

The package includes a generic OpenAI-compatible hosted adapter. It supports the initial text-only chat-completions contract:

- model discovery through a configurable models-list route returning a JSON object with a data array and model IDs;
- conservative catalog registration: only models that explicitly advertise text input and text output are included;
- chat-completions requests with an exact selected model ID;
- bearer-token authentication from an explicitly supplied key or a named environment variable;
- normalized text, finish reason, and token-usage responses;
- typed errors for authentication, rate limits, timeouts, connection failures, provider HTTP errors, and malformed responses;
- strict response identity checking so a provider cannot silently substitute another model.

The adapter does not implement streaming, tool calls, image/audio/video input, embeddings, local inference, fine-tuning, or weight export. Those capabilities must use separate, tested adapters and operation contracts.

## Verified example endpoints

The following endpoints are documented by their providers and match this adapter's expected routes:

| Provider | API base URL | Model-list route | Chat-completions route |
|---|---|---|---|
| DeepSeek | `https://api.deepseek.com` | `/models` | `/chat/completions` |
| OpenRouter | `https://openrouter.ai/api/v1` | `/models` | `/chat/completions` |

Provider documentation:

- [DeepSeek: model list endpoint](https://api-docs.deepseek.com/api/list-models/)
- [DeepSeek: chat completions](https://api-docs.deepseek.com/api/create-chat-completion/)
- [DeepSeek: model names and API base URLs](https://api-docs.deepseek.com/quick_start/pricing/)
- [OpenRouter: model catalog](https://openrouter.ai/docs/api/api-reference/models/get-models)
- [OpenRouter: make a chat-completions request](https://learn.openrouter.ai/courses/first-request/make-a-request)

This is endpoint documentation, not a claim that AgroGuardAI has tested every model listed by those services. The adapter is provider-agnostic at the protocol level; each configured endpoint still needs an integration test and a capability/terms review before being treated as supported.

## Example: DeepSeek

Set the API key in the runtime environment. Never commit the value.

```bash
export DEEPSEEK_API_KEY="your-key"
```

```python
import asyncio

from agroguardai import (
    ChatMessage,
    GenerationRequest,
    ModelRegistry,
    ModelSelection,
    OpenAICompatibleAdapter,
    Operation,
)


async def main():
    adapter = OpenAICompatibleAdapter.from_env(
        api_key_env="DEEPSEEK_API_KEY",
        provider_id="deepseek",
        base_url="https://api.deepseek.com",
    )

    # Refresh catalog metadata from the provider.
    catalog = await adapter.discover_models()
    registry = ModelRegistry()
    registry.register_provider_catalog(adapter.provider_id, catalog)

    # The application should pass this exact ID from the user's model selector.
    selected_model_id = "deepseek-flash"
    selection = ModelSelection(
        provider_id="deepseek",
        model_id=selected_model_id,
        operation=Operation.HOSTED_INFERENCE,
    )
    registry.resolve(selection)

    request = GenerationRequest(
        selection=selection,
        messages=(
            ChatMessage("user", "What information is needed to diagnose maize leaf blight?"),
        ),
    )
    response = await adapter.generate(request)
    print(response.output_text)


if __name__ == "__main__":
    asyncio.run(main())
```

The example model ID is illustrative; use the exact current ID returned by discovery or selected by the user, and do not assume that a provider alias is immutable.

## Example: OpenRouter

```python
from agroguardai import OpenAICompatibleAdapter

adapter = OpenAICompatibleAdapter.from_env(
    api_key_env="OPENROUTER_API_KEY",
    provider_id="openrouter",
    base_url="https://openrouter.ai/api/v1",
)
```

OpenRouter's model catalog can contain models hosted by many upstream organizations. The adapter's provider identity is still `openrouter`, because that is the API endpoint selected by the user. The upstream model ID remains the exact model ID returned by the catalog.

## Security and behavior guarantees

- Credentials are supplied at runtime and are not written into configs or logged.
- Remote endpoints must use HTTPS. Plain HTTP is permitted only for localhost/loopback self-hosted development.
- Model catalog entries that do not explicitly advertise text input and text output are excluded from this text-only adapter.
- The adapter never chooses a model. The caller must provide a provider and exact model ID.
- The adapter rejects requests naming a different provider.
- The adapter checks that the response's model ID exactly matches the requested model ID.
- HTTP errors, timeouts, connection failures, and malformed responses are surfaced as typed exceptions.
- It does not automatically retry or switch models. Any fallback policy must be explicitly selected and implemented by a higher-level execution component.

## Adding another compatible endpoint

Configure the adapter with the provider's documented base URL and route paths. Confirm that its model list schema and chat-completions response match the adapter contract, add a mocked integration test using the provider's documented response fixtures, and document any provider-specific differences. If the provider requires different request/response semantics, implement a dedicated adapter rather than pretending it is compatible.
