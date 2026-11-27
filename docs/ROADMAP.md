# Project roadmap

This roadmap describes evidence-gated milestones. Dates are intentionally omitted until owners, dependencies, and evaluation capacity are confirmed.

## M0 — Public project foundation

- [x] Public repository and baseline Python package
- [x] Basic CI for tests and lint
- [x] Data publication versus training governance
- [x] Explicit model selection policy
- [ ] Complete citation, conduct, and collaboration metadata
- [ ] Repository security settings and branch rules

**Exit criteria:** repository metadata is accurate; clean installation and CI are repeatable; contributor and security processes are documented.

## M1 — Core contracts and validation

- [ ] Typed provider, model, capability, and operation contracts
- [ ] Strict configuration parser and schema validation
- [ ] Explicit selection errors; no implicit default or fallback
- [ ] Unit tests for unknown providers, unknown models, unavailable models, and unsupported operations
- [ ] Structured experiment manifest

**Exit criteria:** model choice is deterministic, inspectable, and test-covered without requiring a paid provider.

## M2 — Provider adapters

- [ ] Local open-weight runtime adapter
- [ ] DeepSeek hosted adapter
- [ ] Moonshot/Kimi hosted adapter
- [ ] Qwen and Gemma local model registrations where current terms and runtimes permit
- [ ] Additional providers through the same adapter contract
- [ ] Mock-server contract tests and safe credential handling

**Exit criteria:** each adapter passes the same contract tests; unavailable providers produce clear errors and never trigger silent substitution.

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
- [ ] Model cards and dataset cards
- [ ] Independent external review of methodology

**Exit criteria:** results can be independently reproduced from published manifests and permissible artifacts; no broad quality claims without evidence.

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
