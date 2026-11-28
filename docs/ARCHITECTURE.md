# System architecture

## Design goal

Build a modular agricultural AI research platform that lets users select the exact model/provider while AgroGuardAI supplies domain-specific data governance, evaluation, safety controls, and reproducible experiment tooling.

The architecture must not depend on one model vendor or hide model substitution.

## Logical components

1. **Model registry** — stores exact provider/model identifiers, supported operations, modality capabilities, availability, and terms-review status. The in-memory registry and core model contracts are implemented.
2. **Provider adapters** — translate a common internal request into each provider's API or local-runtime interface. A shared async protocol is implemented; concrete provider integrations are not yet released.
3. **Execution layer** — runs hosted inference or local inference/fine-tuning as distinct operations. It must preserve exact model selection and keep credentials outside source control. This layer is not yet implemented.
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
    Execution (hosted or local)
                |
                v
  Agricultural safety / evidence checks
                |
                v
     Response + traceable metadata
```

If the user has not selected a model, configuration must fail. If the selected model is unavailable or unsupported, return an error. Fallback is disabled unless the user explicitly configures an ordered list. The current package validates explicit fallback candidates but does not execute fallback because the execution layer has not been implemented.

## Implemented provider contract

The `ProviderAdapter` protocol requires:

- a stable `provider_id`;
- asynchronous `discover_models()` returning exact `ModelDescriptor` records;
- asynchronous `generate(request)` accepting a `GenerationRequest` and returning a normalized `GenerationResponse`.

Catalog registration checks that every discovered descriptor belongs to the provider that supplied it. The response validation helper rejects provider/model identity mismatches. Concrete adapters and the execution component must call these checks; the protocol alone does not make vendor integrations safe.

## Data flow and release boundaries

Raw data intake, publication eligibility, and training eligibility are separate states. Dataset records must carry provenance and a review status. Publicly shareable records may be published with their review labels, but only fully approved records may enter a training split under the documented review gate.

Model weights, datasets, and application code do not automatically share one license. Every release must carry explicit terms and provenance.

## Current implementation status

Implemented: typed model descriptors and selections, operation/modality metadata, in-memory registry, strict safe-YAML selection loader, explicit fallback-policy validation, provider adapter protocol, and exact-response identity checks.

Not yet implemented: concrete provider integrations, model discovery refresh, hosted/local execution, training pipeline, dataset engineering, and agricultural safety enforcement. Track delivery in [ROADMAP.md](ROADMAP.md).
