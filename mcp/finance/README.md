# SignedData MCP Server — Brazil Finance

Signed, verified Brazilian financial data as MCP tools for Claude.
SELIC, CDI, IPCA, IGP-M, USD/BRL, EUR/BRL, B3 stocks, and Copom decisions.

## Quick Start — Remote (10 seconds, zero install)

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "signeddata-finance": {
      "url": "https://finance.mcp.signed-data.org/mcp"
    }
  }
}
```

Or test via curl:

```bash
curl -X POST https://finance.mcp.signed-data.org/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Quick Start — Local (30 seconds)

```bash
pip install "signeddata-mcp-finance @ git+https://github.com/signed-data/cds@v0.3.0#subdirectory=mcp/finance"
signeddata-mcp-finance
```

Then add to Claude Desktop:

```json
{
  "mcpServers": {
    "signeddata-finance": {
      "command": "signeddata-mcp-finance"
    }
  }
}
```

## Quick Start — From Source

```bash
git clone https://github.com/signed-data/cds.git && cd cds
pip install -e sdk/python
pip install -e mcp/finance
signeddata-mcp-finance
```

## Tools

| Tool | Description |
|---|---|
| `get_selic_rate` | SELIC overnight rate (last N days) |
| `get_ipca` | IPCA consumer price index (monthly + 12m) |
| `get_igpm` | IGP-M general price index |
| `get_usd_brl` | USD/BRL PTAX exchange rate (buy/sell) |
| `get_fx_rates` | USD/BRL + EUR/BRL at once |
| `get_stock_quote` | B3 stock quotes — up to 10 tickers |
| `get_market_summary` | SELIC + USD/BRL in one call |
| `get_copom_history` | Last N Copom monetary policy decisions |
| `get_copom_latest` | Most recent Copom decision |

## Resources

| URI | Description |
|---|---|
| `finance://selic/latest` | Latest SELIC rate |
| `finance://usd-brl/latest` | Latest USD/BRL PTAX |
| `finance://ipca/latest` | Latest IPCA index |
| `finance://market-summary` | Market summary |

## HTTP API (deployed endpoint)

The server is deployed at `https://finance.mcp.signed-data.org`.

```bash
# Service info
curl https://finance.mcp.signed-data.org/

# SELIC rate
curl https://finance.mcp.signed-data.org/tool/get_selic_rate

# Stock quote
curl "https://finance.mcp.signed-data.org/tool/get_stock_quote?tickers=PETR4,VALE3"

# USD/BRL (last 5 days)
curl "https://finance.mcp.signed-data.org/tool/get_usd_brl?last_n=5"

# Copom latest
curl https://finance.mcp.signed-data.org/tool/get_copom_latest
```

## Data Sources

| Source | URL | Auth |
|---|---|---|
| Banco Central do Brasil (SGS) | `api.bcb.gov.br` | None (public domain) |
| Brapi (B3 quotes) | `brapi.dev/api` | None (free tier, 15 req/min) |
| BCB Copom | `bcb.gov.br` | None |

## Environment Variables (optional)

| Variable | Description | Default |
|---|---|---|
| `CDS_PRIVATE_KEY_PATH` | Path to RSA private key for signing | (unsigned if not set) |
| `CDS_PUBLIC_KEY_PATH` | Path to RSA public key for verification | (skip verification) |
| `CDS_ISSUER` | Issuer URI in signed events | `signed-data.org` |

All data is cryptographically signed by [signed-data.org](https://signed-data.org) when keys are configured.

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.

## Hosted service

This MCP server is available as a hosted, production-grade service from **Wdotnet**.

No infrastructure required. Connect your AI agent directly to Wdotnet's signed-data endpoints and receive W3C Verifiable Credentials for every response.

→ [wdotnet.com.br](https://wdotnet.com.br) · mcp@wdotnet.com.br

*Every credential is issued by [signed-data.org](https://signed-data.org), the open trust standard powering Wdotnet's data feeds.*
