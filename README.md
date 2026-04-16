<div align="center">

# OLLAMA-OMEGA

**MCP server — Ollama bridge for any IDE. Sovereign compute. No cloud dependency.**

</div>

![Status](https://img.shields.io/badge/Status-ACTIVE-success?style=for-the-badge&labelColor=000000&color=d4af37)
![Version](https://img.shields.io/badge/Version-v1.0.5-blue?style=for-the-badge&labelColor=000000)
![Stack](https://img.shields.io/badge/Stack-Python%20%2B%20MCP-informational?style=for-the-badge&labelColor=000000)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&labelColor=000000)
![Tests](https://img.shields.io/badge/Tests-48%20passed-success?style=for-the-badge&labelColor=000000)

<a href="https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega"><img width="380" height="200" src="https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega/badges/card.svg" alt="Ollama-Omega MCP server" /></a>

[![Ollama-Omega MCP server](https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega/badges/score.svg)](https://glama.ai/mcp/servers/VrtxOmega/Ollama-Omega)

---

## Ecosystem Canon

Ollama-Omega is the compute interface layer of the VERITAS & Sovereign Ecosystem (Omega Universe). It surfaces every locally installed Ollama model — and any cloud-hosted model accessible through an Ollama daemon — as a structured MCP tool set inside any MCP-compatible IDE or agent runtime.

Within the Omega Universe, governance flows downward from `omega-brain-mcp` (the VERITAS gate and approval pipeline) to `Ollama-Omega` (the inference transport). Ollama-Omega is the final execution node: it issues the prompt, receives model output, and returns a validated, schema-typed response. No inference executes before the upstream gate approves the request.

Ollama-Omega does not perform memory, authentication, persistence, or policy enforcement. Those responsibilities belong to the operators above it in the stack. This node does one thing: connect IDE to Ollama, reliably and without information loss.

---

## Overview

**What it is:**

- A single-file MCP server (`ollama_mcp_server.py`) that bridges Ollama into any MCP-compatible client
- Six validated tools covering health, model listing, chat, generation, model inspection, and model pull
- Compatible with Claude Desktop, VS Code + Continue, Cursor, Antigravity IDE, and any other client that speaks MCP over stdio

**What it is not:**

- A full AI platform, memory layer, or policy engine
- A replacement for the Ollama daemon — it wraps the daemon's HTTP API over MCP stdio transport
- A cloud service — all inference is local or routed through your own Ollama daemon

---

## Features

| Feature | Detail |
|---------|--------|
| 6 MCP tools | Health check, list models, chat, generate, show model info, pull model |
| Stdio transport | JSON-RPC 2.0 over stdin/stdout — no network ports opened by this server |
| Typed output schemas | Every tool carries a full `outputSchema` for structured agent consumption |
| SSRF mitigation | `follow_redirects=False` on the singleton httpx client |
| Input validation | `_validate_required()` gate before any HTTP call; no uncaught `KeyError` |
| Safe JSON handling | `_safe_json()` wrapper — no crash on malformed Ollama responses |
| Error sanitization | `_error()` helper — no stack traces, no internals exposed to the client |
| Cloud model support | Any model accessible on your Ollama daemon is available — no config change required |
| Docker-ready | `Dockerfile` included for containerized deployment |

---

## Architecture

```
  IDE / MCP Client
  (Claude Desktop, VS Code + Continue, Cursor, Antigravity, ...)
         |
         |  stdio  JSON-RPC 2.0
         v
  +-----------------------------+
  |    ollama_mcp_server.py     |
  |  Validator  |   Dispatch    |
  |  Singleton httpx AsyncClient|
  +-----------------------------+
         |
         |  HTTP  (default: http://localhost:11434)
         v
  +-----------------------------+
  |       Ollama Daemon         |
  |  Local models  (GPU / CPU)  |
  |  Cloud proxy models         |
  +-----------------------------+
         |
         v
  Local model store
  (~/.ollama/models)
```

The server process lives for the lifetime of the IDE session. One httpx `AsyncClient` handles all upstream Ollama HTTP traffic. The MCP client never communicates with Ollama directly.

---

## Quickstart

### Prerequisites

- **Python 3.11 or later**
- **Ollama daemon installed and running**

#### Install Ollama

| Platform | Method |
|----------|--------|
| **Windows** | Download the installer from [ollama.com/download/windows](https://ollama.com/download/windows) and run it. Ollama starts automatically as a system tray service. |
| **macOS** | Download from [ollama.com/download/mac](https://ollama.com/download/mac), or via Homebrew: `brew install ollama && ollama serve` |
| **Linux** | `curl -fsSL https://ollama.com/install.sh \| sh` — starts the daemon via systemd on supported distributions |

Verify the daemon is reachable before proceeding:

```bash
curl http://localhost:11434
# Expected response: Ollama is running
```

---

### Install Ollama-Omega

**Option A — pip (simplest):**

```bash
pip install mcp httpx
```

Then download the server file:

```bash
# macOS / Linux
curl -O https://raw.githubusercontent.com/VrtxOmega/Ollama-Omega/master/ollama_mcp_server.py

# Windows (PowerShell)
Invoke-WebRequest -Uri https://raw.githubusercontent.com/VrtxOmega/Ollama-Omega/master/ollama_mcp_server.py -OutFile ollama_mcp_server.py
```

**Option B — clone the repository (recommended for local development):**

```bash
git clone https://github.com/VrtxOmega/Ollama-Omega.git
cd Ollama-Omega
pip install mcp httpx
```

**Option C — uv (virtual-env isolation, recommended for production):**

```bash
git clone https://github.com/VrtxOmega/Ollama-Omega.git
cd Ollama-Omega
uv sync
```

**Option D — Docker:**

```bash
git clone https://github.com/VrtxOmega/Ollama-Omega.git
cd Ollama-Omega
docker build -t ollama-omega .
# Run with stdio transport for IDE integration:
docker run -i --rm -e OLLAMA_HOST=http://host.docker.internal:11434 ollama-omega
```

---

### Pull a model

```bash
ollama pull llama3.2:3b
```

---

### Configure your MCP client

Edit the configuration file for your IDE and add the `ollama` server block. Replace `/path/to/Ollama-Omega` with the actual path to your clone (or the directory containing `ollama_mcp_server.py`).

#### Claude Desktop

Config file locations:

| Platform | Path |
|----------|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS / Linux | `~/.config/Claude/claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "ollama": {
      "command": "python",
      "args": ["/path/to/Ollama-Omega/ollama_mcp_server.py"],
      "env": {
        "PYTHONUTF8": "1",
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_TIMEOUT": "300"
      }
    }
  }
}
```

With `uv` (virtual-env isolation):

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

#### VS Code + Continue / Cursor

Most MCP-compatible VS Code extensions follow the same JSON structure under their own config key. Substitute the `command` and `args` block from the Claude Desktop example above. Consult your extension's documentation for the exact config file path.

#### Antigravity IDE

Config file: `~/.gemini/antigravity/mcp_config.json`

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

Restart your IDE after saving the configuration file. Verify connectivity by calling the `ollama_health` tool from your IDE.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Base URL of the Ollama daemon. Override to point at a remote or containerized daemon. |
| `OLLAMA_TIMEOUT` | `300` | HTTP request timeout in seconds. Increase for large model pulls or slow cloud inference. |
| `PYTHONUTF8` | _(unset)_ | Set to `1` on Windows to prevent Unicode encoding errors in stdio transport. |

Cloud-hosted models exposed by your Ollama daemon (e.g., `qwen3.5:397b-cloud` via API proxy) are accessible through the same 6 tools with no configuration change. Authenticate first with `ollama login`.

---

## Troubleshooting

**Ollama daemon not running**

```bash
# Start the daemon
ollama serve

# Verify
curl http://localhost:11434
```

If `OLLAMA_HOST` is set to a non-default value, confirm the URL and port match the daemon's bind address.

---

**Port conflict — daemon fails to start**

Ollama binds to port `11434` by default. If that port is occupied:

```bash
# macOS / Linux — find the occupying process
lsof -i :11434

# Windows (PowerShell)
netstat -ano | findstr :11434
```

Set `OLLAMA_HOST` to an alternate port once you have reconfigured the daemon.

---

**Model not found / HTTP 404**

The referenced model has not been pulled. Pull it first:

```bash
ollama pull <model-name>

# Cloud-hosted models require authentication:
ollama login
ollama pull qwen3.5:397b-cloud
```

Alternatively, call `ollama_pull_model` from your IDE once the server is connected.

---

**Tools do not appear in the IDE**

1. Confirm the `command` path resolves to a working Python 3.11+ interpreter.
2. Confirm `mcp` and `httpx` are installed in that interpreter's environment.
3. Restart the IDE — MCP servers are discovered at startup, not while running.
4. Check IDE logs for JSON-RPC handshake errors.

---

**Windows: `UnicodeEncodeError` or garbled output**

Set `PYTHONUTF8=1` in the server's `env` block. This is already shown in the configuration examples above.

---

**Docker: cannot reach `localhost:11434`**

Docker containers run in an isolated network namespace. Replace `localhost` with `host.docker.internal`:

```bash
docker run -i --rm -e OLLAMA_HOST=http://host.docker.internal:11434 ollama-omega
```

On Linux hosts, `--network=host` may be required instead.

---

**Request timed out after 300s**

Cold inference on large models (70B+) or cloud-proxied models can exceed the default timeout. Increase it in your MCP client config:

```json
"env": { "OLLAMA_TIMEOUT": "600" }
```

---

## Security and Sovereignty

Ollama-Omega runs exclusively on `localhost` by default, communicating with the Ollama daemon over the loopback interface. No data leaves the machine unless your Ollama daemon is configured to proxy to a cloud endpoint.

**Hardening applied to this server:**

| Control | Implementation |
|---------|----------------|
| SSRF prevention | `follow_redirects=False` on the httpx singleton |
| Input sanitization | Required-argument validation before any outbound HTTP call |
| Error sanitization | Internal errors are never forwarded to the MCP client |
| Non-root Docker | Container process runs as a dedicated `ollama` user |

**Limitations and out-of-scope items:**

- Authentication between the MCP client and this server is not implemented. MCP stdio transport is inherently scoped to the local process boundary.
- This server does not validate the content of prompts or model outputs. Content policy enforcement is the responsibility of the upstream operator (see `omega-brain-mcp`).
- Network isolation, host-level security, and key management are outside the scope of this component.

---

## Omega Universe

Ollama-Omega is one node in the VERITAS & Sovereign Ecosystem. Cross-references:

| Repository | Role in the stack |
|------------|-------------------|
| [omega-brain-mcp](https://github.com/VrtxOmega/omega-brain-mcp) | VERITAS gate + cryptographic audit ledger + Cortex approval pipeline. The governance layer above Ollama-Omega. |
| [veritas-vault](https://github.com/VrtxOmega/veritas-vault) | Long-term retention substrate. Stores artifacts, attestations, and approved outputs. |
| [Aegis](https://github.com/VrtxOmega/Aegis) | Security enforcement layer. Threat surface scanning and sovereign boundary enforcement. |
| [drift](https://github.com/VrtxOmega/drift) | Drift detection and configuration integrity monitoring across Omega operators. |
| [SovereignMedia](https://github.com/VrtxOmega/SovereignMedia) | Media processing and content pipeline within the Omega framework. |
| [sovereign-arcade](https://github.com/VrtxOmega/sovereign-arcade) | Operator sandbox and demonstration environment for Omega Universe components. |

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
  <sub>Built by <a href="https://github.com/VrtxOmega">RJ Lopez</a> | VERITAS Omega Framework</sub>
</div>
