# Hosted provider adapters

## Current implementation

The package includes a generic OpenAI-compatible hosted adapter. It supports the initial text-only chat-completions contract:

- model discovery through a configurable models-list route returning a JSON object with a data array and model IDs;
- conservative catalog registration: only models that explicitly advertise text input and text output are included;
- optional provider-specific default modality metadata for APIs whose documented model catalog omits modality arrays;
- chat-completions requests with an exact selected model ID;
- bearer-token authentication from an explicitly supplied key or a named environment variable;
- normalized text, finish reason, and token-usage responses;
- typed errors for authentication, rate limits, timeouts, connection failures, provider HTTP errors, and malformed responses;
- strict response identity checking so a provider cannot silently substitute another model.

The adapter does not implement streaming, tool calls, image/audio/video input, embeddings, local inference, fine-tuning, or weight export. Those capabilities must use separate, tested adapters and operation contracts.

## Configuration-driven construction

Provider configuration can be loaded from YAML and the selected provider adapter can be constructed without hard-coding its endpoint in application code.

Copy `configs/models.example.yaml` to a working config, set the selected provider and exact model ID, then provide that provider's key through the named environment variable:

```bash
export DEEPSEEK_API_KEY="your-key"
```

```python
from agroguardai import HostedModelRuntime, load_model_config

config = load_model_config("configs/models.yaml")
runtime = HostedModelRuntime.from_config(config)
```

The factory builds only the selected provider. It resolves credential values from the process environment (or an explicitly supplied environment mapping for tests), not from YAML. It supports only the `openai-compatible` protocol. A documented but unimplemented protocol such as `transformers` can remain in an unselected provider profile; selecting it raises a clear unsupported-protocol error. The factory also rejects unknown fields in the selected provider profile.

## Hosted runtime orchestration

`HostedModelRuntime` connects the provider configuration, model registry, and hosted adapter for one selected provider/model:

```python
import asyncio

from agroguardai import (
    ChatMessage,
    GenerationRequest,
    HostedModelRuntime,
    load_model_config,
)


async def main():
    config = load_model_config("configs/models.yaml")
    runtime = HostedModelRuntime.from_config(config)

    request = GenerationRequest(
        selection=config.selection.primary,
        messages=(
            ChatMessage("user", "What are common maize leaf blight symptoms?"),
        ),
    )
    response = await runtime.generate(request)
    print(response.output_text)


if __name__ == "__main__":
    asyncio.run(main())
```

On the first request, the runtime discovers the selected provider's catalog, registers it, and checks the exact configured model and operation. It caches that validated catalog for subsequent requests. Call `await runtime.refresh_catalog()` to explicitly refresh it.

The request must match the provider, exact model ID, and operation selected in the loaded config. The runtime checks the response identity again before returning output. Parallel first requests share one catalog discovery, and a failed refresh does not replace a previously valid catalog snapshot.

The runtime supports one hosted text model per instance. It rejects enabled fallback for now; although fallback configuration is parsed and validated, there is no fallback executor. It also does not apply agricultural safety policies or evidence checks. Applications must not present its raw output as verified agronomic advice.

## Verified example endpoints

The following endpoints are documented by their providers and can be configured with this adapter's expected routes:

| Provider | API base URL | Model-list route | Chat-completions route | Catalog behavior |
|---|---|---|---|---|
| DeepSeek | `https://api.deepseek.com` | `models` | `chat/completions` | Explicit input/output modality arrays |
| OpenRouter | `https://openrouter.ai/api/v1` | `models` | `chat/completions` | Modality arrays under `architecture` |
| Moonshot / Kimi API | `https://api.moonshot.ai/v1` | `models` | `chat/completions` | Catalog exposes context length and feature flags; text defaults must be explicitly configured |

Provider documentation:

- [DeepSeek: model list endpoint](https://api-docs.deepseek.com/api/list-models/)
- [DeepSeek: chat completions](https://api-docs.deepseek.com/api/create-chat-completion/)
- [DeepSeek: model names and API base URLs](https://api-docs.deepseek.com/quick_start/pricing/)
- [OpenRouter: model catalog](https://openrouter.ai/docs/api/api-reference/models/get-models)
- [OpenRouter: make a chat-completions request](https://learn.openrouter.ai/courses/first-request/make-a-request)
- [Kimi API Platform: list models](https://platform.kimi.ai/docs/api/list-models)
- [Kimi API Platform: quickstart and chat-completions compatibility](https://platform.kimi.ai/docs/get-your-api-key)

This is endpoint documentation, not a claim that AgroGuardAI has tested every model listed by those services. Mocked integration tests exercise representative documented response shapes. Live credentials and provider-specific smoke tests remain opt-in and have not been claimed as completed.

## Example: DeepSeek (direct adapter use)

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

    catalog = await adapter.discover_models()
    registry = ModelRegistry()
    registry.register_provider_catalog(adapter.provider_id, catalog)

    # Use the exact ID selected by the user from the refreshed catalog.
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

## Example: OpenRouter (direct adapter use)

```python
from agroguardai import OpenAICompatibleAdapter

adapter = OpenAICompatibleAdapter.from_env(
    api_key_env="OPENROUTER_API_KEY",
    provider_id="openrouter",
    base_url="https://openrouter.ai/api/v1",
)
```

OpenRouter's model catalog can contain models hosted by many upstream organizations. The adapter's provider identity is still `openrouter`, because that is the API endpoint selected by the user. The upstream model ID remains the exact model ID returned by the catalog.

## Example: Moonshot / Kimi API (direct adapter use)

Moonshot's model-list response documents `id`, `context_length`, and feature flags such as `supports_image_in` and `supports_video_in`; it does not use the explicit modality arrays returned by DeepSeek or OpenRouter. The provider-specific defaults below enable only the text modality supported by this adapter. They do not turn on image/video requests.

```bash
export MOONSHOT_API_KEY="your-key"
```

```python
from agroguardai import OpenAICompatibleAdapter

adapter = OpenAICompatibleAdapter.from_env(
    api_key_env="MOONSHOT_API_KEY",
    provider_id="moonshot",
    base_url="https://api.moonshot.ai/v1",
    catalog_default_input_modalities=("text",),
    catalog_default_output_modalities=("text",),
)
```

Use the endpoint and credential pair for the same Kimi/Moonshot account. The example uses the international API endpoint. Model availability and capabilities are returned by the account's model-list endpoint.

## Security and behavior guarantees

- Credentials are supplied at runtime and are not written into configs or logged.
- Remote endpoints must use HTTPS. Plain HTTP is permitted only for localhost/loopback self-hosted development.
- Model catalog entries that do not explicitly advertise text input and text output are excluded by default.
- Provider-specific text modality defaults are opt-in and apply only when a catalog field is omitted; they never override explicit provider metadata.
- The adapter never chooses a model. The caller must provide a provider and exact model ID.
- The adapter rejects requests naming a different provider.
- The adapter checks that the response's model ID exactly matches the requested model ID.
- HTTP errors, timeouts, connection failures, and malformed responses are surfaced as typed exceptions.
- It does not automatically retry or switch models. Any fallback policy must be explicitly selected and implemented by a higher-level execution component.

## Adding another compatible endpoint

Configure the adapter with the provider's documented base URL and route paths. Confirm that its model list schema and chat-completions response match the adapter contract, add a mocked integration test using the provider's documented response fixtures, and document any provider-specific differences. If the provider requires different request/response semantics, implement a dedicated adapter rather than pretending it is compatible.
