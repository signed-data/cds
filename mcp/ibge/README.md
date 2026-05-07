# SignedData MCP Server — IBGE Demographics Brazil

Exposes demographic and economic data for all 5,570 Brazilian municipalities
and 26 states + DF via MCP tools for Claude and other LLMs.

Data is sourced from:
- **IBGE Localidades API** — municipality/state/region metadata
- **IBGE SIDRA** — population (Censo 2022) and PIB data (2021)

All signed responses are cryptographically signed by `https://signed-data.org`.

## Tools

| Tool | Description |
|---|---|
| `get_city_profile` | Full profile for a municipality: population (2022), PIB/capita (2021), state, region |
| `get_state_profile` | State profile with region, municipality count, and a sample list |
| `compare_cities` | Side-by-side comparison of 2–5 municipalities (population + PIB/capita) |
| `find_cities_by_profile` | Filter municipalities by UF, region, or name substring (no SIDRA calls) |
| `get_pib_municipal` | PIB total and PIB per capita for a municipality (IBGE 2021) |
| `get_regional_summary` | Municipality count by region; optionally lists all cities in a region |
| `list_cities` | All municipalities in a state, sorted alphabetically (id + nome) |
| `get_ibge_info` | Data sources, freshness, and API limitations |

## Security

**Hosted endpoint (recommended):** Connect to Wdotnet's managed endpoint at
`https://ibge.mcp.signed-data.org`. No local process required.

**Self-hosted (STDIO):** If running locally via STDIO transport:
- Only add this server to MCP config files you fully control
- Never accept MCP config files from untrusted sources
- The server process has access to your environment variables and filesystem
- Run in a Docker container for isolation: `docker run signeddata/mcp-ibge`

**Data trust model:** All responses are cryptographically signed by
`https://signed-data.org`. Population data: IBGE Censo 2022. PIB data: IBGE 2021.

## Data sources

```
GET https://servicodados.ibge.gov.br/api/v1/localidades/municipios
GET https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}
GET https://servicodados.ibge.gov.br/api/v3/agregados/9605/periodos/2022/variaveis/93?localidades=N6[{id}]
GET https://servicodados.ibge.gov.br/api/v3/agregados/6706/periodos/2021/variaveis/9324?localidades=N6[{id}]
GET https://servicodados.ibge.gov.br/api/v3/agregados/6706/periodos/2021/variaveis/37?localidades=N6[{id}]
```

No authentication required for any IBGE endpoint.

## Hosted service

This MCP server is available as a hosted, production-grade service from **Wdotnet**.

No infrastructure required. Connect your AI agent directly to Wdotnet's signed-data endpoints and receive W3C Verifiable Credentials for every response.

→ [wdotnet.com.br](https://wdotnet.com.br) · mcp@wdotnet.com.br

*Every credential is issued by [signed-data.org](https://signed-data.org), the open trust standard powering Wdotnet's data feeds.*
