# Project roadmap

This roadmap describes evidence-gated milestones. Dates are intentionally omitted until owners, dependencies, and evaluation capacity are confirmed.

## M0 — Public project foundation

- [x] Public repository and baseline Python package
- [x] Basic CI for tests and lint
- [x] Data publication versus training governance
- [x] Explicit model selection policy
- [x] Citation, conduct, and contributor metadata
- [x] CodeQL, Dependabot, and OpenSSF Scorecard workflows
- [ ] Repository branch rules and required status checks (manual GitHub setting)

**Exit criteria:** repository metadata is accurate; clean installation and CI are repeatable; contributor and security processes are documented.

## M1 — Core contracts and validation

- [x] Typed provider, model, capability, and operation contracts
- [x] Strict YAML selection parser and validation
- [x] Explicit selection errors; no implicit default or fallback
- [x] Unit tests for unknown providers, unknown models, unavailable models, terms gates, and unsupported operations
- [x] Provider adapter protocol and exact-response identity validation
- [x] Deterministic in-memory model registry

**Exit criteria:** model choice is deterministic, inspectable, and test-covered without requiring a paid provider. This milestone does not include model training.

## M2 — Hosted and local provider adapters

- [x] Generic OpenAI-compatible hosted adapter for text model discovery and chat completions
- [x] Configuration-driven construction of the explicitly selected OpenAI-compatible provider
- [x] Runtime environment-variable secret lookup; no key values in YAML
- [x] Strict rejection of unsupported provider protocols
- [x] Mocked HTTP tests for DeepSeek-style and OpenRouter-style catalog responses
- [x] Moonshot/Kimi model-list compatibility using explicit provider-specific text modality defaults
- [x] Mocked HTTP tests for request construction, authentication, rate limits, errors, and model identity
- [ ] Unified request orchestration (load config, discover/register catalog, resolve exact selection, call adapter, validate response)
- [ ] Verify live credentials and run opt-in smoke tests for each configured provider
- [ ] Dedicated adapters for providers with API semantics that differ from chat completions
- [ ] Local open-weight runtime adapter
- [ ] Streaming and tool-call interfaces
- [ ] Image, audio, and video request contracts
- [ ] Provider contract-test suite shared across integrations

**Exit criteria:** each supported integration has a provider-specific smoke-test record and common contract tests; capability declarations come from verified provider metadata or explicit documented provider-specific defaults; no provider switch occurs without an explicit user fallback policy.

## M3 — Dataset engineering

- [ ] Inventory and checksum legacy artifacts
- [ ] Verify source, consent, redistribution rights, privacy, and partner restrictions
- [ ] Publish canonical schema and provenance format
- [ ] Preserve review states and adjudication history
- [ ] Add duplicate, split-leakage, safety, and quality validators
- [ ] Version dataset releases independently from code

**Exit criteria:** every published record has documented provenance and rights status; training candidates satisfy the separate review gate.

## M4 — Evaluation and agricultural safety

- [ ] Versioned benchmark and scoring rubric
- [ ] Native-language review capacity for each language reported
- [ ] Agronomist-reviewed gold set and unsafe-advice tests
- [ ] Per-language results, confidence intervals, and limitations
- [ ] Model cards and dataset cards populated for actual releases
- [ ] Independent external review of methodology

**Exit criteria:** results can be reproduced from published manifests and permissible artifacts; no broad quality claims without evidence.

## M5 — First reproducible model experiment

- [ ] Select candidate models using the benchmark, not brand preference
- [ ] Pin exact base model and tokenizer revisions
- [ ] Train only on eligible data with a documented configuration
- [ ] Record seed, hardware, package versions, run logs, and checkpoints
- [ ] Compare against base models and relevant baselines
- [ ] Publish only after license, safety, and release review

**Exit criteria:** a third party can reproduce the reported evaluation and understand the intended and prohibited uses.

## M6 — Community and research maturity

- [ ] Independent maintainers and reviewers
- [ ] Public issue triage and release cadence
- [ ] Open research notes and benchmark change log
- [ ] Security assessment and supply-chain self-assessment
- [ ] Research partnerships and external replication

A milestone is complete only when its exit criteria are met and the evidence is public or its limits are clearly disclosed.
