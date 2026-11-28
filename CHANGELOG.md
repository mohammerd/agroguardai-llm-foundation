# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Until the first tagged release, entries are maintained under Unreleased.

## [Unreleased]

### Added

- Initial public Python package scaffold and CI.
- Data governance and migration documentation.
- Explicit multi-provider model-selection policy.
- Architecture, roadmap, research, and reproducibility documentation.
- Contributor and security guidance.
- Typed model descriptors, explicit model selection, and deterministic in-memory registry.
- Strict safe-YAML selection loader and opt-in ordered fallback validation.
- Shared provider adapter protocol and exact provider/model response checks.
- Generic OpenAI-compatible hosted text adapter with model discovery and chat completions.
- HTTPX transport integration with typed authentication, rate-limit, timeout, connection, server, request, and protocol errors.
- Mocked HTTP tests for DeepSeek-style and OpenRouter-style catalog formats, exact model requests, credential handling, and response identity checks.
- Provider-specific catalog modality defaults for documented APIs such as Moonshot/Kimi that do not return modality arrays.
- Mocked Moonshot/Kimi model discovery coverage for `context_length`, explicit provider defaults, and refusal to override stated catalog capabilities.
- Provider adapter endpoint and security documentation.

### Changed

- Package API version advanced to 0.3.1.
- README and architecture distinguish implemented hosted text inference from planned local-runtime and multimodal integrations.

### Planned

- Live provider smoke tests with opt-in credentials.
- Dedicated adapters for providers with different API semantics.
- Local open-weight runtime and streaming/tool-use contracts.
- Versioned data validation and experiment manifest implementation.
- Multilingual agricultural benchmark and model/dataset releases.

## Release policy

A release must identify its source commit, version, compatibility, license scope, known limitations, and validation results. Dataset and model artifacts are versioned and licensed separately from the software.
