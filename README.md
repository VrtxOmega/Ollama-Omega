<div align="center">
  <h1>OLLAMA-OMEGA</h1>
  <p><strong>Sovereign Ollama Bridge — MCP Server for Local &amp; Cloud Models</strong></p>
  <p><em>One file. Two deps. Every Ollama model — local or cloud.</em></p>
</div>

![Status](https://img.shields.io/badge/Status-ACTIVE-success?style=for-the-badge&labelColor=000000&color=d4af37)
![Version](https://img.shields.io/badge/Version-v1.0.5-blue?style=for-the-badge&labelColor=000000)
![Stack](https://img.shields.io/badge/Stack-Python%20%2B%20MCP-informational?style=for-the-badge&labelColor=000000)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&labelColor=000000)
![Tests](https://img.shields.io/badge/Tests-48%20passed-success?style=for-the-badge&labelColor=000000)

<a href="https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega"><img width="380" height="200" src="https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega/badges/card.svg" alt="Ollama-Omega MCP server" /></a>

[![Ollama-Omega MCP server](https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega/badges/score.svg)](https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega)

---

## Overview

Ollama-Omega is a hardened [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that bridges the full Ollama ecosystem — local GPU models and cloud-hosted behemoths alike — into any MCP-compatible IDE or agent. No wrapper scripts. No bloated SDK. Just a single Python file with two dependencies.

Born out of necessity when Google Antigravity and Gemini were offline, Ollama-Omega gives you a **sovereign, offline-capable AI stack** that works regardless of cloud availability. Run 400B+ parameter models locally or via Ollama's cloud proxy — same API, same tools, zero configuration changes.

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

### 1. Install Ollama

Download and install Ollama from [ollama.com](https://ollama.com). Verify it is running:

```bash
curl http://localhost:11434
# Expected: Ollama is running
```

### 2. Install Ollama-Omega

**Option A — pip (recommended):**

```bash
pip install mcp httpx
# Then download the server file:
curl -O https://raw.githubusercontent.com/VrtxOmega/Ollama-Omega/master/ollama_mcp_server.py
```

**Option B — clone the repo:**

```bash
git clone https://github.com/VrtxOmega/Ollama-Omega.git
cd Ollama-Omega
pip install mcp httpx
```

**Option C — Docker:**

```bash
docker build -t ollama-omega .
# Run with stdio transport (for IDE integration):
docker run -i --rm -e OLLAMA_HOST=http://host.docker.internal:11434 ollama-omega
```

### 3. Pull a model (if you don't have one)

```bash
ollama pull llama3.2:3b
# Or a cloud model after `ollama login`:
# ollama pull qwen3.5:397b-cloud
```

### 4. Configure your IDE / MCP client

**Claude Desktop** (`~/.config/Claude/claude_desktop_config.json` on macOS/Linux, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "ollama": {
      "command": "python",
      "args": ["/path/to/ollama_mcp_server.py"],
      "env": {
        "PYTHONUTF8": "1",
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_TIMEOUT": "300"
      }
    }
  }
}
```

**With `uv` (virtual-env isolation):**

```json
{
  "mcpServers": {
    "ollama": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/Ollama-Omega",
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

**Antigravity IDE** (`~/.gemini/antigravity/mcp_config.json`):

```json
{
  "mcpServers": {
    "ollama": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/Ollama-Omega",
        "run",
        "python",
        "ollama_mcp_server.py"
      ],
      "env": {
        "PYTHONUTF8": "1",
        "OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

Restart your IDE after saving the config. Verify with the `ollama_health` tool.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama daemon URL |
| `OLLAMA_TIMEOUT` | `300` | Request timeout in seconds (long for large model pulls/cloud inference) |
| `PYTHONUTF8` | — | Set to `1` for Windows Unicode safety |

### Cloud Models

Ollama-Omega is version-agnostic. If your Ollama daemon exposes cloud-hosted models (e.g., `qwen3.5:397b-cloud` via API proxy), they are accessible through the same 6 tools — no configuration change required.

```bash
# Authenticate with Ollama Cloud first:
ollama login
```

## File Structure

```
Ollama-Omega/
  ollama_mcp_server.py     # MCP server — hardened, single-file
  pyproject.toml            # Package metadata, CLI entry, PyPI classifiers
  requirements.txt          # mcp>=1.9.0, httpx>=0.27.0
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
pip install pytest mcp httpx
python -m pytest tests/ -v
```

48 tests covering:
- **Tool Definitions** — schema validation, required fields, descriptions
- **Helper Functions** — options builder, validation, JSON safety, error formatting
- **Dispatcher** — all 6 tool paths with mocked HTTP responses
- **Error Handling** — connection, timeout, HTTP status, exception sanitization
- **Configuration** — environment defaults, SSRF mitigation, server identity

## Troubleshooting

### `ollama_health` returns `connected: false`

The Ollama daemon is not running or is unreachable at the configured host.

```bash
# Start the daemon
ollama serve

# Verify it responds
curl http://localhost:11434
```

If you changed `OLLAMA_HOST`, make sure the URL and port match your daemon config.

---

### `Request timed out after 300s`

Large cloud models (400B+) can take 60–180 s for a cold response. Increase the timeout:

```json
"env": { "OLLAMA_TIMEOUT": "600" }
```

---

### `Model not found` / HTTP 404 from Ollama

The model hasn't been pulled yet. Use `ollama_pull_model` from your IDE or run:

```bash
ollama pull <model-name>
# Cloud models require login first:
ollama login
ollama pull qwen3.5:397b-cloud
```

---

### Tools don't appear in my IDE

1. Confirm the `command` path resolves to a working Python 3.11+ interpreter.
2. Check that `mcp` and `httpx` are installed in that interpreter's environment.
3. Restart the IDE — MCP servers are discovered at startup.
4. Check IDE logs for JSON-RPC errors from the server.

---

### Windows: `UnicodeEncodeError` / garbled output

Set `PYTHONUTF8=1` in the server's `env` block (already shown in the Quick Start config).

---

### Docker: cannot reach `localhost:11434`

Docker containers use their own network namespace. Use `host.docker.internal` instead of `localhost`:

```bash
docker run -i --rm -e OLLAMA_HOST=http://host.docker.internal:11434 ollama-omega
```

On Linux you may need `--network=host` instead.

## Companion Server

Ollama-Omega is the transport layer for the [**Omega Brain MCP**](https://github.com/VrtxOmega/omega-brain-mcp) — cross-session episodic memory + 10-gate VERITAS Build pipeline. Together they form the sovereign intelligence stack.

## License

MIT

---

<div align="center">
  <sub>Built by <a href="https://github.com/VrtxOmega">RJ Lopez</a> | VERITAS Omega Framework</sub>
</div>
