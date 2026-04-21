# SignedData MCP Server — Brazil Integrity (Sanctions)

Brazilian federal sanction lookups as MCP tools for Claude. Queries CEIS, CNEP, and CEPIM in parallel from Portal da Transparência (Controladoria-Geral da União) and returns one consolidated CDS event per CNPJ — signed when `CDS_PRIVATE_KEY_PATH` is configured, otherwise unsigned.

## Quick Start — Remote (10 seconds, zero install)

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "signeddata-integrity": {
      "url": "https://integrity.mcp.signed-data.org/mcp"
    }
  }
}
```

Or test via curl:

```bash
curl -X POST https://integrity.mcp.signed-data.org/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Quick Start — Local (30 seconds)

```bash
pip install signeddata-cds
pip install "git+https://github.com/signed-data/cds.git#subdirectory=mcp/integrity"
export PORTAL_TRANSPARENCIA_TOKEN="<your token>"
signeddata-mcp-integrity
```

Then add to Claude Desktop:

```json
{
  "mcpServers": {
    "signeddata-integrity": {
      "command": "signeddata-mcp-integrity",
      "env": {
        "PORTAL_TRANSPARENCIA_TOKEN": "<your token>"
      }
    }
  }
}
```

The MCP package is source-installed today; only the SDK packages are published by the repo release workflows.

## Quick Start — From Source

```bash
git clone https://github.com/signed-data/cds.git && cd cds
pip install -e sdk/python
pip install -e mcp/integrity
export PORTAL_TRANSPARENCIA_TOKEN="<your token>"
signeddata-mcp-integrity
```

## Tools

| Tool | Description |
|---|---|
| `check_sanctions_by_cnpj` | Parallel CEIS/CNEP/CEPIM lookup for a CNPJ. Returns one consolidated event (signed if `CDS_PRIVATE_KEY_PATH` is set) with `sanction_found`, `sanction_count`, and the per-registry record list. |

Reserved for future phases:

- `get_sanction_detail(sanction_id)`
- `list_recent_sanctions(window)`
- `check_nonprofit_impediment(cnpj)` — CEPIM only
- `get_federal_contracts_by_cnpj(cnpj)` — `/contratos`
- `get_convenios_by_cnpj(cnpj)` — `/convenios`
- `check_servidor_expulsao(cpf)` — CEAF
- `summarize_sanctions_window_analysis(window)` — LLM-suffixed summary

## Composition with `mcp/companies`

The intended due-diligence flow is to compose `mcp/companies` and `mcp/integrity` in the same Claude turn:

```text
get_company_profile("11.222.333/0001-44")        # signeddata-companies → BrasilAPI
check_sanctions_by_cnpj("11.222.333/0001-44")    # signeddata-integrity → Portal da Transparência
```

Each call returns its own CDS event (signed when server signing is configured). Together they form a complete, independently verifiable due-diligence record: who the company is, and whether the federal government has sanctioned it.

## HTTP API (deployed endpoint)

The server is deployed at `https://integrity.mcp.signed-data.org`.

```bash
# JSON-RPC tools/list
curl -X POST https://integrity.mcp.signed-data.org/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Health check
curl https://integrity.mcp.signed-data.org/health
```

## Data Source

| Source | URL | Auth | License |
|---|---|---|---|
| Portal da Transparência | `api.portaldatransparencia.gov.br/api-de-dados` | `chave-api-dados` header | LAI 12.527/2011 |

The Portal da Transparência API token is free but per-email. Register at https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email.

Rate limits (per token): 90 req/min during 06:00–23:59 BRT, 300 req/min during 00:00–05:59 BRT.

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `PORTAL_TRANSPARENCIA_TOKEN` | Portal da Transparência `chave-api-dados` token | Yes (for tool calls) |
| `CDS_PRIVATE_KEY_PATH` | Path to RSA private key for signing | No (unsigned if not set) |
| `CDS_ISSUER` | Issuer URI in signed events | No (defaults to `signed-data.org`) |

If `PORTAL_TRANSPARENCIA_TOKEN` is missing, the server starts but `check_sanctions_by_cnpj` returns an error response explaining the missing token. The `/health` check still reports healthy with `token_configured: false`.

## Privacy Note

CEIS, CNEP, and CEPIM records include CPF/CNPJ of sanctioned parties (natural persons and legal entities) as published by the Controladoria-Geral da União under Lei de Acesso à Informação 12.527/2011. The CDS signature attests to the source, not to the appropriateness of redistribution.
