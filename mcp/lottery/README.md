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
cd mcp/lottery
pip install fastmcp httpx pydantic cryptography
# also needs the CDS SDK
pip install -e ../../sdk/python
```

## Run

```bash
# stdio (Claude Desktop / Claude Code)
python server.py

# SSE (web clients)
python server.py --transport sse --port 8001
```

## Claude Desktop config (~/.config/claude/claude_desktop_config.json)

```json
{
  "mcpServers": {
    "signeddata-lottery": {
      "command": "python",
      "args": ["/path/to/cds/mcp/lottery/server.py"],
      "env": {
        "CDS_PRIVATE_KEY_PATH": "/path/to/keys/private.pem",
        "CDS_PUBLIC_KEY_PATH":  "/path/to/keys/public.pem",
        "CDS_ISSUER":           "signed-data.org"
      }
    }
  }
}
```

## Data source

Official Caixa Econômica Federal API — no authentication required.

```
GET https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/
GET https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/{concurso}
```
