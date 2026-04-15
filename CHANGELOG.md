# Changelog

All notable changes to Ollama-Omega will be documented in this file.

## [1.0.1] — 2026-04-15

### Added
- `glama.json` — Glama MCP directory registration
- `tests/test_server.py` — 48 tests covering tools, dispatch, errors, SSRF, config
- `examples/basic_usage.py` — programmatic MCP client example
- `pyproject.toml` — keywords, classifiers, CLI entry point, project URLs, pytest config

### Changed
- Moved `BUILD_SPEC.md` to `docs/BUILD_SPEC.md` (internal; not for public repo root)
- Updated README to AAA standard with architecture diagram, hardening audit, test section

### Fixed
- `pyproject.toml` now declares `httpx>=0.27.0` as explicit dependency

## [1.0.0] — 2026-04-15

### Added
- Initial release of `ollama_mcp_server.py` — hardened MCP server bridging Ollama
- 6 tools: `ollama_health`, `ollama_list_models`, `ollama_chat`, `ollama_generate`, `ollama_show_model`, `ollama_pull_model`
- 7-point hardening: SSRF mitigation, singleton client, argument validation, safe JSON, structured logging, DRY payloads, error sanitization
- VERITAS-branded README, LICENSE (MIT), pyproject.toml, requirements.txt, CHANGELOG
- Deployed to GitHub (`VrtxOmega/Ollama-Omega`) and Codeberg (`VeritasOmega/Ollama-Omega`)
