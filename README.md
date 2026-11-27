# AgroGuardAI LLM Foundation

[![CI](https://github.com/mohammerd/agroguardai-llm-foundation/actions/workflows/ci.yml/badge.svg)](https://github.com/mohammerd/agroguardai-llm-foundation/actions/workflows/ci.yml)

Research infrastructure for building and evaluating safer agricultural language models, with an initial focus on Nigerian and other underrepresented African languages.

AgroGuardAI is not a generic chatbot wrapper. The project is intended to combine a governed agricultural data foundation, model-agnostic execution, language-specific evaluation, and safety controls for high-impact agronomic advice.

## Project status

**Early research foundation — not production-ready.** The public repository currently contains the package scaffold, governance documentation, model-selection policy, collaboration templates, and CI/security workflows. Provider adapters, model execution, dataset pipelines, and agricultural safety enforcement are planned but not yet implemented.

The legacy research repository is `mohammerd/agroguardai-llm`. No legacy datasets, model weights, or training results have been migrated or cleared for redistribution. The old repository remains the source archive during the migration review.

## Design principles

- **Evidence before advice:** distinguish sourced facts, uncertainty, and cases requiring local expert help.
- **Language inclusion:** evaluate each language independently; do not infer local-language quality from English scores.
- **Safety first:** high-impact advice about chemicals, dosages, disease treatment, and animal health requires heightened review.
- **Reproducibility:** record exact model/data revisions, configs, code commits, seeds, dependencies, hardware, and evaluation methods.
- **Responsible data release:** document source, rights, consent, privacy, and review labels. Public availability does not imply training approval.
- **Explicit model choice:** users select the provider and exact model ID. No random selection or silent provider substitution.
- **Model portability:** separate hosted inference from local inference and fine-tuning. API access does not imply downloadable weights or permission to redistribute them.

## Model support

The target registry is extensible and is intended to include providers and model families such as DeepSeek, Qwen, Gemma, Kimi/Moonshot, Llama, and other supported models. A model is selectable only when an adapter and its capabilities are implemented and validated. See [Model Registry](docs/MODEL_REGISTRY.md).

## Project documentation

- [Architecture](docs/ARCHITECTURE.md) — target system boundaries and request flow.
- [Roadmap](docs/ROADMAP.md) — evidence-gated project milestones.
- [Data Governance](docs/DATA_GOVERNANCE.md) — publication versus training eligibility.
- [Research Policy](docs/RESEARCH_POLICY.md) — claim and evaluation standards.
- [Reproducibility](docs/REPRODUCIBILITY.md) — experiment manifest requirements.
- [Model Registry](docs/MODEL_REGISTRY.md) — explicit model/provider selection.
- [Model Benchmark Protocol](docs/BASE_MODEL_BENCHMARK.md) — candidate comparison methodology.
- [Migration Plan](docs/MIGRATION_PLAN.md) — controlled migration from the legacy repository.
- [Model Card Template](docs/templates/MODEL_CARD_TEMPLATE.md) — documentation required for model releases.
- [Dataset Card Template](docs/templates/DATASET_CARD_TEMPLATE.md) — documentation required for dataset releases.
- [Experiment Review Template](docs/templates/EXPERIMENT_REVIEW_TEMPLATE.md) — independent experiment review record.
- [Changelog](CHANGELOG.md) — documented project changes.

## Repository layout

- `src/agroguardai/` — reusable Python package.
- `configs/` — example model and experiment configurations.
- `data/` — schemas, source metadata, and annotation guidance; no legacy dataset is released yet.
- `docs/` — architecture, governance, evaluation, and research policies.
- `tests/` — automated validation.
- `.github/` — CI, CodeQL, Dependabot, issue forms, and contribution templates.

## Development

Python 3.10+ is required.

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

## Safety notice

This is a research project, not a certified agronomic advisory service. Model outputs can be wrong and must not be treated as a substitute for qualified local agronomists, product labels, or official agricultural guidance. Never use an unvalidated model output as the sole basis for pesticide application, chemical dosage, or other potentially harmful action.

## Contributing and security

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Please read the [Code of Conduct](CODE_OF_CONDUCT.md) and [Security Policy](SECURITY.md) before participating. Cite the project using [CITATION.cff](CITATION.cff).

## License

The software source code is licensed under Apache-2.0. Dataset releases, model weights, and third-party materials have separate terms and must not be assumed to share the code license. See each release's documentation.
