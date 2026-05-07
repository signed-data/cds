# Security Policy

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email: security@wdotnet.com.br  
Response time: within 72 hours for confirmed issues.

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations

We will acknowledge receipt, investigate, and coordinate disclosure timing with you.

## Supported Versions

| Component | Supported |
|-----------|-----------|
| All `signeddata-mcp-*` packages (latest) | ✅ |
| `signeddata-cds` SDK (latest) | ✅ |
| Older releases | ❌ (update to latest) |

## Prompt Injection

All MCP servers in this repository include explicit anti-injection instructions in their `FastMCP` constructor. The servers:

- Only execute their defined data-retrieval tools
- Do not follow instructions embedded in tool arguments or user messages
- Do not override their configured signing behavior
- Do not expose credentials, private keys, or internal state

If you discover a prompt injection vector that bypasses these protections, report it as a security vulnerability.

## PyPI Package Integrity

All packages published to PyPI include [provenance attestations](https://docs.pypi.org/attestations/) signed via GitHub Actions OIDC. Verify before installing:

```bash
pip install signeddata-mcp-finance
pip show signeddata-mcp-finance  # check version
# Verify provenance at https://pypi.org/project/signeddata-mcp-finance/
```

**Official packages** (all published by the `signed-data` GitHub organization):

| Package | PyPI |
|---------|------|
| `signeddata-mcp-finance` | https://pypi.org/project/signeddata-mcp-finance/ |
| `signeddata-mcp-commodities` | https://pypi.org/project/signeddata-mcp-commodities/ |
| `signeddata-mcp-lottery` | https://pypi.org/project/signeddata-mcp-lottery/ |
| `signeddata-mcp-companies` | https://pypi.org/project/signeddata-mcp-companies/ |
| `signeddata-mcp-gov-br` | https://pypi.org/project/signeddata-mcp-gov-br/ |
| `signeddata-mcp-weather` | https://pypi.org/project/signeddata-mcp-weather/ |
| `signeddata-mcp-sports` | https://pypi.org/project/signeddata-mcp-sports/ |
| `signeddata-mcp-integrity` | https://pypi.org/project/signeddata-mcp-integrity/ |
| `signeddata-cds` | https://pypi.org/project/signeddata-cds/ |

Typosquat warning: packages with similar names (e.g. `signed-data-mcp-*`, `signeddata_mcp_*` variants with different spellings) are not official. If you find a lookalike package, report it to security@wdotnet.com.br.
