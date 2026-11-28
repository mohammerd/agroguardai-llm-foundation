# AgroGuardAI LLM Foundation

[![CI](https://github.com/mohammerd/agroguardai-llm-foundation/actions/workflows/ci.yml/badge.svg)](https://github.com/mohammerd/agroguardai-llm-foundation/actions/workflows/ci.yml)

Research infrastructure for building and evaluating safer agricultural language models, with an initial focus on Nigerian and other underrepresented African languages.

AgroGuardAI is not a generic chatbot wrapper. The project combines a governed agricultural data foundation, model-agnostic execution, language-specific evaluation, and safety controls for high-impact agronomic advice.

## Project status

**Early research infrastructure — not production-ready.** The repository includes a tested model registry, configuration-driven construction of the selected OpenAI-compatible provider adapter, a generic hosted text adapter, and mocked integration tests. No live provider smoke tests, local runtime, training pipeline, dataset release, or agricultural safety enforcement are claimed yet.

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

The first hosted integration is a generic OpenAI-compatible text adapter. It includes documented catalog handling for DeepSeek and OpenRouter, plus provider-specific modality defaults for Moonshot/Kimi's model-list format. The YAML provider profiles can now be loaded, and the selected compatible adapter can be constructed from the configured base URL and a named environment variable. Mocked fixtures cover the documented response formats; live credentials and per-model smoke tests remain opt-in and have not been claimed as completed. Other protocols require dedicated adapters. See [Provider Adapters](docs/PROVIDER_ADAPTERS.md).

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

## Core API: configuration-driven hosted provider

Copy `configs/models.example.yaml` to your own configuration file. Set the primary `provider` and exact `model_id`; provider credentials are named there, but their values remain in environment variables.

For example, when selecting DeepSeek:

```bash
export DEEPSEEK_API_KEY="your-key"
```

```python
import asyncio

from agroguardai import (
    ChatMessage,
    GenerationRequest,
    ModelRegistry,
    OpenAICompatibleAdapter,
    build_selected_adapter,
    load_model_config,
)


async def main():
    runtime_config = load_model_config("configs/models.yaml")
    adapter = build_selected_adapter(runtime_config)

    # Refresh the selected provider's catalog and validate the exact model ID.
    registry = ModelRegistry()
    registry.register_provider_catalog(adapter.provider_id, await adapter.discover_models())
    selection = runtime_config.selection.primary
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

Change the YAML selection to another configured provider, such as `moonshot` or `openrouter`, and set that provider's credential environment variable. The factory constructs only the selected provider. It does not load credential values from YAML, choose a model, execute fallback, or claim unimplemented protocols such as `transformers` are supported.

The example uses hosted APIs and may incur provider charges. The generic adapter is text-only; image/video support indicated by upstream model catalogs is not exposed by this adapter.

## Core API: direct provider construction

For applications that manage their own settings, instantiate the generic adapter directly:

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

Provider-specific modality defaults apply only when the upstream model catalog omits those fields. Explicit catalog metadata always takes precedence. See [Provider Adapters](docs/PROVIDER_ADAPTERS.md).

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

- `src/agroguardai/` — typed model contracts, registry, provider config loader, and provider adapters.
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
