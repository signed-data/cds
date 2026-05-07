# cds-mcp-saude

SignedData CDS MCP Server — **Health Surveillance Brazil (Fiocruz / OpenDataSUS)**

Brazilian epidemiological health surveillance data from Fiocruz InfoGripe (flu/respiratory illness) and OpenDataSUS (SRAG notifications), cryptographically signed by [signed-data.org](https://signed-data.org).

## Tools

| Tool | Description |
|------|-------------|
| `get_flu_surveillance_br` | National weekly flu/SARS incidence from Fiocruz InfoGripe |
| `get_flu_surveillance_state` | State-level weekly surveillance data |
| `get_srag_recent` | Recent SRAG (severe respiratory illness) notifications from OpenDataSUS |

## Data Sources

- **Fiocruz InfoGripe** — `https://info.gripe.fiocruz.br` — no API key required
- **OpenDataSUS** — `https://opendatasus.saude.gov.br` — no API key required

## Usage

```bash
pip install -e .
signeddata-mcp-saude
```

Or in Claude Desktop / Cursor:

```json
{
  "mcpServers": {
    "saude": {
      "command": "signeddata-mcp-saude"
    }
  }
}
```

## Hosted Endpoint

`https://saude.mcp.signed-data.org`
