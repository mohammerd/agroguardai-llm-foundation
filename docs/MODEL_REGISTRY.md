# Model registry and explicit model selection

## Product requirement

AgroGuardAI must be model-agnostic. Users choose the exact provider and model for each operation. The system must never silently select a random model, substitute a different provider, or switch models because one is unavailable.

The model catalog may include (but is not limited to) DeepSeek, Qwen, Gemma, Kimi/Moonshot, Llama, and other compatible providers and model families. This is an extensible catalog, not a promise that every model supports every operation.

## Two different model paths

### Hosted inference

A provider hosts the model and exposes it through an API. The user selects the provider and exact model ID; credentials are supplied through server-side environment variables or a secrets manager.

Examples include DeepSeek API models and Kimi/Moonshot API models. These may be callable through OpenAI-compatible interfaces, but compatibility must be verified per endpoint and capability.

### Local inference and fine-tuning

The user selects a model with downloadable weights and a supported runtime. Fine-tuning is allowed only when the model's terms permit the intended use and the runtime supports the architecture. Exporting or redistributing resulting weights is a separate license review.

A hosted API model must not appear as locally fine-tunable merely because its provider offers an API.

## Registry metadata

Every catalog entry should declare, where available:

- stable provider ID and exact model ID;
- display name and model family;
- operation support: hosted inference, local inference, fine-tuning, and weight export;
- supported input/output modalities and context limits;
- API protocol or local runtime adapter;
- license/terms URL and a review status;
- capability metadata and last discovery timestamp;
- whether the upstream identifier is immutable or a moving alias.

Unknown properties remain unknown; do not invent capabilities or license permissions.

## Selection rules

1. A request must identify a provider and model ID explicitly.
2. If no model is selected, return a clear configuration error. Do not choose a default at random.
3. If the selected model is unavailable, return an actionable error. Do not silently substitute another model.
4. Fallback is disabled by default. A user may explicitly configure an ordered fallback list, and every fallback candidate must be visible before the task runs.
5. Model selection is recorded in logs and experiment metadata. Never log API keys or private prompts.
6. Reproducible experiments pin local model revisions and record exact provider model IDs. For hosted aliases that can change upstream, record the provider identifier, discovery metadata, and run timestamp.
7. Capability or license checks must block unsupported operations before execution.

## Discovery

Where a provider offers an authenticated or public model-list endpoint, the provider adapter may refresh its catalog from that endpoint. For example, DeepSeek documents a `GET /models` endpoint with model identifiers and capability metadata. Kimi/Moonshot also documents a model-list API. Discovery is provider-specific; it does not imply every provider exposes all metadata.

The application should merge discovered entries with manually registered local/open-weight models. It should show when a catalog entry was last refreshed and allow an administrator to disable a model.

## Agricultural evaluation gate

Availability does not mean suitability. Before a model can be recommended for an AgroGuardAI agricultural workflow, evaluate it against the versioned benchmark for the relevant languages and tasks. Track factuality, evidence alignment, unsafe chemical/dosage advice, uncertainty, referral behavior, language quality, and modality performance. Show results per language rather than hiding weaknesses in one global score.

## Example

See [`configs/models.example.yaml`](../configs/models.example.yaml) for illustrative configurations. The entries are examples, not claims that credentials, terms, or capabilities have already been validated.
