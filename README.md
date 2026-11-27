# AgroGuardAI LLM Foundation

Research infrastructure for building and evaluating safer agricultural language models, with an initial focus on Nigerian and other underrepresented African languages.

AgroGuardAI is not a generic chatbot wrapper. The project aims to build a reproducible agricultural AI foundation: governed datasets, transparent model experiments, language-specific evaluation, and safety controls for high-impact agronomic advice.

## Project status

**Early foundation / migration in progress.** This repository is being established as the clean public home for the project. The legacy research repository is `mohammerd/agroguardai-llm`. No legacy datasets, model weights, or training results are considered migrated or cleared for redistribution until they have passed the documented provenance, privacy, licensing, and quality checks.

## Principles

- **Evidence before advice:** distinguish sourced facts, uncertain suggestions, and cases requiring local expert help.
- **Language inclusion:** evaluate each supported language independently; do not infer local-language quality from English scores.
- **Safety first:** unsafe pesticide, dosage, disease-treatment, and other high-impact recommendations require special review and conservative behavior.
- **Reproducibility:** record exact base-model revisions, data releases, configs, code versions, seeds, and evaluation results.
- **Responsible data release:** publish only records with a documented right to redistribute; retain review labels and never equate public availability with training approval.
- **Open research:** publish code and documentation where possible, while respecting data rights, consent, privacy, and upstream model licenses.

## Repository map

- `src/agroguardai/` — reusable data, training, inference, evaluation, and safety modules.
- `data/` — schemas, source metadata, annotation guidance, and approved-to-share datasets.
- `configs/` — versioned experiment configurations.
- `docs/` — governance, migration, and evaluation protocols.
- `tests/` — automated validation and regression tests.
- `reports/` — reproducible evaluation reports and release notes.

## Data and model availability

No dataset or model weights are currently released from this repository. Dataset publication and training eligibility are separate decisions. See [Data governance](docs/DATA_GOVERNANCE.md) before contributing or using data.

## Development

Python 3.10+ is required.

```bash
python -m pip install -e ".[dev]"
pytest
```

## Base-model selection

Qwen and Llama are candidates, not settled choices. Selection will follow the documented multilingual agricultural benchmark and license review in [Base-model benchmark protocol](docs/BASE_MODEL_BENCHMARK.md).

## Safety notice

This is a research project, not a certified agronomic advisory service. Model outputs can be wrong and must not be treated as a substitute for qualified local agronomists, product labels, or official agricultural guidance. Never use an unvalidated model output as the sole basis for pesticide application, chemical dosage, or other potentially harmful action.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), [data contribution guidance](data/CONTRIBUTING.md), and [SECURITY.md](SECURITY.md) before opening a contribution.

## License

Code licensing and data/model licensing may differ. The repository license applies only to files that the project has the right to license. Dataset and model releases will carry their own explicit terms and provenance.
