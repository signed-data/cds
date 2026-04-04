# CDS Domain Specification — `companies.brazil`

**Version:** 1.0.0
**Domain URI:** `https://signed-data.org/vocab/companies-brazil/`
**Status:** Active
**Date:** 2026-04-03

---

## Overview

The `companies.brazil` domain provides certified, signed CNPJ company
registration data from the Brazilian Receita Federal via BrasilAPI.
This is a **query-driven** domain — data is fetched on demand per CNPJ
lookup, not on a schedule.

## Data Sources

| Source | URI | Auth | License |
|---|---|---|---|
| BrasilAPI | `https://signed-data.org/sources/brasilapi.com.br.v1` | none | MIT |

## Content Types

| Schema | Content Type URI | Source | Cadence |
|---|---|---|---|
| `profile.cnpj` | `https://signed-data.org/vocab/companies-brazil/profile-cnpj` | BrasilAPI | On-demand |
| `partners.cnpj` | `https://signed-data.org/vocab/companies-brazil/partners-cnpj` | BrasilAPI | On-demand |
| `cnae.profile` | `https://signed-data.org/vocab/companies-brazil/cnae-profile` | BrasilAPI | Reference |

## Ingestor Pattern

Query-driven. No scheduled ingestor. The MCP server fetches and signs
CNPJ data on each request. The CDS signature proves that BrasilAPI
returned this data at the query timestamp.

## CNPJ Validation

All lookups validate the CNPJ check digits before making any API call.
The Brazilian CNPJ has two check digits computed with a standard algorithm.

## Language

All events use `lang: "pt-BR"`.
