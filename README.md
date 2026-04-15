<div align="center">
  <img src="https://raw.githubusercontent.com/VrtxOmega/Gravity-Omega/master/omega_icon.png" width="100" alt="VERITAS" />
  <h1>OLLAMA-OMEGA</h1>
  <p><strong>Sovereign Ollama Bridge — MCP Server for Local & Cloud Models</strong></p>
  <p><em>One file. Two deps. Every Ollama model — local or cloud.</em></p>
</div>

![Status](https://img.shields.io/badge/Status-ACTIVE-success?style=for-the-badge&labelColor=000000&color=d4af37)
![Version](https://img.shields.io/badge/Version-v1.0.2-blue?style=for-the-badge&labelColor=000000)
![Stack](https://img.shields.io/badge/Stack-Python%20%2B%20MCP-informational?style=for-the-badge&labelColor=000000)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&labelColor=000000)
![Tests](https://img.shields.io/badge/Tests-48%20passed-success?style=for-the-badge&labelColor=000000)

<a href="https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega"><img width="380" height="200" src="https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega/badges/card.svg" alt="Ollama-Omega MCP server" /></a>

[![Ollama-Omega MCP server](https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega/badges/score.svg)](https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega)

---

A hardened MCP server that bridges the full Ollama ecosystem — local models and cloud-hosted behemoths alike — into any MCP-compatible IDE. No wrapper scripts. No bloated SDK. Just a single Python file with two dependencies.

> **DESIGN PRINCIPLE:** Ollama-Omega does not abstract away Ollama. It exposes the complete Ollama API surface through 6 validated, error-handled MCP tools with zero information loss.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    MCP Client (IDE)                  │
│         Claude Desktop / Antigravity / etc.          │
└──────────────────────┬──────────────────────────────┘
                       │ stdio (JSON-RPC 2.0)
┌──────────────────────▼──────────────────────────────┐
│              ollama_mcp_server.py                     │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐    │
│  │ Validator│ │ Dispatch │ │ Singleton httpx   │    │
│  │ + Schema │→│ Router   │→│ AsyncClient       │    │
│  └──────────┘ └──────────┘ │ (no redirects)    │    │
│                             └─────────┬─────────┘    │
└───────────────────────────────────────┼──────────────┘
                                        │ HTTP
┌───────────────────────────────────────▼──────────────┐
│                  Ollama Daemon                        │
│    Local models (GPU) │ Cloud models (API proxy)      │
└───────────────────────────────────────────────────────┘
```

## Tools (6)

| Tool | Purpose |
|------|---------|
| `ollama_health` | Check connectivity and list currently running/loaded models |
| `ollama_list_models` | List all available models with size, loaded status, and modification date |
| `ollama_chat` | Send a chat completion request with message history and system prompt |
| `ollama_generate` | Generate a response for a given prompt without chat history |
| `ollama_show_model` | Show detailed information about a specific model (license, parameters) |
| `ollama_pull_model` | Download a model from the Ollama library |

## Hardening Audit

| # | Category | Mitigation |
|---|----------|------------|
| 1 | **SSRF** | Redirects disabled on httpx client (`follow_redirects=False`) |
| 2 | **Resource Leak** | Singleton `AsyncClient` — one connection pool for server lifetime |
| 3 | **Input Validation** | `_validate_required()` gate on every tool before any HTTP call |
| 4 | **JSON Safety** | `_safe_json()` wrapper — never crashes on malformed responses |
| 5 | **Structured Logging** | All stderr output via `logging` module, not raw `print()` |
| 6 | **DRY Payloads** | `_build_options()` centralizes temperature/token mapping |
| 7 | **Error Sanitization** | `_error()` helper — no stack traces, no internals leaked to client |

## Quick Start

### Requirements

- Python 3.11+
- `pip install mcp httpx`

### Configure in Claude Desktop / Antigravity

```json
{
  "mcpServers": {
    "ollama": {
      "command": "uv",
      "args": [
        "--directory",
        "path/to/ollama-mcp",
        "run",
        "python",
        "ollama_mcp_server.py"
      ],
      "env": {
        "PYTHONUTF8": "1",
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_TIMEOUT": "300"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama daemon URL |
| `OLLAMA_TIMEOUT` | `300` | Request timeout in seconds (long for large model pulls/cloud inference) |
| `PYTHONUTF8` | — | Set to `1` for Windows Unicode safety |

### Cloud Models

Ollama-Omega is version-agnostic. If your Ollama daemon exposes cloud-hosted models (e.g., `qwen3.5:397b-cloud` via API proxy), they are accessible through the same 6 tools — no configuration change required.

## File Structure

```
Ollama-Omega/
  ollama_mcp_server.py     # MCP server (~307 lines) — hardened, single-file
  pyproject.toml            # Package metadata, CLI entry, PyPI classifiers
  requirements.txt          # mcp>=1.0.0, httpx>=0.27.0
  glama.json                # Glama MCP directory registration
  LICENSE                   # MIT
  CHANGELOG.md              # Version history
  tests/
    test_server.py           # 48 tests — tools, dispatch, errors, SSRF, config
  examples/
    basic_usage.py           # Programmatic MCP client example
  docs/
    BUILD_SPEC.md            # Internal build specification
```

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

48 tests covering:
- **Tool Definitions** — schema validation, required fields, descriptions
- **Helper Functions** — options builder, validation, JSON safety, error formatting
- **Dispatcher** — all 6 tool paths with mocked HTTP responses
- **Error Handling** — connection, timeout, HTTP status, exception sanitization
- **Configuration** — environment defaults, SSRF mitigation, server identity

## Companion Server

Ollama-Omega is the transport layer for the [**Omega Brain MCP**](https://github.com/VrtxOmega/omega-brain-mcp) — cross-session episodic memory + 10-gate VERITAS Build pipeline. Together they form the sovereign intelligence stack.

## License

MIT

---

<div align="center">
  <sub>Built by <a href="https://github.com/VrtxOmega">RJ Lopez</a> | VERITAS Omega Framework</sub>
</div>
