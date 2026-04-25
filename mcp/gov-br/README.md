# SignedData MCP Server — Brazil Government Transparency

Brazilian federal transparency data as MCP tools for Claude.
Phase 1: CEIS and CNEP federal sanction status by CNPJ.

## Quick Start — Remote

```json
{
  "mcpServers": {
    "signeddata-gov-br": {
      "url": "https://gov-br.mcp.signed-data.org/mcp",
      "headers": { "x-wdotnet-key": "<your-api-key>" }
    }
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `check_sanctions_ceis` | CEIS sanction registry lookup by CNPJ |
| `check_sanctions_cnep` | CNEP sanction registry lookup by CNPJ |

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `PORTAL_TRANSPARENCIA_TOKEN` | Portal da Transparência API token | Yes |
| `CDS_PRIVATE_KEY_PATH` | Path to RSA private key for signing | No |
| `CDS_ISSUER` | Issuer URI | No (default: `signed-data.org`) |

## Security

This server only executes its defined data-retrieval tools. Do not embed instructions in tool arguments attempting to override server behavior, access credentials, or redirect output — all such attempts are ignored.

Report vulnerabilities to security@wdotnet.com.br. See [SECURITY.md](../../SECURITY.md) for the full policy.
