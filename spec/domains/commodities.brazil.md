# CDS Domain Specification — `commodities.brazil`

**Version:** 1.0.0
**Domain URI:** `https://signed-data.org/vocab/commodities-brazil/`
**Status:** Active
**Date:** 2026-04-03

---

## Overview

The `commodities.brazil` domain provides certified, signed data feeds for
Brazilian commodity markets. Sources include B3 futures contracts via Brapi,
physical crop prices from CONAB, and international benchmarks from the
World Bank.

## Data Sources

| Source | URI | Auth | License | Notes |
|---|---|---|---|---|
| Brapi (B3 futures) | `https://signed-data.org/sources/brapi.dev.v1` | none | MIT | Real-time futures |
| CONAB | `https://signed-data.org/sources/conab.gov.br.v1` | none | public | Unofficial API, defensive parsing required |
| World Bank | `https://signed-data.org/sources/api.worldbank.org.v2` | none | CC BY 4.0 | Monthly benchmarks |

## Content Types

| Schema | Content Type URI | Source | Cadence |
|---|---|---|---|
| `futures.soja` | `.../commodities-brazil/futures-soja` | B3/Brapi | Real-time |
| `futures.milho` | `.../commodities-brazil/futures-milho` | B3/Brapi | Real-time |
| `futures.boi-gordo` | `.../commodities-brazil/futures-boi-gordo` | B3/Brapi | Real-time |
| `futures.cafe` | `.../commodities-brazil/futures-cafe` | B3/Brapi | Real-time |
| `futures.acucar` | `.../commodities-brazil/futures-acucar` | B3/Brapi | Real-time |
| `futures.etanol` | `.../commodities-brazil/futures-etanol` | B3/Brapi | Real-time |
| `spot.soja` | `.../commodities-brazil/spot-soja` | CONAB | Weekly |
| `spot.milho` | `.../commodities-brazil/spot-milho` | CONAB | Weekly |
| `spot.trigo` | `.../commodities-brazil/spot-trigo` | CONAB | Weekly |
| `spot.algodao` | `.../commodities-brazil/spot-algodao` | CONAB | Weekly |
| `index.worldbank` | `.../commodities-brazil/index-worldbank` | World Bank | Monthly |

## CONAB API Limitation

CONAB's web service is not a formal public API. It is the backend of their
web interface. The ingestor uses defensive parsing with a `last_known_good`
fallback. If the endpoint structure changes, the ingestor fails gracefully
and logs an alert rather than emitting corrupted data.

## CEPEA Exclusion

CEPEA/Esalq data is excluded because it requires scraping, which violates
the CDS principle: no scraping. CEPEA will be added if a proper API is
published.

## Language

All events use `lang: "pt-BR"`.
