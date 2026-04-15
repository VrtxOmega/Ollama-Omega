# Ollama MCP Server — Build Specification
## For: Qwen 3.5 397B to implement

---

## 1. WHAT THIS IS

A single-file Python MCP (Model Context Protocol) server that bridges any Ollama model
(local or cloud) into the Antigravity IDE as callable tools. It runs as a stdio-based
MCP server, identical in pattern to the existing `omega-brain-mcp` server at
`c:\Veritas_Lab\omega-brain-mcp\omega_brain_mcp_standalone.py`.

**File:** `c:\Veritas_Lab\ollama-mcp\ollama_mcp_server.py`
**Single file. No external dependencies beyond `mcp` and `httpx`.**

---

## 2. ENVIRONMENT CONTEXT

### How Antigravity discovers MCP servers

The IDE reads `C:\Users\rlope\.gemini\antigravity\mcp_config.json`. After you build the
server, add this entry:

```json
{
  "mcpServers": {
    "ollama": {
      "command": "uv",
      "args": [
        "--directory",
        "c:\\Veritas_Lab\\ollama-mcp",
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

### How MCP servers work (stdio transport)

- The server communicates over **stdin/stdout** using JSON-RPC 2.0 (MCP protocol).
- Use the `mcp` Python package: `pip install mcp`
- The server registers **tools** that the IDE can invoke.
- Each tool call receives JSON arguments and returns JSON results.

### Ollama REST API (the backend you're hitting)

Base URL: `http://localhost:11434` (configurable via `OLLAMA_HOST` env var)

Key endpoints:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tags` | GET | List all available models |
| `/api/show` | POST | Get model details (params, template, families) |
| `/api/generate` | POST | Text generation (non-chat) |
| `/api/chat` | POST | Chat completion (messages array) |
| `/api/pull` | POST | Pull/download a model |
| `/api/ps` | GET | List running models |
| `/` | GET | Health check (returns "Ollama is running") |

### Models the user wants to access

These are **Ollama Cloud** models (routed through the local Ollama daemon after `ollama login`):
- `qwen3.5:397b-cloud`
- `qwen3.5:122b-cloud`
- `deepseek-v3.1:671b-cloud`
- `glm-5.1:cloud`
- `nemotron-3-super:120b-cloud`

Plus any local models already pulled (e.g., `qwen2.5:7b`, `llama3.2:3b`, etc.)

---

## 3. REQUIRED TOOLS (MCP tool definitions)

### Tool 1: `ollama_list_models`
**Purpose:** List all available models (local + cloud)
**Arguments:** None
**Returns:** JSON array of model objects with: name, size, modified_at, family, parameter_size, quantization
**Implementation:** `GET /api/tags` -> parse response -> return model list
**Also call:** `GET /api/ps` -> merge in "currently loaded" status

### Tool 2: `ollama_chat`
**Purpose:** Send a chat message to any Ollama model and get a response
**Arguments:**
- `model` (string, required): Model name, e.g. "qwen3.5:397b-cloud"
- `messages` (array, required): Array of `{role: "user"|"assistant"|"system", content: string}`
- `temperature` (float, optional, default 0.7): Sampling temperature
- `max_tokens` (int, optional, default -1): Max tokens to generate (-1 = unlimited)
- `system` (string, optional): System prompt (prepended as system message)
- `stream` (bool, optional, default false): Whether to stream (for MCP, always false - collect full response)
**Returns:** JSON with: model, response (full text), eval_count (tokens generated), eval_duration (nanoseconds), total_duration, prompt_eval_count
**Implementation:** `POST /api/chat` with `stream: false` -> return the full response object

### Tool 3: `ollama_generate`
**Purpose:** Raw text generation (non-chat, for completions/code gen)
**Arguments:**
- `model` (string, required)
- `prompt` (string, required)
- `temperature` (float, optional, default 0.7)
- `max_tokens` (int, optional, default -1)
- `system` (string, optional)
**Returns:** JSON with: model, response (full text), eval metrics
**Implementation:** `POST /api/generate` with `stream: false`

### Tool 4: `ollama_show_model`
**Purpose:** Get detailed info about a specific model
**Arguments:**
- `model` (string, required)
**Returns:** JSON with: modelfile, parameters, template, details (family, parameter_size, quantization), model_info
**Implementation:** `POST /api/show`

### Tool 5: `ollama_pull_model`
**Purpose:** Pull/download a model from registry
**Arguments:**
- `model` (string, required): Model to pull, e.g. "qwen3.5:397b-cloud"
**Returns:** JSON with: status, digest (when complete)
**Implementation:** `POST /api/pull` with `stream: false` (may take a while for cloud auth)

### Tool 6: `ollama_health`
**Purpose:** Check Ollama server connectivity and status
**Arguments:** None
**Returns:** JSON with: status ("connected"|"disconnected"), host, running_models (from /api/ps), version
**Implementation:** `GET /`, `GET /api/ps`, return status

---

## 4. CODE STRUCTURE (follow this exactly)

```python
#!/usr/bin/env python3
"""
Ollama MCP Server - Sovereign Ollama Bridge for Antigravity IDE
================================================================
Bridges any Ollama model (local or cloud) into the IDE as MCP tools.
Single file. Two deps: mcp, httpx.

Install:
    pip install mcp httpx

Run (add to mcp_config.json):
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
          "env": { "PYTHONUTF8": "1", "OLLAMA_HOST": "http://localhost:11434" }
        }
      }
    }
"""

