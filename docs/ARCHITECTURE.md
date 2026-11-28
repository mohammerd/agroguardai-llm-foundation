# System architecture

## Design goal

Build a modular agricultural AI research platform that lets users select the exact model/provider while AgroGuardAI supplies domain-specific data governance, evaluation, safety controls, and reproducible experiment tooling.

The architecture must not depend on one model vendor or hide model substitution.

## Logical components

1. **Model registry** — stores exact provider/model identifiers, supported operations, modality capabilities, availability, and terms-review status. The in-memory registry and core model contracts are implemented.
2. **Provider configuration** — loads provider endpoints and protocol settings from YAML while resolving credential values only from named environment variables. The configuration parser and selected-adapter factory are implemented for the OpenAI-compatible hosted protocol.
3. **Provider adapters** — translate a common internal request into each provider's API or local-runtime interface. A shared async protocol and a generic OpenAI-compatible hosted text adapter are implemented. Provider-specific differences require their own tested adapters.
4. **Hosted runtime** — connects configuration, catalog discovery, exact registry resolution, adapter generation, and response-identity checks for one configured hosted model. This single-provider text runtime is implemented; multi-provider fallback orchestration and local runtime execution are not.
5. **Data pipeline** — validates schemas, tracks provenance and consent/rights, preserves annotation statuses, detects duplicates, and creates leakage-resistant versioned splits. This layer is not yet implemented.
6. **Agricultural safety layer** — checks task-specific constraints, evidence requirements, uncertainty, and referral conditions. It must fail safely when required information is missing. This layer is not yet implemented.
7. **Evaluation layer** — evaluates each language and task independently, records exact experiment manifests, and generates reports. Documentation and templates exist; executable benchmark tooling is still planned.
8. **Release layer** — packages software, dataset releases, and model artifacts separately with their own version, license, provenance, and documentation. Release governance is documented; model/dataset releases do not yet exist.

## Request flow

```text
User selects provider + exact model ID
                |
                v
       Load selected provider config
                |
                v
       Build selected provider adapter
                |
                v
       Hosted runtime refreshes catalog
                |
                v
       Exact model registry resolution
                |
       capability / terms checks
                |
                v
       Send explicit generation request
                |
                v
       Response identity validation
                |
                v
  (Future) agricultural safety/evidence layer
                |
                v
        Response + traceable metadata
```

If the user has not selected a model, configuration must fail. If the selected provider is not configured, its protocol is unsupported, or the selected model is unavailable, return an error. Fallback is disabled unless the user explicitly configures an ordered list. The configuration layer validates fallback entries and requires their provider profiles; the current hosted runtime rejects enabled fallback because fallback execution is not implemented.

## Implemented provider configuration

- `load_model_config(path)` reads YAML with PyYAML SafeLoader and validates selection plus provider profiles.
- `build_selected_adapter(config)` constructs only the selected provider.
- API credentials are referenced by environment-variable name in YAML; secret values are resolved at runtime and never written back to config.
- The current factory supports the `openai-compatible` hosted protocol. A future protocol such as `transformers` may be documented in the catalog, but attempting to select it returns an explicit unsupported-protocol error.
- Provider-specific discovery paths and optional modality defaults are passed to the generic adapter. Defaults are never applied globally and never override explicit catalog fields.

## Implemented hosted runtime

`HostedModelRuntime.from_config(config)` constructs the selected adapter from a validated `ModelRuntimeConfig`. Its `generate(request)` method:

1. requires the request's provider, exact model ID, and operation to match the configuration;
2. discovers the provider catalog on first use and caches the validated catalog;
3. resolves the exact selected model and checks advertised capability/terms constraints through `ModelRegistry`;
4. invokes the selected adapter once, without silent retry or provider/model substitution;
5. validates the response provider/model identity before returning it.

Catalog refresh is explicit through `await runtime.refresh_catalog()`. Parallel first requests share one initial catalog discovery. If discovery fails or returns a catalog with the wrong provider identity, a previously valid catalog snapshot is not replaced.

The runtime currently supports only hosted text inference. It rejects enabled fallback, local inference, and any request that differs from the configured model selection. It does not apply agricultural safety checks, execute training, or provide a multimodal interface.

## Implemented provider contract

The `ProviderAdapter` protocol requires:

- a stable `provider_id`;
- asynchronous `discover_models()` returning exact `ModelDescriptor` records;
- asynchronous `generate(request)` accepting a `GenerationRequest` and returning a normalized `GenerationResponse`.

The generic `OpenAICompatibleAdapter` implements a text-only hosted path for providers exposing a compatible model list and chat-completions API. It excludes models unless the catalog explicitly advertises text input and text output, or a provider-specific default was explicitly configured when catalog fields are absent. It uses HTTPS for remote endpoints, can source credentials from an environment variable, surfaces typed provider errors, and rejects responses whose provider/model identity differs from the request.

The adapter does not retry or switch models. It does not implement streaming, tool calls, image/audio/video generation, local inference, fine-tuning, or weight export.

## Data flow and release boundaries

Raw data intake, publication eligibility, and training eligibility are separate states. Dataset records must carry provenance and a review status. Publicly shareable records may be published with their review labels, but only fully approved records may enter a training split under the documented review gate.

Model weights, datasets, and application code do not automatically share one license. Every release must carry explicit terms and provenance.

## Current implementation status

Implemented: typed model descriptors and selections, operation/modality metadata, in-memory registry, strict safe-YAML selection loader, explicit fallback-policy validation, provider configuration parsing, selected OpenAI-compatible adapter construction, hosted text runtime, mocked HTTP integration tests, catalog caching, and exact-response identity checks.

Not yet implemented: fallback execution, provider-specific live smoke-test records, local runtime, training pipeline, dataset engineering, multimodal adapters, streaming/tool calls, and agricultural safety enforcement. Track delivery in [ROADMAP.md](ROADMAP.md).
