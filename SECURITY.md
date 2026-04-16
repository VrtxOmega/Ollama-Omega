# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x (latest) | Yes |
| < 1.0.0 | No |

---

## Reporting a Vulnerability

Do not open a public GitHub issue for security vulnerabilities.

Report security issues privately via GitHub's Security Advisories feature:
[github.com/VrtxOmega/Ollama-Omega/security/advisories/new](https://github.com/VrtxOmega/Ollama-Omega/security/advisories/new)

Include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce.
- Any suggested remediation.

You will receive a response within 72 hours. Confirmed vulnerabilities will be patched in the next release and disclosed in `CHANGELOG.md` under a `Security` heading.

---

## Threat Scope

Ollama-Omega is a stdio-transport MCP server. Its attack surface is intentionally narrow.

**In scope:**

- Prompt injection through MCP tool arguments reaching the Ollama daemon.
- SSRF via `OLLAMA_HOST` manipulation (mitigated: `follow_redirects=False` on the httpx client).
- Information leakage through error messages (mitigated: `_error()` sanitization helper).
- Dependency vulnerabilities in `mcp` or `httpx`.

**Out of scope (handled by the host OS or upstream operators):**

- Compromised host OS or stolen credentials.
- Network-level attacks against the Ollama daemon.
- Content policy violations in model outputs — enforcement is the responsibility of the upstream operator (`omega-brain-mcp`).
- Authentication between the MCP client and this server — MCP stdio transport is inherently scoped to the local process boundary.
