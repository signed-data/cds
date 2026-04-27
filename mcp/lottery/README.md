# SignedData MCP Server — Brazil Lottery

Exposes Mega Sena (and other Caixa games) as MCP tools for Claude.

## Tools

| Tool | Description |
|---|---|
| `get_mega_sena_latest` | Latest draw — numbers, prizes, acumulado |
| `get_mega_sena_by_concurso` | Specific draw by number |
| `get_mega_sena_recent` | Last N draws (up to 20) |
| `check_mega_sena_ticket` | Check if your numbers won |
| `get_mega_sena_statistics` | Frequency analysis of last N draws |

## Resources

| URI | Description |
|---|---|
| `lottery://mega-sena/latest` | Latest result as JSON |
| `lottery://mega-sena/schema` | CDS content type + payload schema |

## Install

```bash
pip install signeddata-mcp-lottery
```

## Run

```bash
# stdio (Claude Desktop / Claude Code)
python -m cds_mcp_lottery mega-sena

# SSE (web clients)
signeddata-mcp-lottery mega-sena --transport sse --port 8001
```

## Claude Desktop config (~/.config/claude/claude_desktop_config.json)

```json
{
  "mcpServers": {
    "signeddata-lottery": {
      "command": "python",
      "args": ["-m", "cds_mcp_lottery", "mega-sena"],
      "env": {
        "CDS_PRIVATE_KEY_PATH": "/path/to/keys/private.pem",
        "CDS_PUBLIC_KEY_PATH":  "/path/to/keys/public.pem",
        "CDS_ISSUER":           "signed-data.org"
      }
    }
  }
}
```

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.

## Data source

Official Caixa Econômica Federal API — no authentication required.

```
GET https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/
GET https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/{concurso}
```

## Hosted service

This MCP server is available as a hosted, production-grade service from **Wdotnet**.

No infrastructure required. Connect your AI agent directly to Wdotnet's signed-data endpoints and receive W3C Verifiable Credentials for every response.

→ [wdotnet.com.br](https://wdotnet.com.br) · mcp@wdotnet.com.br

*Every credential is issued by [signed-data.org](https://signed-data.org), the open trust standard powering Wdotnet's data feeds.*
