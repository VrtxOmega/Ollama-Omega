"""
test_server.py — Ollama-Omega MCP Server Test Suite

Tests tool definitions, dispatcher logic, helpers, error handling,
and configuration without requiring a live Ollama instance.
"""

import json
import os
import sys
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure the server module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama_mcp_server as server


def _run(coro):
    """Run an async coroutine in a fresh event loop (Python 3.10-3.14 safe)."""
    return asyncio.run(coro)


# ── Tool Definition Tests ──────────────────────────────────────


class TestToolDefinitions(unittest.TestCase):
    """Verify all 6 tools are declared with correct schemas."""

    def test_tool_count(self):
        """Exactly 6 tools must be registered."""
        self.assertEqual(len(server.TOOLS), 6)

    def test_tool_names(self):
        """All expected tool names exist."""
        names = {t.name for t in server.TOOLS}
        expected = {
            "ollama_health",
            "ollama_list_models",
            "ollama_chat",
            "ollama_generate",
            "ollama_show_model",
            "ollama_pull_model",
        }
        self.assertEqual(names, expected)

    def test_all_tools_have_schemas(self):
        """Every tool must have a valid inputSchema with 'type': 'object'."""
        for tool in server.TOOLS:
            self.assertIn("type", tool.inputSchema, f"{tool.name} missing schema type")
            self.assertEqual(tool.inputSchema["type"], "object", f"{tool.name} schema type not 'object'")

    def test_chat_required_fields(self):
        """ollama_chat must require 'model' and 'messages'."""
        chat_tool = next(t for t in server.TOOLS if t.name == "ollama_chat")
        self.assertIn("required", chat_tool.inputSchema)
        self.assertIn("model", chat_tool.inputSchema["required"])
        self.assertIn("messages", chat_tool.inputSchema["required"])

    def test_generate_required_fields(self):
        """ollama_generate must require 'model' and 'prompt'."""
        gen_tool = next(t for t in server.TOOLS if t.name == "ollama_generate")
        self.assertIn("required", gen_tool.inputSchema)
        self.assertIn("model", gen_tool.inputSchema["required"])
        self.assertIn("prompt", gen_tool.inputSchema["required"])

    def test_show_model_required_fields(self):
        """ollama_show_model must require 'model'."""
        show_tool = next(t for t in server.TOOLS if t.name == "ollama_show_model")
        self.assertIn("model", show_tool.inputSchema["required"])

    def test_pull_model_required_fields(self):
        """ollama_pull_model must require 'model'."""
        pull_tool = next(t for t in server.TOOLS if t.name == "ollama_pull_model")
        self.assertIn("model", pull_tool.inputSchema["required"])

    def test_health_no_required_fields(self):
        """ollama_health has no required fields."""
        health_tool = next(t for t in server.TOOLS if t.name == "ollama_health")
        self.assertNotIn("required", health_tool.inputSchema)

    def test_list_models_no_required_fields(self):
        """ollama_list_models has no required fields."""
        list_tool = next(t for t in server.TOOLS if t.name == "ollama_list_models")
        self.assertNotIn("required", list_tool.inputSchema)

    def test_all_tools_have_descriptions(self):
        """Every tool must have a non-empty description."""
        for tool in server.TOOLS:
            self.assertTrue(len(tool.description) > 10, f"{tool.name} description too short")


# ── Helper Function Tests ──────────────────────────────────────


