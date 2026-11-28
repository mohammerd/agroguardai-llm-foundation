# Model registry and explicit model selection

## Product requirement

AgroGuardAI is model-agnostic. Users choose the exact provider and model for each operation. The system must never silently select a random model, substitute a different provider, or switch models because one is unavailable.

The catalog may include DeepSeek, Qwen, Gemma, Kimi/Moonshot, Llama, and other providers or model families. This is an extensible catalog, not a promise that every model supports every operation or is already integrated.

## Implemented core

The Python package provides:

- `ModelDescriptor` for exact provider/model IDs, advertised operations, input/output modalities, context-window metadata, availability, and upstream terms-review status.
- `ModelSelection` for a required provider, exact model ID, and operation.
- `ModelRegistry` for deterministic registration, listing, and resolution.
- Provider-catalog identity checks so discovered records cannot be registered under a different provider.
- Strict YAML selection loading through `load_selection_config` and PyYAML's `safe_load`.
- An opt-in ordered fallback policy. Fallback is disabled by default; candidates must be explicitly listed and are validated before an executor can use them.
- A shared `ProviderAdapter` protocol and response-identity validation to reject a provider response that names a different model.

The registry is currently an in-memory metadata catalogue. There are no concrete hosted API or local-runtime adapters yet, and it does not perform model discovery or inference itself.

## Two different model paths

### Hosted inference

A provider hosts the model and exposes it through an API. The user selects the provider and exact model ID; credentials are supplied through server-side environment variables or a secrets manager.

A provider may expose an OpenAI-compatible interface, but compatibility must be verified per endpoint and capability. A common request format does not guarantee identical tool calling, multimodal support, error behavior, rate limits, or model semantics.

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

Additional discovery metadata such as immutable model revision, provider endpoint, model family, catalog timestamp, and reviewer/process record should be recorded by concrete provider integrations as they are implemented. Unknown properties remain unknown; do not invent capabilities or license permissions.

Fine-tuning and weight export are rejected unless terms status is reviewed. A model marked restricted is rejected for all operations. Capability declarations must be backed by provider documentation or a local runtime check.

## Selection and fallback rules

1. A request must identify a provider, exact model ID, and operation.
2. Missing model selection is a configuration error. There is no random or implicit default.
3. An unknown provider or model returns a typed error. The registry never searches for a "similar" model.
4. An unavailable model or unsupported operation returns an error.
5. Fallback is disabled by default. If enabled, the user must supply an ordered list. Every candidate is resolved against the registry before execution. The current package validates that order; it does not yet execute inference or fallback.
6. A provider response must identify the same provider/model pair that was requested. A mismatch raises `ProviderResponseMismatchError`.
7. API keys and private prompts must never be logged.

## Provider adapter contract

A concrete adapter implements `ProviderAdapter`:

- `provider_id`: stable provider name used by configuration;
- `discover_models()`: returns current `ModelDescriptor` records;
- `generate(request)`: executes the explicit `GenerationRequest` and returns a normalized `GenerationResponse`.

Adapters must report the model actually used, preserve the requested model ID, avoid credential logging, and raise actionable errors instead of switching providers. The execution layer must call `validate_provider_response` before returning output to a caller.

## Model suitability is a separate question

Availability and API compatibility do not imply agricultural suitability. Before recommending a model for an AgroGuardAI workflow, evaluate it against the versioned benchmark for the relevant languages and tasks. Track factuality, evidence alignment, unsafe chemical/dosage advice, uncertainty, referral behavior, and language quality. Show results per language rather than hiding weaknesses in one global score.

## Configuration

See [`configs/models.example.yaml`](../configs/models.example.yaml). Values are placeholders, not a verified live catalogue. Never put API credentials in YAML committed to the repository.