import os
import json
import logging
import httpx
from datetime import datetime, timezone
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# -- CONFIG --
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
REQUEST_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "300"))  # 5 min for cloud models

log = logging.getLogger("OllamaMCP")

# -- HTTP CLIENT --
# Use httpx for async HTTP. Create a module-level client.
# Set timeout high because cloud model inference can take 60-180s.

_client = httpx.AsyncClient(
    base_url=OLLAMA_HOST,
    timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=10.0),
)

# -- HELPER: call Ollama API --

async def _ollama_get(path: str) -> dict:
    """GET request to Ollama API."""
    resp = await _client.get(path)
    resp.raise_for_status()
    return resp.json()

async def _ollama_post(path: str, body: dict) -> dict:
    """POST request to Ollama API."""
    resp = await _client.post(path, json=body)
    resp.raise_for_status()
    return resp.json()

# -- TOOL IMPLEMENTATIONS --
# Each function takes the parsed arguments dict and returns a result dict.

async def _list_models() -> dict:
    """Implement ollama_list_models."""
    # ... GET /api/tags, GET /api/ps, merge, return

async def _chat(model: str, messages: list, **kwargs) -> dict:
    """Implement ollama_chat."""
    # ... POST /api/chat with stream=false, return full response

async def _generate(model: str, prompt: str, **kwargs) -> dict:
    """Implement ollama_generate."""
    # ... POST /api/generate with stream=false, return full response

async def _show_model(model: str) -> dict:
    """Implement ollama_show_model."""
    # ... POST /api/show

async def _pull_model(model: str) -> dict:
    """Implement ollama_pull_model."""
    # ... POST /api/pull with stream=false

async def _health() -> dict:
    """Implement ollama_health."""
    # ... GET /, GET /api/ps, return status

# -- MCP SERVER SETUP --

