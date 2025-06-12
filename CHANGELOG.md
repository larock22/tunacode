# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Comprehensive fallback response mechanism when agent reaches maximum iterations without user response (#22)
  - Response state tracking across all agent types (main agent, readonly agent, orchestrator)
  - Configurable fallback verbosity levels (minimal, normal, detailed)
  - Context extraction showing tool calls, files modified, and commands run in fallback responses
- Configuration option `fallback_response` to enable/disable fallback responses
- Automatic synthesis of incomplete task status when max iterations reached

### Fixed

- Orchestrator bug where fallback responses appeared even when tasks produced output (#22)
- Response state tracking to ensure fallback only triggers when no user-visible output exists

### Changed

- Modified CLI commands processing
- Updated REPL functionality
- Enhanced output display formatting
- Improved fallback response mechanism to handle edge cases across different agent types

## [0.0.23] - 2025-01-06

### Added

- Fallback response handling for agent iterations

## [0.0.22] - 2025-01-06

### Added

- Control-C handling improvements for smooth exit

## [0.0.21] - 2025-01-06

### Fixed

- Various bug fixes and improvements

## [0.0.19] - 2025-01-06

### Added

- Orchestrator features with planning visibility
- Background manager implementation

### Changed

- Updated README with orchestrator features
- System prompt updates

## [0.0.18] - 2025-01-05

### Fixed

- Circular import in ReadOnlyAgent
- Orchestrator integration to use TunaCode's LLM infrastructure

## [0.0.17] - 2025-01-05

### Changed

- General codebase cleanup

## [0.0.16] - 2025-01-05

### Fixed

- Publish script to use temporary deploy venv
- Improved .gitignore

## [0.0.15] - 2025-01-05

### Added

- Shell command support with `!` prefix
- Updated yolomode message

### Fixed

- Escape-enter keybinding test

## [0.0.14] - 2025-01-04

### Changed

- Various improvements and bug fixes

## [0.0.13] - 2025-01-04

### Changed

- Initial stable release with core features
