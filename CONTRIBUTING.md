# Contributing

Contributions are welcome in software, documentation, data tooling, evaluation, and agricultural safety research. The repository is early-stage; substantial changes should begin with an issue so scope and review requirements are clear.

## Before opening a pull request

1. Read the [Code of Conduct](CODE_OF_CONDUCT.md), [Security Policy](SECURITY.md), and relevant data/model governance documents.
2. Open or link an issue for non-trivial changes.
3. Keep the pull request focused and explain the problem, design, alternatives, and limitations.
4. Add or update tests for behavior changes.
5. Update documentation and example configuration when interfaces or behavior change.
6. Do not include secrets, personal data, partner-confidential material, or data without documented redistribution rights.
7. Never mark a dataset record as approved without the required independent review evidence.

## Local development

Python 3.10+ is required.

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

## Research and data contributions

Research contributions must identify the model/provider, dataset release, benchmark version, evaluation protocol, and relevant hardware/runtime details. See [Reproducibility](docs/REPRODUCIBILITY.md) and [Research Policy](docs/RESEARCH_POLICY.md).

Dataset contributions must include source/provenance and rights information. Publication eligibility and training eligibility are separate. See [Data Governance](docs/DATA_GOVERNANCE.md) and [Data Contribution Guidance](data/CONTRIBUTING.md).

## Review and merge expectations

Pull requests must pass CI and receive maintainer review before merge. Changes affecting model execution, data eligibility, agricultural safety, privacy, or release behavior require explicit tests and documentation. Do not merge with failing checks or unresolved high-impact safety concerns.
