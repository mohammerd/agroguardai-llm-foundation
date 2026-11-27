# Reproducibility standard

Every benchmark, training, and evaluation result must have a machine-readable experiment manifest.

## Required fields

- experiment ID and creation timestamp;
- source repository commit;
- exact model provider and model ID;
- immutable model revision where possible; for hosted aliases, provider identifier and run timestamp;
- tokenizer identity and revision;
- dataset release ID, checksums, and split version;
- configuration file and checksum;
- random seeds and determinism settings;
- Python, framework, CUDA/driver, and dependency versions;
- hardware and memory;
- prompt/template version and decoding parameters;
- evaluation code commit, benchmark version, scoring rubric, and reviewer protocol;
- raw result artifact locations and checksums;
- known limitations, failed runs, exclusions, and deviations from protocol.

## Rules

Do not report a result without the manifest. Do not overwrite old reports; create a new version. Record failed and incomplete experiments. Keep personal data, provider credentials, confidential partner information, and private prompts out of public manifests.

Hosted model aliases can change upstream. Record the exact provider-returned model ID and timestamp; do not claim exact reproducibility when the provider does not expose an immutable revision.

For human-reviewed language and agronomy evaluations, report reviewer qualifications and process without publishing private reviewer identities.
