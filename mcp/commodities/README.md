# SignedData MCP Server — Brazil Commodities

Signed, verified Brazilian commodity data as MCP tools for Claude.
B3 agro futures, CONAB physical crop prices, and auditable basis spreads.

## Quick Start — Remote (10 seconds, zero install)

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "signeddata-commodities": {
      "url": "https://commodities.mcp.signed-data.org/mcp"
    }
  }
}
```

Or test via curl:

```bash
curl -X POST https://commodities.mcp.signed-data.org/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Quick Start — Local (30 seconds)

```bash
pip install "signeddata-mcp-commodities @ git+https://github.com/signed-data/cds@v0.3.1#subdirectory=mcp/commodities"
signeddata-mcp-commodities
```

Then add to Claude Desktop:

```json
{
  "mcpServers": {
    "signeddata-commodities": {
      "command": "signeddata-mcp-commodities"
    }
  }
}
```

## Quick Start — From Source

```bash
git clone https://github.com/signed-data/cds.git && cd cds
pip install -e sdk/python
pip install -e mcp/commodities
signeddata-mcp-commodities
```

## Tools

| Tool | Description |
|---|---|
| `get_soja_futures` | Latest soybean B3 futures quote |
| `get_all_agro_futures` | All supported B3 agricultural futures |
| `get_futures_by_commodity` | Single B3 commodity futures quote by ticker |
| `get_soja_spot_prices` | CONAB soybean spot prices by state |
| `get_spot_by_commodity` | CONAB spot prices for soja, milho, trigo, or algodao |
| `get_commodity_summary` | Futures plus spot prices side by side |
| `get_basis` | Auditable basis spread: spot minus futures |

## HTTP API (deployed endpoint)

The server is deployed at `https://commodities.mcp.signed-data.org`.

```bash
# Service info
curl https://commodities.mcp.signed-data.org/

# All agro futures
curl https://commodities.mcp.signed-data.org/tool/get_all_agro_futures

# One B3 futures ticker
curl "https://commodities.mcp.signed-data.org/tool/get_futures_by_commodity?ticker=SFI"

# CONAB spot prices
curl "https://commodities.mcp.signed-data.org/tool/get_soja_spot_prices?states=MT&states=GO"

# Basis spread
curl "https://commodities.mcp.signed-data.org/tool/get_basis?commodity=soja&state=MT"
```

## Data Sources

| Source | URL | Auth |
|---|---|---|
| Brapi (B3 futures) | `brapi.dev/api` | None (free tier, 15 req/min) |
| CONAB | `consultaweb.conab.gov.br/consultas/consultaGrao/listar` | None |
| World Bank commodity indicators | `api.worldbank.org/v2/en/indicator` | None |

## Environment Variables (optional)

| Variable | Description | Default |
|---|---|---|
| `CDS_PRIVATE_KEY_PATH` | Path to RSA private key for signing | (unsigned if not set) |
| `CDS_PUBLIC_KEY_PATH` | Path to RSA public key for verification | (skip verification) |
| `CDS_ISSUER` | Issuer URI in signed events | `signed-data.org` |

All data is cryptographically signed by [signed-data.org](https://signed-data.org) when keys are configured.
