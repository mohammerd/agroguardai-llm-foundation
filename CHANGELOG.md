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
- Tests for registry errors, operation/terms gates, configuration errors, and no-substitution behavior.

### Changed

- Package API version advanced to 0.2.0.
- README and roadmap now distinguish implemented registry contracts from planned provider integrations.

### Planned

- Concrete hosted and local provider adapters.
- Versioned data validation and experiment manifest implementation.
- Multilingual agricultural benchmark and model/dataset releases.

## Release policy

A release must identify its source commit, version, compatibility, license scope, known limitations, and validation results. Dataset and model artifacts are versioned and licensed separately from the software.
