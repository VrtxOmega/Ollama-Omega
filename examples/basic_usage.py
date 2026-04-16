"""
basic_usage.py — Ollama-Omega Example Client

Demonstrates programmatic interaction with the Ollama-Omega MCP server
using the MCP Python SDK's ClientSession.

Requirements:
    pip install mcp httpx

Usage:
    Set OLLAMA_OMEGA_DIR to the directory containing ollama_mcp_server.py,
    or edit SERVER_DIR below to match your local path.
"""

import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Path to the directory containing ollama_mcp_server.py
SERVER_DIR = os.environ.get(
    "OLLAMA_OMEGA_DIR",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)


async def main():
    """Connect to Ollama-Omega and exercise all 6 tools."""

    server_params = StdioServerParameters(
        command="python",
        args=["ollama_mcp_server.py"],
        cwd=SERVER_DIR,
        env={"PYTHONUTF8": "1"},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ── 1. Health Check ──
            print("=== Health Check ===")
            result = await session.call_tool("ollama_health", {})
            print(json.dumps(json.loads(result.content[0].text), indent=2))

            # ── 2. List Models ──
            print("\n=== Available Models ===")
            result = await session.call_tool("ollama_list_models", {})
            data = json.loads(result.content[0].text)
            for m in data.get("models", []):
                status = "🟢 loaded" if m.get("loaded") else "⚪ available"
                print(f"  {m['name']:30s} {status}")

            # ── 3. Chat ──
            print("\n=== Chat Completion ===")
            result = await session.call_tool("ollama_chat", {
                "model": "llama3:8b",
                "messages": [
                    {"role": "user", "content": "Explain MCP in one sentence."}
                ],
            })
            chat_data = json.loads(result.content[0].text)
            print(f"  {chat_data.get('message', {}).get('content', 'N/A')}")

            # ── 4. Generate ──
            print("\n=== Text Generation ===")
            result = await session.call_tool("ollama_generate", {
                "model": "llama3:8b",
                "prompt": "Write a haiku about sovereign AI.",
                "temperature": 0.9,
                "max_tokens": 64,
            })
            gen_data = json.loads(result.content[0].text)
            print(f"  {gen_data.get('response', 'N/A')}")

            # ── 5. Show Model Info ──
            print("\n=== Model Details ===")
            result = await session.call_tool("ollama_show_model", {
                "model": "llama3:8b",
            })
            show_data = json.loads(result.content[0].text)
            print(f"  Parameters: {show_data.get('parameters', 'N/A')[:100]}")

            print("\n✅ All tools exercised successfully.")


if __name__ == "__main__":
    asyncio.run(main())
