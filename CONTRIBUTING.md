# Contributing to Ollama-Omega

Ollama-Omega is a single-file MCP server. Contributions are welcome and held to a high standard of correctness.

---

## Ground Rules

- **No behavior changes without tests.** The test suite in `tests/test_server.py` covers 48 cases. Any change to `ollama_mcp_server.py` must maintain or extend this coverage.
- **No new dependencies** without a clear rationale. The two-dependency constraint (`mcp`, `httpx`) is a design principle, not an oversight.
- **Documentation changes** (README, CHANGELOG, inline docstrings) are always welcome and do not require a test.

---

## Workflow

1. Fork the repository and create a feature branch from `master`.
2. Make your changes.
3. Run the test suite:
   ```bash
   pip install pytest mcp httpx
   python -m pytest tests/ -v
   ```
4. Update `CHANGELOG.md` with a summary of your change under the appropriate version heading.
5. Open a pull request against `master` with a clear description of the change and its rationale.

---

## Code Style

- Python 3.11+. Type hints are encouraged but not required.
- All tool definitions must include an `outputSchema` and `ToolAnnotations`.
- Error paths must use `_error()`. Success paths must use `_ok()`.
- Structured logging via the `logging` module. No bare `print()` to stdout.

---

## Reporting Issues

Open a GitHub issue. Include:

- The tool name and arguments that triggered the issue.
- The error message or unexpected output (sanitize any sensitive data).
- Your Python version, OS, and Ollama daemon version (`ollama --version`).
