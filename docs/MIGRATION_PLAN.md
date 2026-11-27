# Legacy migration plan

Source: `mohammerd/agroguardai-llm` (private). Destination: this public repository.

## Rules

- Keep the legacy repository intact until migration is verified.
- Do not copy all files wholesale.
- Do not migrate credentials, private records, model checkpoints, generated artifacts, stale reports, backups, or unreviewed data by default.
- Preserve source commit references and checksums for every migrated artifact.
- Public release requires documented redistribution rights and privacy review.
- Training eligibility remains separate from publication eligibility.

## Migration phases

1. **Inventory:** record source commit, file paths, sizes, checksums, and purpose.
2. **Classify:** mark each item as code, data, model artifact, report, notebook, configuration, or sensitive/obsolete.
3. **Review:** inspect licenses, provenance, secrets, privacy, data quality, and partner restrictions.
4. **Port:** move reusable modules into the package structure; remove duplicate and obsolete scripts.
5. **Validate:** rebuild tests and data validators; verify all data records and split leakage controls.
6. **Benchmark:** compare Qwen and Llama candidates under the same dataset, compute, prompts, and evaluation protocol.
7. **Release:** publish versioned datasets/models only with model cards, data statements, checksums, licenses, and evaluation reports.
8. **Archive:** consider archiving the legacy repository only after all required artifacts and history have been verified.

## First-pass source inventory

The legacy repository contains data JSON files, review/audit artifacts, training and evaluation scripts, configuration files, notebooks, benchmark reports, and a small model adapter/checkpoint. Each category requires separate review. In particular, do not copy the model checkpoint or tokenizer assets until base-model identity, license terms, and redistribution rights are confirmed.
