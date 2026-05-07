# SignedData MCP Server — B3 Fundamentals Brazil

Exposes fundamental analysis data for B3-listed Brazilian stocks via MCP tools for Claude and other LLMs.

Data is sourced from:
- **Brapi** — official B3 market data aggregator (primary)
- **Fundamentus** — HTML scraping enrichment (reliability: unofficial)

All signed responses are cryptographically signed by `https://signed-data.org`.

## Tools

| Tool | Description |
|---|---|
| `get_fundamentals` | P/L, P/VP, ROE, DY, EBITDA, net debt — Brapi primary + Fundamentus enrichment |
| `get_dre_quarterly` | Last 4 quarters of revenue, gross profit, net income |
| `compare_fundamentals` | Side-by-side comparison of up to 5 tickers |
| `get_sector_ranking` | Rank stocks in a sector by ROE, P/L, P/VP, or DY |
| `get_dividend_history` | Historical dividend payments for a ticker |
| `screen_stocks` | Filter all B3 stocks by ROE, P/E, DY, P/VP thresholds |

## Install

```bash
pip install signeddata-mcp-b3-fundamentus
```

## Run

```bash
# stdio (Claude Desktop / Claude Code)
python -m server
```

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.

## Disclaimer

Fundamentus data is extracted via HTML scraping and may differ from official sources. Not financial advice.

## Data sources

- Brapi: `https://brapi.dev/api/quote/{ticker}`
- Fundamentus: `https://www.fundamentus.com.br/resultado.php`

## Hosted service

This MCP server is available as a hosted, production-grade service from **Wdotnet**.

No infrastructure required. Connect your AI agent directly to Wdotnet's signed-data endpoints and receive W3C Verifiable Credentials for every response.

→ [wdotnet.com.br](https://wdotnet.com.br) · mcp@wdotnet.com.br

*Every credential is issued by [signed-data.org](https://signed-data.org), the open trust standard powering Wdotnet's data feeds.*
