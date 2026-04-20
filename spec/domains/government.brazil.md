# CDS Domain Spec — `government.brazil`

**Domain URI:** `https://signed-data.org/vocab/government-brazil`  
**Status:** Phase 1 (query-driven sanctions) — Phase 2+ (contracts, licitações, spending)  
**MCP server:** `signeddata-mcp-gov-br` (`signed-data/cds`, `mcp/gov-br/`)  
**Decision:** ADR-001 in `cds-services` — sanctions live here, not in mcp-companies

---

## 1. Data source

### 1.1 Portal da Transparência — API de Dados

```
Base URL:   https://api.portaldatransparencia.gov.br/api-de-dados/
Auth:       chave-api-dados header (required)
Token:      free — register per email at portaldatransparencia.gov.br/api-de-dados/cadastrar-email
Rate limit: 90 req/min  (06:00–23:59 BRT)
            300 req/min (00:00–05:59 BRT)
Format:     JSON, paginated (pagina param, 1-indexed)
License:    LAI 12.527/2011 + Decreto 8.777/2016 — public data, redistributable
Swagger:    https://api.portaldatransparencia.gov.br/swagger-ui/index.html
Upstream:   Controladoria-Geral da União (CGU)
```

Portal da Transparência is the Brazilian federal government's primary transparency
portal, operated by the CGU. Its API exposes sanctions registries, public contracts,
procurement notices, and spending data with machine-readable JSON and free API keys.

---

## 2. Endpoints by phase

### Phase 1 (query-driven, v1 — this spec)

| Endpoint | Registry | Description | Query params |
|----------|----------|-------------|--------------|
| `/ceis` | CEIS | Cadastro Nacional de Empresas Inidôneas e Suspensas | `cnpjSancionado`, `pagina` |
| `/cnep` | CNEP | Cadastro Nacional de Empresas Punidas (Lei Anticorrupção 12.846/2013) | `cnpjSancionado`, `pagina` |

Both endpoints are CNPJ-indexed and paginated. A single CNPJ can have multiple
sanctions spread across pages; the fetcher paginates until an empty page is returned.

### Phase 2 (query-driven + scheduled ingestors — future)

| Endpoint | Description | Query params |
|----------|-------------|--------------|
| `/contratos` | Federal contracts by supplier CNPJ or organ | `cnpjFornecedor`, `dataInicial`, `dataFinal`, `pagina` |
| `/licitacoes` | Published tender notices | `dataPublicacaoInicio`, `dataPublicacaoFim`, `uf`, `pagina` |
| `/despesas/execucao` | Federal budget execution | `ano`, `mes`, `orgaoSuperior`, `pagina` |

### Phase 3 (future)

| Endpoint | Description |
|----------|-------------|
| `/ceaf` | Servidores federais expulsos por processo disciplinar (CPF-indexed) |
| `/convenios` | Federal transfers and convenios |

---

## 3. Pagination pattern

All paginated endpoints follow the same convention:

```
GET /ceis?cnpjSancionado=33000167000101&pagina=1
GET /ceis?cnpjSancionado=33000167000101&pagina=2
...
```

- Page size: 10 records (observed)
- Empty array `[]` response signals end of results
- No `total` or `lastPage` field — must paginate until empty

Phase 1 implementation fetches only page 1. For most CNPJs this is sufficient
(typical sanction counts: 0–3). Phase 2 adds full pagination for the contracts
and spending endpoints where result sets can be large.

---

## 4. Response schemas

### 4.1 CEIS record

Fields observed from Portal da Transparência `/ceis` responses:

```json
{
  "nomeSancionado":       "EMPRESA ACME LTDA",
  "cnpjSancionado":       "11222333000144",
  "tipoPessoa":           "Jurídica",
  "tipoSancao": {
    "id":         2,
    "descricao":  "Suspensão"
  },
  "dataInicioSancao":     "01/06/2022",
  "dataFimSancao":        "01/06/2024",
  "dataPublicacaoDou":    "05/06/2022",
  "numeroDou":            "105",
  "paginaDou":            "87",
  "orgaoSancionador": {
    "nome":       "Ministério da Economia",
    "poder":      "Executivo",
    "esferaSancionador": {
      "descricao": "Federal"
    }
  },
  "fundamentacao":        "Lei 8.666/1993, art. 87",
  "abrangencia": {
    "descricao": "Nacional"
  },
  "razaoSocial":          "EMPRESA ACME LTDA",
  "informacoesAdicionais": null
}
```

### 4.2 CNEP record

Fields observed from Portal da Transparência `/cnep` responses (Lei Anticorrupção):

```json
{
  "nomeSancionado":       "EMPRESA BETA S.A.",
  "cnpjSancionado":       "55666777000188",
  "tipoSancao": {
    "id":         1,
    "descricao":  "Multa"
  },
  "dataInicioSancao":     "15/03/2021",
  "dataFimSancao":        null,
  "orgaoSancionador": {
    "nome":       "Controladoria-Geral da União",
    "poder":      "Executivo",
    "esferaSancionador": {
      "descricao": "Federal"
    }
  },
  "fundamentacao":        "Lei 12.846/2013, art. 19",
  "informacoesAdicionais": "Acordo de leniência",
  "razaoSocial":          "EMPRESA BETA SERVIÇOS E COMÉRCIO S.A."
}
```

