# CDS Domain Specification — `integrity.brazil`

**Version:** 1.0.0
**Domain URI:** `https://signed-data.org/vocab/integrity-brazil/`
**Status:** Active
**Date:** 2026-04-07

---

## Overview

The `integrity.brazil` domain provides certified, signed feeds of Brazilian
federal sanctions, contracts, and public-integrity data from Portal da
Transparência (Controladoria-Geral da União). It is the KYC/AML/due-diligence
companion to `companies.brazil`.

Phase 1 ships a **query-driven** sanction lookup: given a CNPJ, return the
consolidated status across the three main federal sanction registries
(CEIS, CNEP, CEPIM) as one signed CDS event. Phase 2+ will add scheduled
ingestors for contracts, convênios, and new-sanction deltas.

## Data Sources

| Source | URI | Auth | License |
|---|---|---|---|
| Portal da Transparência | `https://signed-data.org/sources/api.portaldatransparencia.gov.br.v1` | api-key | LAI 12.527/2011 |

Token-based: a free `chave-api-dados` header is required. Register at
https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email. Rate
limits: 90 req/min (06:00–23:59 BRT), 300 req/min (00:00–05:59 BRT).

## Content Types

| Schema | Content Type URI | Source | Cadence |
|---|---|---|---|
| `sanctions.consolidated` | `.../integrity-brazil/sanctions-consolidated` | Portal da Transparência | On-demand |
| `sanctions.ceis` | `.../integrity-brazil/sanctions-ceis` | Portal da Transparência | On-demand |
| `sanctions.cnep` | `.../integrity-brazil/sanctions-cnep` | Portal da Transparência | On-demand |
| `sanctions.cepim` | `.../integrity-brazil/sanctions-cepim` | Portal da Transparência | On-demand |

`sanctions.consolidated` is the Phase 1 primary schema — it merges CEIS,
CNEP, and CEPIM results into a single signed event. The individual
registry schemas are reserved for future tools that expose single-registry
lookups.

## Ingestor Pattern

**Phase 1 — query-driven.** No scheduled ingestor. The MCP server fetches
all three sanction registries in parallel and signs the consolidated
response per request. The CDS signature proves that Portal da Transparência
returned this data at the query timestamp.

**Phase 2+ — hybrid.** Scheduled ingestors will emit one signed event per
new sanction/contract/licitação for downstream subscribers.

## CNPJ Validation

All lookups validate the CNPJ check digits before making any API call.
Reuses the same validator from `cds.sources.companies` — one source of
truth for CNPJ parsing across domains.

## Privacy Note

Sanction records include CPF/CNPJ of sanctioned parties (natural persons
and legal entities) as published by the Controladoria-Geral da União.
This is public data under Lei de Acesso à Informação 12.527/2011. The
CDS signature attests to the source, not to the appropriateness of
storing or sharing it.

## Language

All events use `lang: "pt-BR"`.
