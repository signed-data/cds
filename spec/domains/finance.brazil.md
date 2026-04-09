# CDS Domain Specification — `finance.brazil`

**Version:** 1.0.0
**Domain URI:** `https://signed-data.org/vocab/finance-brazil/`
**Status:** Active
**Date:** 2026-04-03

---

## Overview

The `finance.brazil` domain provides certified, signed data feeds for
Brazilian financial markets. Data sources include the Banco Central do
Brasil (BCB) SGS API for official rates, indices, and FX data, and
Brapi for B3 stock and crypto quotes.

All content types in this domain use CDS v0.2.0 Linked Data URIs.

## Data Sources

| Source | URI | Auth | License |
|---|---|---|---|
| Banco Central do Brasil — SGS API | `https://signed-data.org/sources/api.bcb.gov.br.v1` | none | public domain |
| Brapi — B3 e finanças brasileiras | `https://signed-data.org/sources/brapi.dev.v1` | none (free tier) | MIT |

## Content Types

| Schema | Content Type URI | Source | Cadence |
|---|---|---|---|
| `rate.selic` | `https://signed-data.org/vocab/finance-brazil/rate-selic` | BCB SGS 11 | Daily |
| `rate.cdi` | `https://signed-data.org/vocab/finance-brazil/rate-cdi` | BCB SGS 4391 | Daily |
| `index.ipca` | `https://signed-data.org/vocab/finance-brazil/index-ipca` | BCB SGS 432+433 | Monthly |
| `index.igpm` | `https://signed-data.org/vocab/finance-brazil/index-igpm` | BCB SGS 189 | Monthly |
| `fx.usd-brl` | `https://signed-data.org/vocab/finance-brazil/fx-usd-brl` | BCB SGS 1+2 | Daily |
| `fx.eur-brl` | `https://signed-data.org/vocab/finance-brazil/fx-eur-brl` | BCB SGS 21619 | Daily |
| `quote.stock` | `https://signed-data.org/vocab/finance-brazil/quote-stock` | Brapi | Real-time |
| `quote.fii` | `https://signed-data.org/vocab/finance-brazil/quote-fii` | Brapi | Real-time |
| `quote.crypto` | `https://signed-data.org/vocab/finance-brazil/quote-crypto` | Brapi | Real-time |
| `decision.copom` | `https://signed-data.org/vocab/finance-brazil/decision-copom` | BCB | ~8x/year |

## Ingestor Pattern

Event-driven with scheduled triggers during market hours. Stock and crypto
quotes are fetched on-demand by the MCP server (no scheduled ingestor).

## Language

All events use `lang: "pt-BR"`.
