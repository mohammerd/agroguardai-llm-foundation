# Base-model benchmark protocol

Qwen, Llama, Gemma, DeepSeek model releases, Kimi/Moonshot models, and other candidates may be evaluated. The initial Qwen-versus-Llama comparison is a starting experiment, not a permanent restriction on supported models.

Separate hosted API models from downloadable-weight models. A hosted model can be benchmarked for inference without being eligible for local training. Fine-tuning candidates must have downloadable weights, supported architecture/runtime, and terms that permit the intended training use. Weight export and redistribution require a separate review.

Compare exact model revisions under matched conditions where possible. Before testing, record model identifier, revision or provider alias, license/terms, tokenizer, context length, quantization, hardware, inference settings, API protocol, and any restrictions on derivative weights.

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

The registry and explicit selection rules are defined in [MODEL_REGISTRY.md](MODEL_REGISTRY.md).