class TestHelpers(unittest.TestCase):
    """Test utility functions used by the dispatcher."""

    def test_build_options_temperature(self):
        """Temperature should pass through to options."""
        opts = server._build_options({"temperature": 0.7})
        self.assertEqual(opts["temperature"], 0.7)

    def test_build_options_max_tokens(self):
        """max_tokens should map to num_predict."""
        opts = server._build_options({"max_tokens": 1024})
        self.assertEqual(opts["num_predict"], 1024)

    def test_build_options_zero_tokens_ignored(self):
        """max_tokens=0 should not produce num_predict."""
        opts = server._build_options({"max_tokens": 0})
        self.assertNotIn("num_predict", opts)

    def test_build_options_negative_tokens_ignored(self):
        """Negative max_tokens should not produce num_predict."""
        opts = server._build_options({"max_tokens": -1})
        self.assertNotIn("num_predict", opts)

    def test_build_options_empty(self):
        """Empty arguments should return empty options."""
        opts = server._build_options({})
        self.assertEqual(opts, {})

    def test_build_options_both(self):
        """Both temperature and max_tokens should co-exist."""
        opts = server._build_options({"temperature": 0.5, "max_tokens": 512})
        self.assertEqual(opts["temperature"], 0.5)
        self.assertEqual(opts["num_predict"], 512)

    def test_validate_required_pass(self):
        """All required keys present should return None."""
        result = server._validate_required({"model": "x", "prompt": "y"}, "model", "prompt")
        self.assertIsNone(result)

    def test_validate_required_missing(self):
        """Missing key should return error string."""
        result = server._validate_required({"model": "x"}, "model", "prompt")
        self.assertIn("prompt", result)

    def test_validate_required_none_value(self):
        """None value for required key should return error string."""
        result = server._validate_required({"model": None}, "model")
        self.assertIn("model", result)

    def test_safe_json_valid(self):
        """Valid JSON response should parse correctly."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "ok"}
        result = server._safe_json(mock_resp)
        self.assertEqual(result["status"], "ok")

    def test_safe_json_invalid(self):
        """Invalid JSON should return error dict, not crash."""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = json.JSONDecodeError("", "", 0)
        mock_resp.text = "not json at all"
        result = server._safe_json(mock_resp)
        self.assertIn("error", result)
        self.assertIn("raw", result)

    def test_safe_json_truncates_long_raw(self):
        """Raw text in error should be truncated to 500 chars max."""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError()
        mock_resp.text = "x" * 1000
        result = server._safe_json(mock_resp)
        self.assertLessEqual(len(result["raw"]), 500)

    def test_error_returns_text_content(self):
        """_error() should return a list with one TextContent."""
        result = server._error("test error")
        self.assertEqual(len(result), 1)
        parsed = json.loads(result[0].text)
        self.assertEqual(parsed["error"], "test error")

    def test_error_with_extra_fields(self):
        """_error() should include extra keyword arguments."""
        result = server._error("fail", status_code=404)
        parsed = json.loads(result[0].text)
        self.assertEqual(parsed["status_code"], 404)

    def test_ok_returns_text_content(self):
        """_ok() should return a list with one TextContent."""
        result = server._ok({"models": []})
        self.assertEqual(len(result), 1)
        parsed = json.loads(result[0].text)
        self.assertEqual(parsed["models"], [])


# ── Dispatcher Tests (Mocked HTTP) ─────────────────────────────


class TestDispatcher(unittest.TestCase):
    """Test the call_tool dispatcher with mocked httpx responses."""

    def _mock_response(self, data, status_code=200):
        """Build a mock httpx.Response."""
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = data
        mock.text = json.dumps(data)
        mock.raise_for_status = MagicMock()
        return mock

    @patch.object(server, "_client")
    def test_unknown_tool(self, mock_client):
        """Unknown tool name should return error, not crash."""
        result = _run(server.call_tool("nonexistent_tool", {}))
        parsed = json.loads(result[0].text)
        self.assertIn("error", parsed)
        self.assertIn("Unknown tool", parsed["error"])

    @patch.object(server, "_client")
    def test_chat_missing_model(self, mock_client):
        """ollama_chat without model should return validation error."""
        result = _run(server.call_tool("ollama_chat", {"messages": []}))
        parsed = json.loads(result[0].text)
        self.assertIn("error", parsed)
        self.assertIn("model", parsed["error"])

    @patch.object(server, "_client")
    def test_chat_missing_messages(self, mock_client):
        """ollama_chat without messages should return validation error."""
        result = _run(server.call_tool("ollama_chat", {"model": "test"}))
        parsed = json.loads(result[0].text)
        self.assertIn("error", parsed)
        self.assertIn("messages", parsed["error"])

    @patch.object(server, "_client")
    def test_generate_missing_prompt(self, mock_client):
        """ollama_generate without prompt should return validation error."""
        result = _run(server.call_tool("ollama_generate", {"model": "test"}))
        parsed = json.loads(result[0].text)
        self.assertIn("error", parsed)

    @patch.object(server, "_client")
    def test_show_model_missing_model(self, mock_client):
        """ollama_show_model without model should return validation error."""
        result = _run(server.call_tool("ollama_show_model", {}))
        parsed = json.loads(result[0].text)
        self.assertIn("error", parsed)

    @patch.object(server, "_client")
    def test_pull_model_missing_model(self, mock_client):
        """ollama_pull_model without model should return validation error."""
        result = _run(server.call_tool("ollama_pull_model", {}))
        parsed = json.loads(result[0].text)
        self.assertIn("error", parsed)

    @patch.object(server, "_client")
    def test_health_success(self, mock_client):
        """ollama_health should return connectivity info."""
        mock_client.get = AsyncMock(side_effect=[
            self._mock_response("Ollama is running"),  # GET /
            self._mock_response({"models": [{"name": "llama3:8b"}]}),  # GET /api/ps
        ])
        result = _run(server.call_tool("ollama_health", {}))
        parsed = json.loads(result[0].text)
        self.assertTrue(parsed["connected"])
        self.assertEqual(parsed["host"], server.OLLAMA_HOST)

    @patch.object(server, "_client")
    def test_list_models_success(self, mock_client):
        """ollama_list_models should merge tags and ps data."""
        mock_client.get = AsyncMock(side_effect=[
            self._mock_response({"models": [
                {"name": "llama3:8b", "size": 4_000_000_000, "modified_at": "2025-01-01"},
                {"name": "qwen3:8b", "size": 5_000_000_000, "modified_at": "2025-02-01"},
            ]}),
            self._mock_response({"models": [{"name": "llama3:8b"}]}),
        ])
        result = _run(server.call_tool("ollama_list_models", {}))
        parsed = json.loads(result[0].text)
        models = parsed["models"]
        self.assertEqual(len(models), 2)
        llama = next(m for m in models if m["name"] == "llama3:8b")
        qwen = next(m for m in models if m["name"] == "qwen3:8b")
        self.assertTrue(llama["loaded"])
        self.assertFalse(qwen["loaded"])

    @patch.object(server, "_client")
    def test_chat_success(self, mock_client):
        """ollama_chat should post to /api/chat and return response."""
        mock_client.post = AsyncMock(return_value=self._mock_response({
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True,
        }))
        result = _run(server.call_tool("ollama_chat", {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hi"}],
        }))
        parsed = json.loads(result[0].text)
        self.assertEqual(parsed["message"]["content"], "Hello!")
        call_args = mock_client.post.call_args
        self.assertEqual(call_args[0][0], "/api/chat")

    @patch.object(server, "_client")
    def test_chat_with_system_prompt(self, mock_client):
        """System prompt should be injected as messages[0]."""
        mock_client.post = AsyncMock(return_value=self._mock_response({"done": True}))
        _run(server.call_tool("ollama_chat", {
            "model": "test",
            "messages": [{"role": "user", "content": "Hi"}],
            "system": "You are a pirate."
        }))
        call_args = mock_client.post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][0]["content"], "You are a pirate.")
        self.assertEqual(payload["messages"][1]["role"], "user")

    @patch.object(server, "_client")
    def test_generate_success(self, mock_client):
        """ollama_generate should post to /api/generate."""
        mock_client.post = AsyncMock(return_value=self._mock_response({
            "response": "The answer is 42.",
            "done": True,
        }))
        result = _run(server.call_tool("ollama_generate", {
            "model": "test-model",
            "prompt": "What is the answer?",
        }))
        parsed = json.loads(result[0].text)
        self.assertEqual(parsed["response"], "The answer is 42.")

    @patch.object(server, "_client")
    def test_generate_with_options(self, mock_client):
        """Temperature and max_tokens should be sent as options."""
        mock_client.post = AsyncMock(return_value=self._mock_response({"done": True}))
        _run(server.call_tool("ollama_generate", {
            "model": "test",
            "prompt": "Hello",
            "temperature": 0.3,
            "max_tokens": 256,
        }))
        payload = mock_client.post.call_args[1]["json"]
        self.assertEqual(payload["options"]["temperature"], 0.3)
        self.assertEqual(payload["options"]["num_predict"], 256)

    @patch.object(server, "_client")
    def test_show_model_success(self, mock_client):
        """ollama_show_model should post to /api/show."""
        mock_client.post = AsyncMock(return_value=self._mock_response({
            "modelfile": "FROM llama3:8b",
            "parameters": "num_ctx 4096",
        }))
        result = _run(server.call_tool("ollama_show_model", {"model": "llama3:8b"}))
        parsed = json.loads(result[0].text)
        self.assertIn("modelfile", parsed)

    @patch.object(server, "_client")
    def test_pull_model_success(self, mock_client):
        """ollama_pull_model should post to /api/pull with stream=False."""
        mock_client.post = AsyncMock(return_value=self._mock_response({"status": "success"}))
        result = _run(server.call_tool("ollama_pull_model", {"model": "llama3:8b"}))
        parsed = json.loads(result[0].text)
        self.assertEqual(parsed["status"], "success")
        payload = mock_client.post.call_args[1]["json"]
        self.assertFalse(payload["stream"])


# ── Error Handling Tests ───────────────────────────────────────


class TestErrorHandling(unittest.TestCase):
    """Test graceful error handling for network and server failures."""

    @patch.object(server, "_client")
    def test_connection_error(self, mock_client):
        """ConnectError should return friendly error, not crash."""
        import httpx
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        result = _run(server.call_tool("ollama_health", {}))
        parsed = json.loads(result[0].text)
        self.assertIn("Connection Failed", parsed["error"])

    @patch.object(server, "_client")
    def test_timeout_error(self, mock_client):
        """TimeoutException should return timeout message."""
        import httpx
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
        result = _run(server.call_tool("ollama_chat", {
            "model": "test", "messages": [{"role": "user", "content": "Hi"}]
        }))
        parsed = json.loads(result[0].text)
        self.assertIn("Timeout", parsed["error"])

    @patch.object(server, "_client")
    def test_http_status_error(self, mock_client):
        """HTTP 4xx/5xx should return sanitized error, not stack trace."""
        import httpx
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "model not found"
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=mock_resp
        )
        result = _run(server.call_tool("ollama_generate", {
            "model": "nonexistent", "prompt": "test"
        }))
        parsed = json.loads(result[0].text)
        self.assertIn("HTTP Error", parsed["error"])
        self.assertEqual(parsed["status_code"], 404)

    @patch.object(server, "_client")
    def test_unexpected_exception_sanitized(self, mock_client):
        """Unexpected exception should not leak internals."""
        mock_client.get = AsyncMock(side_effect=RuntimeError("something broke inside"))
        result = _run(server.call_tool("ollama_health", {}))
        parsed = json.loads(result[0].text)
        self.assertEqual(parsed["error"], "Internal server error")
        # Must NOT contain the actual error message
        self.assertNotIn("something broke inside", result[0].text)


# ── Configuration Tests ────────────────────────────────────────


class TestConfiguration(unittest.TestCase):
    """Test environment variable handling and defaults."""

    def test_default_host(self):
        """Default OLLAMA_HOST should be localhost:11434."""
        self.assertEqual(server.OLLAMA_HOST, os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    def test_default_timeout(self):
        """Default timeout should be 300s."""
        default_timeout = float(os.getenv("OLLAMA_TIMEOUT", "300"))
        self.assertEqual(server.REQUEST_TIMEOUT, default_timeout)

    def test_client_no_redirects(self):
        """SSRF mitigation: client must NOT follow redirects."""
        self.assertFalse(server._client.follow_redirects)

    def test_server_name(self):
        """Server should be named 'ollama'."""
        self.assertEqual(server.app.name, "ollama")


# ── List Tools Handler Test ────────────────────────────────────


class TestListToolsHandler(unittest.TestCase):
    """Test the MCP list_tools handler."""

    def test_list_tools_returns_all_tools(self):
        """list_tools() should return the TOOLS list."""
        result = _run(server.list_tools())
        self.assertEqual(len(result), 6)
        self.assertEqual(result, server.TOOLS)


if __name__ == "__main__":
    unittest.main()
