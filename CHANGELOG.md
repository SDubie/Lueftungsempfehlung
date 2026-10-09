# Changelog

All notable changes to this project will be documented in this file.

## 0.4.0 - 2026-10-09

### Added

- Dedicated dry-air recommendation handling for ventilation decisions and matching sensor icon updates.
- Improved notification logic for active-device checks and reminder behavior.
- Duplicate-entry validation in the config flow with clearer user feedback when a sensor is already configured.
- Stricter entity selectors restricted by device class to reduce invalid configuration entries.

### Changed

- Refined the ventilation reason handling and notification messaging around humidity-based recommendations.
- Improved validation and setup feedback for configuration and sensor selection.
- Updated developer tooling and quality checks to support maintenance and release readiness.

## 0.3.0 - 2026-07-29

### Added

- Short and long reason texts (`reason_short` and `reason`) as sensor attributes.
- Notification quiet-hours settings (`notification_silence_start`, `notification_silence_end`).
- External notification mute control via entity (`notification_silence_entity`), e.g. schedule helper.
- Multi-step setup and options flow (base sensors, notifications, advanced thresholds).

### Changed

- Switched not-recommended humidity guard to absolute humidity comparison.
- Notification text now uses short reason labels and shows absolute humidity for humidity-related reasons.
- Replaced ambiguous neutral reason with explicit no-ventilation-needed reason.
- Updated translations and README for the new configuration and notification behavior.

## 0.2.0 - 2026-07-27

### Added

- README with setup, status logic, and HACS installation notes.
- Git ignore rules for `__pycache__` and VS Code settings.
- VS Code tasks for local development setup and test execution.
- Brand assets for integration icon and logo.

### Changed

- Improved ventilation status handling and configuration reload behavior.