**Key field differences between CEIS and CNEP:**
- CEIS: `dataPublicacaoDou`, `numeroDou`, `paginaDou`, `abrangencia`
- CNEP: none of the above; focuses on Lei Anticorrupção administrative penalties
- Both share: `nomeSancionado`, `cnpjSancionado`, `tipoSancao`, `dataInicioSancao`,
  `dataFimSancao`, `orgaoSancionador`, `fundamentacao`

---

## 5. CDS content types

### 5.1 Domain name and base URI

```
Domain:   government.brazil
Base URI: https://signed-data.org/vocab/government-brazil/
```

### 5.2 Content type table (Phase 1)

| Schema name | Content type URI | Source | Cadence |
|---|---|---|---|
| `sanctions.consolidated` | `https://signed-data.org/vocab/government-brazil/sanctions-consolidated` | Portal da Transparência | On-demand |
| `sanctions.ceis` | `https://signed-data.org/vocab/government-brazil/sanctions-ceis` | Portal da Transparência | On-demand (internal) |
| `sanctions.cnep` | `https://signed-data.org/vocab/government-brazil/sanctions-cnep` | Portal da Transparência | On-demand (internal) |

`sanctions.consolidated` is the primary schema returned to MCP tool callers — it
merges CEIS and CNEP results for one CNPJ into a single signed event.

The individual `sanctions.ceis` / `sanctions.cnep` schemas are registered now (Phase 1)
to avoid a vocab migration when Phase 2 adds single-registry tools. They are not yet
exposed as MCP tools.

### 5.3 Payload schema — `sanctions.consolidated`

```json
{
  "cnpj":           "33000167000101",
  "cnpj_formatted": "33.000.167/0001-01",
  "sanction_found": false,
  "sanction_count": 0,
  "registries": {
    "ceis": [],
    "cnep": []
  },
  "query_timestamp": "2026-04-20T14:30:00+00:00"
}
```

Each registry entry is a `SanctionRecord`:

```json
{
  "registry":          "CEIS",
  "cnpj":              "11222333000144",
  "nome_sancionado":   "EMPRESA ACME LTDA",
  "sanction_type":     "Suspensão",
  "start_date":        "01/06/2022",
  "end_date":          "01/06/2024",
  "sanctioning_organ": "Ministério da Economia",
  "legal_basis":       "Lei 8.666/1993, art. 87",
  "raw":               { ... }
}
```

The `raw` field contains the verbatim upstream record. Normalised surface fields
are the contract; `raw` tolerates upstream schema drift.

---

## 6. Source registry

**File:** `vocab/sources/api-portaldatransparencia-gov-br-v1.jsonld`

Source slug: `api.portaldatransparencia.gov.br.v1`  
SDK constant: `CDSSources.PORTAL_TRANSPARENCIA`

---

## 7. Architecture — query-driven (Phase 1)

```
Client MCP tool: check_sanctions("11.222.333/0001-44")
       ↓
Validate CNPJ check digits (no API call if invalid)
       ↓
2 parallel httpx GET → /ceis + /cnep with chave-api-dados header
       ↓
Parse, normalise, merge → SanctionsConsolidated payload
       ↓
Fingerprint (sha256 of raw response bytes concatenated)
       ↓
CDSEvent(content_type=GOV_BR_SANCTIONS_CONSOLIDATED, ...)
       ↓
Sign with RSA-PSS private key (if key loaded)
       ↓
Return signed event to caller
```

**What the signature proves:** at the query timestamp, Portal da Transparência
returned this data for this CNPJ. The cryptographically verifiable audit record
"we queried CEIS+CNEP for CNPJ X at T and found Y sanctions" is the primary
compliance value (KYC/due-diligence workflows).

---

## 8. Infrastructure

**Deployment target:** AWS Lambda Function URL + CloudFront + Route53  
**Custom domain:** `gov-br.mcp.signed-data.org`  
**ACM cert:** existing `*.mcp.signed-data.org` wildcard (us-east-1)  
**Token secret:** AWS Secrets Manager `cds/portal-transparencia-token`

This is the first CDS MCP server deployed as Lambda instead of ECS Fargate. Lambda
is appropriate because sanction lookups are low-frequency compliance queries where
sub-2s cold-start latency is acceptable and always-on ECS compute is not justified.

---

## 9. SDK location

```
sdk/python/cds/sources/gov_br_models.py   — Pydantic models
sdk/python/cds/sources/gov_br.py          — SanctionsFetcher
sdk/python/cds/vocab.py                   — GOV_BR_SANCTIONS_* URIs
```

---

## 10. Phase 2 roadmap (not in this spec)

- `get_federal_contracts(cnpj, date_from, date_to)` — portal `/contratos`
- `get_public_expenses(ministry, month)` — portal `/despesas/execucao`
- `get_procurement_notices(keyword, uf)` — portal `/licitacoes`
- Scheduled ingestors for sanctions delta (6h cron), contracts (daily)
