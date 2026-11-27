# Data governance

## Two separate gates

A record may be published for research transparency without being eligible for training. These decisions must never be conflated.

### Gate A: publication

Before public release, verify:

- documented source and chain of custody;
- explicit redistribution rights or a compatible license;
- consent where required;
- removal of names, phone numbers, account identifiers, precise farm coordinates, and other identifying details;
- no confidential partner or institution material;
- no unlicensed copied text, images, audio, or transcripts;
- a stable record identifier and provenance metadata.

### Gate B: training

In addition to Gate A, require:

- language identification and competent native-language review;
- agronomic correctness review by a qualified reviewer;
- evidence/source review for factual claims;
- three distinct reviewer approvals recorded in the audit trail;
- duplicate and train/evaluation leakage checks;
- safety screening for chemical, dosage, disease-treatment, and other high-impact advice.

A pending, rejected, or needs-revision record must not enter a training split. Approval must be explicit, auditable, and tied to a dataset version.

## Review statuses

Use only these canonical statuses: `pending`, `needs_revision`, `rejected`, and `approved`. Keep reviewer identity data private; publish only the minimum non-identifying audit metadata needed to establish independent review.

## Historical audit figures

Numbers from the legacy repository are historical and must be re-computed against the exact migration commit before they are repeated as current dataset statistics. No legacy data is automatically cleared by this document.
