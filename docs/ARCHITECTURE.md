# System architecture

## Design goal

Build a modular agricultural AI research platform that lets users select the exact model/provider while AgroGuardAI supplies domain-specific data governance, evaluation, safety controls, and reproducible experiment tooling.

The architecture must not depend on one model vendor or hide model substitution.

## Logical components

1. **Model registry** — stores exact provider/model identifiers, supported operations, modality capabilities, availability, and terms-review status. The in-memory registry and core model contracts are implemented.
2. **Provider adapters** — translate a common internal request into each provider's API or local-runtime interface. A shared async protocol and a generic OpenAI-compatible hosted text adapter are implemented. Provider-specific differences require their own tested adapters.
3. **Execution layer** — coordinates registry resolution and adapter invocation. It must preserve exact model selection, validate returned model identity, and keep credentials outside source control. A unified execution/orchestration service is not yet implemented.
4. **Data pipeline** — validates schemas, tracks provenance and consent/rights, preserves annotation statuses, detects duplicates, and creates leakage-resistant versioned splits. This layer is not yet implemented.
5. **Agricultural safety layer** — checks task-specific constraints, evidence requirements, uncertainty, and referral conditions. It must fail safely when required information is missing. This layer is not yet implemented.
6. **Evaluation layer** — evaluates each language and task independently, records exact experiment manifests, and generates reports. Documentation and templates exist; executable benchmark tooling is still planned.
7. **Release layer** — packages software, dataset releases, and model artifacts separately with their own version, license, provenance, and documentation. Release governance is documented; model/dataset releases do not yet exist.

## Request flow

```text
User selects provider + exact model ID
                |
                v
       Strict configuration
                |
                v
       Model registry validation
                |
       capability / terms checks
                |
                v
       Explicit provider adapter
                |
                v
    Hosted or local execution
                |
                v
  Agricultural safety / evidence checks
                |
                v
     Response + traceable metadata
```

If the user has not selected a model, configuration must fail. If the selected model is unavailable or unsupported, return an error. Fallback is disabled unless the user explicitly configures an ordered list. The current package validates explicit fallback candidates but does not execute fallback.

## Implemented provider contract

The `ProviderAdapter` protocol requires:

- a stable `provider_id`;
- asynchronous `discover_models()` returning exact `ModelDescriptor` records;
- asynchronous `generate(request)` accepting a `GenerationRequest` and returning a normalized `GenerationResponse`.

The generic `OpenAICompatibleAdapter` implements a text-only hosted path for providers exposing a compatible model list and chat-completions API. It excludes models unless the catalog explicitly advertises text input and text output. It uses HTTPS for remote endpoints, can source credentials from an environment variable, surfaces typed provider errors, and rejects responses whose provider/model identity differs from the request.

This is not yet a full provider execution service. Callers must resolve the user's exact model through `ModelRegistry` before calling the adapter. The adapter does not retry or switch models.

## Data flow and release boundaries

Raw data intake, publication eligibility, and training eligibility are separate states. Dataset records must carry provenance and a review status. Publicly shareable records may be published with their review labels, but only fully approved records may enter a training split under the documented review gate.

Model weights, datasets, and application code do not automatically share one license. Every release must carry explicit terms and provenance.

## Current implementation status

Implemented: typed model descriptors and selections, operation/modality metadata, in-memory registry, strict safe-YAML selection loader, explicit fallback-policy validation, provider adapter protocol, generic OpenAI-compatible text adapter, mocked HTTP integration tests, and exact-response identity checks.

Not yet implemented: provider-specific live smoke-test records, unified execution orchestration, local runtime, training pipeline, dataset engineering, multimodal adapters, and agricultural safety enforcement. Track delivery in [ROADMAP.md](ROADMAP.md).
