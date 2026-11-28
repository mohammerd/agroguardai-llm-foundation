# Model registry and explicit model selection

## Product requirement

AgroGuardAI is model-agnostic. Users choose the exact provider and model for each operation. The system must never silently select a random model, substitute a different provider, or switch models because one is unavailable.

The catalog may include DeepSeek, Qwen, Gemma, Kimi/Moonshot, Llama, OpenAI, Anthropic, and other providers or model families. This is an extensible catalog, not a promise that every model supports every operation or is already integrated.

## Implemented core

The Python package provides:

- `ModelDescriptor` for exact provider/model IDs, advertised operations, input/output modalities, context-window metadata, availability, and upstream terms-review status.
- `ModelSelection` for a required provider, exact model ID, and operation.
- `ModelRegistry` for deterministic registration, listing, and resolution.
- Provider-catalog identity checks so discovered records cannot be registered under a different provider.
- Strict YAML selection loading through `load_selection_config` and PyYAML's `safe_load`.
- An opt-in ordered fallback policy. Fallback is disabled by default; candidates must be explicitly listed and are validated before an executor can use them.
- A shared `ProviderAdapter` protocol and response-identity validation to reject a provider response that names a different model.
- A generic `OpenAICompatibleAdapter` for text-only hosted model discovery and chat completions.

The registry is currently an in-memory metadata catalogue. The generic adapter does not cover every provider-specific feature and does not implement local inference, fine-tuning, streaming, tools, embeddings, or multimodal requests.

## Hosted inference and local model paths

### Hosted inference

A provider hosts the model and exposes it through an API. The user selects the provider and exact model ID; credentials are supplied through environment variables or a secrets manager.

The generic adapter implements a subset of the OpenAI-compatible protocol: model-list discovery and text chat completions. Its documented example configurations are DeepSeek and OpenRouter. These integrations use different API base URL conventions, so the base URL is configured independently for each provider. Provider model IDs are fetched from the catalog, not guessed or hard-coded.

See [Provider Adapters](PROVIDER_ADAPTERS.md) for endpoint references and examples.

### Local inference and fine-tuning

The user selects a model with downloadable weights and a supported runtime. Fine-tuning is allowed only when the model's terms permit the intended use and the runtime supports the architecture. Exporting or redistributing resulting weights is a separate review.

A hosted API model must not appear as locally fine-tunable merely because its provider offers an API.

## Registry metadata

Each catalog entry should declare verified information where available:

- stable provider ID and exact model ID;
- display name;
- supported operations: hosted inference, local inference, fine-tuning, and weight export;
- supported input/output modalities and context limits;
- availability;
- terms status and evidence.

When terms status is `reviewed` or `restricted`, the current `ModelDescriptor` requires an HTTPS `terms_url` and timezone-aware ISO 8601 `terms_reviewed_at`. A bare status flag is rejected. This is an auditable metadata requirement, not legal advice; maintainers must still assess the actual terms and intended use.

Fine-tuning and weight export are rejected unless terms status is reviewed. A model marked restricted is rejected for all operations. Capability declarations must be backed by provider documentation or a local runtime check.

## Selection and fallback rules

1. A request must identify a provider, exact model ID, and operation.
2. Missing model selection is a configuration error. There is no random or implicit default.
3. An unknown provider or model returns a typed error. The registry never searches for a similar model.
4. An unavailable model or unsupported operation returns an error.
5. Fallback is disabled by default. If enabled, the user must supply an ordered list. Every candidate is resolved against the registry before execution. The current package validates that order; it does not yet execute inference or fallback.
6. A provider response must identify the same provider/model pair that was requested. A mismatch raises `ProviderResponseMismatchError`.
7. API keys and private prompts must never be logged.

## Provider adapter contract

A concrete adapter implements `ProviderAdapter`:

- `provider_id`: stable provider name used by configuration;
- `discover_models()`: returns current `ModelDescriptor` records;
- `generate(request)`: executes the explicit `GenerationRequest` and returns a normalized `GenerationResponse`.

The generic OpenAI-compatible adapter registers only models whose model catalog explicitly advertises text input and text output. It sends the exact selected model ID to the provider, returns typed errors, and verifies the provider's returned model ID. The caller must resolve the selection through `ModelRegistry` before calling the adapter.

Adapters must preserve the requested model ID, avoid credential logging, and raise actionable errors instead of switching providers.

## Model suitability is a separate question

Availability and API compatibility do not imply agricultural suitability. Before recommending a model for an AgroGuardAI workflow, evaluate it against the versioned benchmark for the relevant languages and tasks. Track factuality, evidence alignment, unsafe chemical/dosage advice, uncertainty, referral behavior, and language quality. Show results per language rather than hiding weaknesses in one global score.

## Configuration

See [`configs/models.example.yaml`](../configs/models.example.yaml). Values are placeholders, not a verified live catalogue. Never put API credentials in YAML committed to the repository.
