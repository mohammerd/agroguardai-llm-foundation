# System architecture

## Design goal

Build a modular agricultural AI research platform that allows users to select the exact model/provider while AgroGuardAI supplies the domain-specific data governance, evaluation, safety controls, and reproducible experiment tooling.

The architecture must not depend on one model vendor or hide model substitution.

## Logical components

1. **Model registry** — stores provider/model identifiers, supported operations, modality capabilities, terms-review status, and discovery timestamps.
2. **Provider adapters** — translate a common internal request into each provider's API or local-runtime interface. Adapters must expose capabilities and normalize errors without silently changing models.
3. **Execution layer** — runs hosted inference or local inference/fine-tuning as distinct operations. Credentials remain outside source control and are injected at runtime.
4. **Data pipeline** — validates schemas, tracks provenance and consent/rights, preserves annotation statuses, detects duplicates, and creates leakage-resistant versioned splits.
5. **Agricultural safety layer** — checks task-specific constraints, evidence requirements, uncertainty, and referral conditions. It must fail safely when required information is missing.
6. **Evaluation layer** — evaluates each language and task independently, records exact experiment manifests, and generates reports.
7. **Release layer** — packages software, dataset releases, and model artifacts separately with their own version, license, provenance, and documentation.

## Request flow

```text
User selects provider + exact model ID
                |
                v
       Registry validation
                |
       capability / terms check
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

If the user has not selected a model, the request must fail with a clear configuration error. If the selected model is unavailable, return an error. Fallback is disabled unless the user has explicitly configured an ordered list. Every fallback candidate must be visible and logged before execution.

## Provider adapter contract

An adapter should provide:

- stable provider identity and model discovery where supported;
- exact model-ID validation;
- explicit capability declarations (text, image, audio, video, tools, context limits);
- operation support: hosted inference, local inference, fine-tuning, export;
- consistent timeout, rate-limit, authentication, and unavailable-model errors;
- bounded retries that do not switch model/provider;
- no credential or private prompt logging.

A hosted API integration must not claim local weights or fine-tuning support. Terms and license metadata must be verified before a model is used for training or its artifacts are redistributed.

## Data flow and release boundaries

Raw data intake, publication eligibility, and training eligibility are separate states. Dataset records must carry provenance and a review status. Publicly shareable records may be published with their review labels, but only fully approved records may enter a training split under the documented review gate.

Model weights, datasets, and application code do not automatically share one license. Every release must carry explicit terms and provenance.

## Current implementation status

This document describes the target architecture. The current repository contains the initial Python package scaffold and governance documentation; provider adapters, model execution, data pipelines, and safety enforcement are not yet implemented. Track delivery in [ROADMAP.md](ROADMAP.md).
