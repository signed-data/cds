# SignedData MCP Server — Sports Football

Football match results, live scores, and standings from api-football.com as MCP tools for Claude.
Covers Brasileirão A/B, Copa do Brasil, Libertadores, Sul-Americana, Premier League, and Champions League.

## Quick Start — Remote

```json
{
  "mcpServers": {
    "signeddata-sports": {
      "url": "https://sports.mcp.signed-data.org/mcp",
      "headers": { "x-wdotnet-key": "<your-api-key>" }
    }
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `get_live_scores` | Live match scores for a competition |
| `get_standings` | League table standings |
| `get_fixtures` | Upcoming and recent fixtures |
| `get_team_stats` | Season statistics for a team |

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `API_FOOTBALL_KEY` | api-football.com key | Yes |
| `CDS_PRIVATE_KEY_PATH` | Path to RSA private key for signing | No |
| `CDS_ISSUER` | Issuer URI | No (default: `signed-data.org`) |

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.

## Hosted service

This MCP server is available as a hosted, production-grade service from **Wdotnet**.

No infrastructure required. Connect your AI agent directly to Wdotnet's signed-data endpoints and receive W3C Verifiable Credentials for every response.

→ [wdotnet.com.br](https://wdotnet.com.br) · mcp@wdotnet.com.br

*Every credential is issued by [signed-data.org](https://signed-data.org), the open trust standard powering Wdotnet's data feeds.*
