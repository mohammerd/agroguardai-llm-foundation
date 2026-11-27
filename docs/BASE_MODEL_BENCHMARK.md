# Base-model benchmark protocol

Qwen and Llama are candidate families. No base model is selected yet.

Compare exact model revisions under matched conditions. Before testing, record model identifier, revision, license, tokenizer, context length, quantization, hardware, inference settings, and any restrictions on derivative weights.

Evaluate each supported language independently. Include Hausa, Yoruba, Igbo, Fulfulde, Kanuri, Tiv, Ibibio, and Nigerian Pidgin where benchmark coverage and qualified reviewers are available.

Measure:
- agricultural factuality and evidence alignment;
- harmful or unsupported chemical and dosage advice;
- uncertainty calibration and appropriate referral;
- language fluency and meaning preservation;
- robustness to spelling variation, code-switching, and low-resource prompts;
- refusal quality for unsafe or underspecified requests;
- latency, memory use, and practical inference cost.

Use a fixed, versioned benchmark with native-language and agronomy review. Report per-language results, confidence intervals where appropriate, failure examples with sensitive details removed, and limitations. Do not select a model based only on English scores or a single aggregate metric.