app = Server("ollama")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="ollama_list_models",
            description="List all available Ollama models (local + cloud). Returns name, size, family, quantization, and whether currently loaded.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="ollama_chat",
            description="Send a chat message to any Ollama model. Supports local and cloud models including Qwen 3.5 397B, DeepSeek V3.1 671B, etc. Returns the full response with token metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Model name, e.g. 'qwen3.5:397b-cloud'"},
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                "content": {"type": "string"},
                            },
                        },
                        "description": "Chat messages array",
                    },
                    "temperature": {"type": "number", "default": 0.7},
                    "max_tokens": {"type": "integer", "default": -1},
                    "system": {"type": "string", "description": "System prompt"},
                },
                "required": ["model", "messages"],
            },
        ),
        Tool(
            name="ollama_generate",
            description="Raw text generation (non-chat) with any Ollama model. Use for completions, code generation, or single-shot prompts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string"},
                    "prompt": {"type": "string"},
                    "temperature": {"type": "number", "default": 0.7},
                    "max_tokens": {"type": "integer", "default": -1},
                    "system": {"type": "string"},
                },
                "required": ["model", "prompt"],
            },
        ),
        Tool(
            name="ollama_show_model",
            description="Get detailed information about a specific Ollama model: parameters, template, families, quantization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string"},
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="ollama_pull_model",
            description="Pull/download a model from the Ollama registry. Use for cloud models after 'ollama login'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Model to pull, e.g. 'qwen3.5:397b-cloud'"},
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="ollama_health",
            description="Check Ollama server connectivity, running models, and version.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "ollama_list_models":
            result = await _list_models()
        elif name == "ollama_chat":
            result = await _chat(**arguments)
        elif name == "ollama_generate":
            result = await _generate(**arguments)
        elif name == "ollama_show_model":
            result = await _show_model(**arguments)
        elif name == "ollama_pull_model":
            result = await _pull_model(**arguments)
        elif name == "ollama_health":
            result = await _health()
        else:
            result = {"error": f"Unknown tool: {name}"}
    except httpx.ConnectError:
        result = {"error": f"Cannot connect to Ollama at {OLLAMA_HOST}. Is it running?"}
    except httpx.TimeoutException:
        result = {"error": f"Request timed out after {REQUEST_TIMEOUT}s. Cloud models may need longer."}
    except Exception as e:
        result = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

# -- MAIN --

async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 5. CRITICAL IMPLEMENTATION DETAILS

### 5.1 Timeout handling
Cloud models (397B, 671B) can take **60-180 seconds** to respond. The httpx client
MUST have a timeout of at least 300 seconds. The connect timeout can be shorter (10s).

### 5.2 Stream = false
MCP tools return complete responses, not streams. Always set `"stream": false` in
Ollama API calls. The Ollama API will then return a single JSON response with the
complete generation.

### 5.3 Error handling
- `httpx.ConnectError` -> "Ollama not running"
- `httpx.TimeoutException` -> "Timed out, try increasing OLLAMA_TIMEOUT"
- HTTP 404 -> "Model not found, pull it first"
- Wrap ALL tool calls in try/except and return structured error JSON

### 5.4 The chat endpoint body format
```json
{
  "model": "qwen3.5:397b-cloud",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing."}
  ],
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 4096
  }
}
```

### 5.5 The generate endpoint body format
```json
{
  "model": "qwen3.5:397b-cloud",
  "prompt": "Write a Python function that...",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 4096
  }
}
```

### 5.6 Options mapping
- `temperature` -> `options.temperature`
- `max_tokens` -> `options.num_predict` (only if > 0)
- `system` -> prepend as system message in chat, or use `system` field in generate

---

## 6. REGISTRATION (mcp_config.json)

After building, add to `C:\Users\rlope\.gemini\antigravity\mcp_config.json`:

```json
"ollama": {
  "command": "uv",
  "args": [
    "--directory",
    "c:\\Veritas_Lab\\ollama-mcp",
    "run",
    "python",
    "ollama_mcp_server.py"
  ],
  "env": {
    "PYTHONUTF8": "1",
    "OLLAMA_HOST": "http://localhost:11434"
  }
}
```

Then restart the IDE.

---

## 7. DEPENDENCIES

```
pip install mcp httpx
```

That's it. Two packages. Both are pure Python, no native compilation needed.

---

## 8. TESTING

After building, test with:

```bash
# 1. Verify Ollama is running
curl http://localhost:11434

# 2. Test the MCP server standalone (it reads/writes JSON-RPC on stdio)
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python ollama_mcp_server.py

# 3. After registering in mcp_config.json and restarting IDE:
#    - The tools should appear in Antigravity's tool list
#    - Call ollama_health to verify connectivity
#    - Call ollama_list_models to see available models
#    - Call ollama_chat with model="qwen3.5:397b-cloud" to test cloud inference
```

---

## 9. WHAT NOT TO DO

- Do NOT use `requests` -- use `httpx` (async-native, matches the async MCP server)
- Do NOT stream responses -- MCP tools return complete results
- Do NOT hardcode model names -- accept any model string the user provides
- Do NOT add unnecessary dependencies -- keep it to `mcp` + `httpx`
- Do NOT use `subprocess` or shell commands -- HTTP only
- Do NOT log secrets or auth tokens
- Do NOT add a venv auto-activation shim -- keep it simple
