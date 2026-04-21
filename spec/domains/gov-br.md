# CDS Domain Specification — `gov-br`

**Version:** 1.0.0  
**Domain URI:** `https://signed-data.org/vocab/gov-br/`  
**Status:** Active (Phase 1: Sanctions only)  
**Date:** 2026-04-20

---

## Overview

The `gov-br` domain provides certified, signed Brazilian government transparency data from the Portal da Transparência (https://portaldatransparencia.gov.br). Phase 1 focuses on sanctions status (CEIS and CNEP registries). Future phases will include federal contracts, procurement notices, and budget execution data.

All content types in this domain use CDS v0.2.0 Linked Data URIs.

## Data Source

| Source | URI | Auth | License | Rate Limit |
|---|---|---|---|---|
| Portal da Transparência — API de Dados | `https://signed-data.org/sources/api.portaldatransparencia.gov.br.v1` | `chave-api-dados` header | LAI 12.527/2011 + Decreto 8.777/2016 (public) | 90 req/min (06:00–23:59 BRT) / 300 req/min (00:00–05:59 BRT) |

### API Details

**Base URL:** `https://api.portaldatransparencia.gov.br/api-de-dados/`  
**Auth Method:** HTTP header `chave-api-dados: {token}`  
**Pagination:** Query params: `pagina`, `tamanhoPagina` (default 20)  
**Format:** JSON  
**Documentation:** https://api.portaldatransparencia.gov.br/swagger-ui/index.html

## Content Types — Phase 1

| Schema | Content Type URI | API Endpoint | Purpose |
|---|---|---|---|
| `sanctions.consolidated` | `https://signed-data.org/vocab/gov-br/sanctions-consolidated` | `/ceis` + `/cnep` | CNPJ sanction status (CEIS inidôneas + CNEP Lei Anticorrupção) |

### Phase 2 (Reserved)

- `contracts.federal` → `/contratos`
- `procurement.notices` → `/licitacoes`
- `expenses.execution` → `/despesas/execucao`

### Phase 3 (Reserved)

- `officials.expelled` → `/ceaf` (CPF-indexed federal officials)
- `transfers.federal` → `/convenios`

---

## API Endpoints — Phase 1

### /ceis

**Purpose:** Fetch companies registered in CEIS (Cadastro de Empresas Inidôneas e Suspensas — register of suspended/unsuitable companies)

**Request:**
```
GET /api-de-dados/ceis?cnpj=11222333000144&tamanhoPagina=1
Host: api.portaldatransparencia.gov.br
chave-api-dados: {token}
```

**Response example:**
```json
{
  "dados": [
    {
      "CNPJ": "11222333000144",
      "RAZAO_SOCIAL": "Example Corp",
      "DATA_PUBLICACAO_INSCRICAO": "2023-01-15",
      "DATA_INICIO_SUSPENSAO": "2023-01-15",
      "DATA_FIM_SUSPENSAO": "2026-01-14",
      "MOTIVO_INSCRICAO": "Descumprimento de obrigação...",
      "NORMA_LEGAL": "Lei 8.666/1993",
      "ORGAO": "CGU"
    }
  ],
  "paginacao": {
    "pagina": 1,
    "tamanhoPagina": 1,
    "proximaPagina": false
  }
}
```

**Key fields:**
- `CNPJ`: 14-digit CNPJ (unformatted)
- `RAZAO_SOCIAL`: Company legal name
- `DATA_PUBLICACAO_INSCRICAO`: Publication date
- `DATA_INICIO_SUSPENSAO`: Suspension start date
- `DATA_FIM_SUSPENSAO`: Suspension end date (null if ongoing)
- `MOTIVO_INSCRICAO`: Reason for listing
- `NORMA_LEGAL`: Legal basis
- `ORGAO`: Agency responsible (CGU, ANAC, etc.)

### /cnep

**Purpose:** Fetch companies under the Lei Anticorrupção (Law 12.846/2013 — Anti-Corruption Law)

**Request:**
```
GET /api-de-dados/cnep?cnpj=11222333000144&tamanhoPagina=1
Host: api.portaldatransparencia.gov.br
chave-api-dados: {token}
```

**Response example:**
```json
{
  "dados": [
    {
      "CNPJ": "11222333000144",
      "RAZAO_SOCIAL": "Example Corp",
      "DATA_PUBLICACAO_PUNICAO": "2023-06-20",
      "DATA_INICIO_PUNICAO": "2023-06-20",
      "DATA_FIM_PUNICAO": "2026-06-19",
      "TIPO_PUNICAO": "Suspension",
      "FUNDAMENTACAO_LEGAL": "Lei 12.846/2013",
      "ORGAO": "CGU"
    }
  ],
  "paginacao": {
    "pagina": 1,
    "tamanhoPagina": 1,
    "proximaPagina": false
  }
}
```

**Key fields:**
- `CNPJ`: 14-digit CNPJ (unformatted)
- `RAZAO_SOCIAL`: Company legal name
- `DATA_PUBLICACAO_PUNICAO`: Publication date
- `DATA_INICIO_PUNICAO`: Penalty start date
- `DATA_FIM_PUNICAO`: Penalty end date (null if ongoing)
- `TIPO_PUNICAO`: Penalty type (Suspension, Disqualification, etc.)
- `FUNDAMENTACAO_LEGAL`: Legal basis
- `ORGAO`: Agency responsible (CGU)

---

## Schema Payload — `sanctions.consolidated`

Unified response combining both CEIS and CNEP checks for a single CNPJ.

```json
{
  "cnpj": "11222333000144",
  "cnpj_formatted": "11.222.333/0001-44",
  "sanction_found": false,
  "sanction_count": 0,
  "registries": {
    "ceis": [],
    "cnep": []
  },
  "query_timestamp": "2026-04-20T14:30:00Z"
}
```

### Schema details

| Field | Type | Description |
|---|---|---|
| `cnpj` | string | 14-digit CNPJ (unformatted) |
| `cnpj_formatted` | string | CNPJ in XX.XXX.XXX/XXXX-XX format |
| `sanction_found` | boolean | `true` if any record found in CEIS or CNEP |
| `sanction_count` | integer | Total number of sanction records (CEIS + CNEP) |
| `registries.ceis` | array | CEIS records for this CNPJ (empty if none) |
| `registries.cnep` | array | CNEP records for this CNPJ (empty if none) |
| `query_timestamp` | string | ISO 8601 timestamp of query (UTC) |

### CEIS record structure (inside `registries.ceis`)

```json
{
  "cnpj": "11222333000144",
  "reason": "Descumprimento de obrigação...",
  "published_date": "2023-01-15",
  "start_date": "2023-01-15",
  "end_date": "2026-01-14",
  "legal_basis": "Lei 8.666/1993",
  "agency": "CGU",
  "company_name": "Example Corp"
}
```

### CNEP record structure (inside `registries.cnep`)

```json
{
  "cnpj": "11222333000144",
  "published_date": "2023-06-20",
  "start_date": "2023-06-20",
  "end_date": "2026-06-19",
  "penalty_type": "Suspension",
  "legal_basis": "Lei 12.846/2013",
  "agency": "CGU",
  "company_name": "Example Corp"
}
```

---

## Ingestor Pattern

Query-driven (no scheduled ingestion). The MCP server calls both endpoints on demand when `check_sanctions(cnpj)` is invoked. Parallel requests reduce latency.

---

## Language

All events and field names use English. Portuguese source field names are mapped to English equivalents. Event locale is `pt-BR` for metadata only (presentation purposes).

---

## Trust & Verification

- All data is published by Controladoria-Geral da União (CGU) and is public domain under LAI 12.527/2011.
- Responses are wrapped in a CDS Event, timestamped, and signed by the operator's RSA-PSS key.
- Signature verification confirms data integrity but does not certify freshness (consume timestamps for recency).
