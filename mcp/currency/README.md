# SignedData MCP Server — Currency Exchange Brazil

Exposes currency exchange rates and PTAX data via MCP tools for Claude and other LLMs.

Data is sourced from:
- **AwesomeAPI** — real-time exchange rates (free, anonymous)
- **BCB PTAX** — official Banco Central do Brasil exchange rates

All signed responses are cryptographically signed by `https://signed-data.org`.

## Tools

| Tool | Description |
|---|---|
| `get_exchange_rate` | Current bid/ask for any currency pair |
| `get_multiple_rates` | Batch rates for a base currency vs multiple targets |
| `get_latam_rates` | All LATAM currencies vs BRL in one call |
| `get_rate_history` | Historical daily rates via BCB PTAX (up to 365 days) |
| `get_ptax_oficial` | Official BCB PTAX buy/sell rate for a given date |
| `convert_amount` | Convert an amount between currencies with full rate metadata |

## Install

```bash
pip install signeddata-mcp-currency
```

## Run

```bash
# stdio (Claude Desktop / Claude Code)
python -m server
```

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.

## Data sources

- AwesomeAPI: `https://economia.awesomeapi.com.br/json/last/{pairs}`
- BCB PTAX: `https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/`

## Hosted service

This MCP server is available as a hosted, production-grade service from **Wdotnet**.

No infrastructure required. Connect your AI agent directly to Wdotnet's signed-data endpoints and receive W3C Verifiable Credentials for every response.

→ [wdotnet.com.br](https://wdotnet.com.br) · mcp@wdotnet.com.br

*Every credential is issued by [signed-data.org](https://signed-data.org), the open trust standard powering Wdotnet's data feeds.*
