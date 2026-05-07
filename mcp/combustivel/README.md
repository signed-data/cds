# cds-mcp-combustivel

SignedData CDS MCP Server — **Fuel Prices Brazil (ANP)**

Weekly retail fuel price survey data from ANP (Agência Nacional do Petróleo, Gás Natural e Biocombustíveis), cryptographically signed by [signed-data.org](https://signed-data.org).

## Tools

| Tool | Description |
|------|-------------|
| `get_prices_by_state` | Latest retail fuel prices in a Brazilian state |
| `get_prices_by_municipality` | Prices in a specific city |
| `get_national_average` | National average sale price across all states |

## Products

- `GASOLINA COMUM`
- `ETANOL HIDRATADO`
- `DIESEL S10`
- `DIESEL S500`
- `GNV`

## Data Source

ANP CKAN open data portal — no API key required.
Resource: `b642eb11-f27a-4543-b265-a2f3d79adfb9`

## Usage

```bash
pip install -e .
signeddata-mcp-combustivel
```

Or in Claude Desktop / Cursor:

```json
{
  "mcpServers": {
    "combustivel": {
      "command": "signeddata-mcp-combustivel"
    }
  }
}
```

## Hosted Endpoint

`https://combustivel.mcp.signed-data.org`
