# AgroGuardAI LLM Foundation

[![CI](https://github.com/mohammerd/agroguardai-llm-foundation/actions/workflows/ci.yml/badge.svg)](https://github.com/mohammerd/agroguardai-llm-foundation/actions/workflows/ci.yml)

Research infrastructure for building and evaluating safer agricultural language models, with an initial focus on Nigerian and other underrepresented African languages.

AgroGuardAI is not a generic chatbot wrapper. The project combines a governed agricultural data foundation, model-agnostic execution, language-specific evaluation, and safety controls for high-impact agronomic advice.

## Project status

**Early research infrastructure — not production-ready.** The repository includes a tested model registry, strict YAML selection configuration, a provider-adapter protocol, a generic OpenAI-compatible hosted text adapter, and mocked integration tests. No live provider smoke tests, local runtime, training pipeline, dataset release, or agricultural safety enforcement are claimed yet.

The legacy research repository is `mohammerd/agroguardai-llm`. It remains unchanged as the source archive during migration review.

## Design principles

- **Evidence before advice:** distinguish sourced facts, uncertainty, and cases requiring local expert help.
- **Language inclusion:** evaluate each language independently; do not infer local-language quality from English scores.
- **Safety first:** high-impact advice about chemicals, dosages, disease treatment, and animal health requires heightened review.
- **Reproducibility:** record exact model/data revisions, configs, code commits, seeds, dependencies, hardware, and evaluation methods.
- **Responsible data release:** document source, rights, consent, privacy, and review labels. Public availability does not imply training approval.
- **Explicit model choice:** users select the provider and exact model ID. No random selection or silent provider substitution.
- **Model portability:** separate hosted inference from local inference and fine-tuning. API access does not imply downloadable weights or permission to redistribute them.

## Model support

The registry is designed to support multiple providers and model families, including DeepSeek, Qwen, Gemma, Kimi/Moonshot, Llama, OpenAI, Anthropic, and other providers. A model is selectable only after its exact provider/model ID and supported operation have been registered.

The first hosted integration is a generic OpenAI-compatible text adapter. It includes documented catalog handling for DeepSeek and OpenRouter, plus provider-specific modality defaults for Moonshot/Kimi's model-list format. Mocked fixtures cover those response formats; live credentials and per-model smoke tests remain opt-in and have not been claimed as completed. Other providers require endpoint compatibility checks or dedicated adapters. See [Provider Adapters](docs/PROVIDER_ADAPTERS.md).

## Core API: model registry

The registry can be used without paid API credentials:

```python
from agroguardai import ModelDescriptor, ModelRegistry, ModelSelection, Operation, TermsStatus

registry = ModelRegistry()
registry.register(
    ModelDescriptor(
        provider_id="local",
        model_id="agro-model-3b",
        display_name="Agro Model 3B",
        operations=frozenset({Operation.LOCAL_INFERENCE}),
        terms_status=TermsStatus.REVIEWED,
        terms_url="https://example.org/model-license",
        terms_reviewed_at="2026-11-28T12:00:00Z",
    )
)

selected = registry.resolve(
    ModelSelection(
        provider_id="local",
        model_id="agro-model-3b",
        operation=Operation.LOCAL_INFERENCE,
    )
)
print(selected.model_id)
```

This validates metadata and selection. It does not download weights or run local inference.

## Core API: hosted inference

The generic adapter supports text-only hosted inference through an OpenAI-compatible chat-completions API. Set the provider key in the runtime environment, not in source code or committed YAML.

For DeepSeek:

```bash
export DEEPSEEK_API_KEY="your-key"
```

```python
import asyncio

from agroguardai import (
    ChatMessage,
    GenerationRequest,
    ModelRegistry,
    ModelSelection,
    OpenAICompatibleAdapter,
    Operation,
)

async def main():
    adapter = OpenAICompatibleAdapter.from_env(
        api_key_env="DEEPSEEK_API_KEY",
        provider_id="deepseek",
        base_url="https://api.deepseek.com",
    )

    registry = ModelRegistry()
    registry.register_provider_catalog(adapter.provider_id, await adapter.discover_models())

    # In a product UI, this exact ID comes from the user's model selection.
    selection = ModelSelection(
        provider_id="deepseek",
        model_id="deepseek-flash",
        operation=Operation.HOSTED_INFERENCE,
    )
    registry.resolve(selection)

    request = GenerationRequest(
        selection=selection,
        messages=(
            ChatMessage("user", "What information is needed to diagnose maize leaf blight?"),
        ),
    )
    response = await adapter.generate(request)
    print(response.output_text)

asyncio.run(main())
```

Use the exact model ID returned by live discovery or selected by the user. The adapter does not choose a default, retry on a different model, or switch providers. This example uses a hosted API and may incur provider charges.

For OpenRouter, use `provider_id="openrouter"`, `base_url="https://openrouter.ai/api/v1"`, and the `OPENROUTER_API_KEY` environment variable.

For Moonshot/Kimi, the model-list API omits the explicit modality arrays used by DeepSeek and OpenRouter. The adapter therefore requires explicit provider-specific defaults based on the documented text chat API:

```python
from agroguardai import OpenAICompatibleAdapter

adapter = OpenAICompatibleAdapter.from_env(
    api_key_env="MOONSHOT_API_KEY",
    provider_id="moonshot",
    base_url="https://api.moonshot.ai/v1",
    catalog_default_input_modalities=("text",),
    catalog_default_output_modalities=("text",),
)
```

Use the endpoint and key for the same Kimi/Moonshot account region. The example uses the international API endpoint. The catalog defaults apply only when modality fields are absent and do not enable image or video requests. See [Provider Adapters](docs/PROVIDER_ADAPTERS.md) for details.

## Project documentation

- [Architecture](docs/ARCHITECTURE.md) — system boundaries and request flow.
- [Roadmap](docs/ROADMAP.md) — evidence-gated project milestones.
- [Data Governance](docs/DATA_GOVERNANCE.md) — publication versus training eligibility.
- [Research Policy](docs/RESEARCH_POLICY.md) — claim and evaluation standards.
- [Reproducibility](docs/REPRODUCIBILITY.md) — experiment manifest requirements.
- [Model Registry](docs/MODEL_REGISTRY.md) — exact model selection and capability checks.
- [Provider Adapters](docs/PROVIDER_ADAPTERS.md) — hosted adapter setup and API references.
- [Model Benchmark Protocol](docs/BASE_MODEL_BENCHMARK.md) — candidate comparison methodology.
- [Migration Plan](docs/MIGRATION_PLAN.md) — controlled migration from the legacy repository.
- [Model Card Template](docs/templates/MODEL_CARD_TEMPLATE.md) — documentation required for model releases.
- [Dataset Card Template](docs/templates/DATASET_CARD_TEMPLATE.md) — documentation required for dataset releases.
- [Experiment Review Template](docs/templates/EXPERIMENT_REVIEW_TEMPLATE.md) — independent experiment review record.
- [Changelog](CHANGELOG.md) — documented project changes.

## Repository layout

- `src/agroguardai/` — typed model contracts, registry, configuration loader, and provider adapters.
- `configs/` — example model and experiment configurations.
- `data/` — schemas, source metadata, and annotation guidance; no legacy dataset is released yet.
- `docs/` — architecture, governance, provider, and research documentation.
- `tests/` — automated unit and mocked integration validation.
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
