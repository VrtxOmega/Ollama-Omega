# Changelog

All notable changes to Ollama-Omega will be documented in this file.

## [1.0.5] — 2026-04-15

### Added
- **`outputSchema` on all 6 tools** — typed JSON Schema return structures with field descriptions,
  required fields, and error case documentation. This is the key structural gap Glama penalized:
  "no output schema provided" → tools now carry full structured behavioral data.
- Explicit "No authentication required" and "No rate limits" in every description

### Changed
- MCP SDK minimum bumped to `>=1.9.0` to ensure `outputSchema` + `annotations` wire support
- Descriptions shortened — return documentation moved from prose into `outputSchema` where it belongs
- Version bumped to 1.0.5

## [1.0.4] — 2026-04-15

### Changed
- **Complete TDQS rewrite targeting 5/5 on all dimensions** — restructured every tool description
  following Glama's documented 5/5 template pattern
- All 6 tools now follow: Purpose → When to use → When NOT to use → Prerequisites → Behavior → Returns
- **Behavior** (2→5): Added error handling, retry safety, idempotency, timeout behavior for each tool
- **Completeness** (2→5): Full return structure with field types, edge cases, empty result behavior
- **Usage Guidelines** (2→5): Explicit "Do not use for X — use Y instead" cross-references on every tool
- **Parameters** (3→5): Added decision guidance (low temp for factual, high for creative), format
  examples (`name:tag`), and tool-to-tool data flow (use `name` from `ollama_list_models` output)
- Version bumped to 1.0.4

## [1.0.3] — 2026-04-15

### Added
- **MCP ToolAnnotations** on all 6 tools — `readOnlyHint`, `destructiveHint`, `idempotentHint`,
  `openWorldHint`, and `title` for full Behavioral Transparency scoring
- `minLength` constraints on all string parameters requiring non-empty input
- `minimum`/`maximum` constraints on `temperature` (0.0–2.0) and `max_tokens` (≥-1) parameters
- `minItems: 1` constraint on `ollama_chat` messages array
- `additionalProperties: false` on nested message items in `ollama_chat`

### Changed
- Tightened all tool descriptions for higher Conciseness & Structure score —
  front-loaded critical info, removed filler, standardized return value format notation
- Descriptions now use compact `{ key: type }` return format for consistency
- Version bumped to 1.0.3

## [1.0.2] — 2026-04-15

### Added
- Server instructions via MCP `initialization_options.instructions` — provides agents with recommended
  workflow order and tool disambiguation guidance
- Glama Card Badge and Score Badge in README
- `additionalProperties: false` on all tool input schemas for stricter validation

### Changed
- **Tool definitions upgraded for Glama Tool Definition Quality scoring** — all 6 tools now include:
  purpose clarity, usage guidelines, behavioral transparency (read-only vs write, side effects),
  parameter semantics (valid ranges, formats, defaults), and return value descriptions
- Rich parameter descriptions with examples, valid values, and relationship to Ollama API parameters
- `ollama_chat` message items now include `enum` constraints on the `role` field
- Version bumped to 1.0.2

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
