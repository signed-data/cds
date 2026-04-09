# Curated Data Standard (CDS) — Specification v0.2.0

**Status:** Draft
**Issuer:** SignedData.Org
**Website:** https://signed-data.org
**License:** MIT
**Supersedes:** CDS v0.1.0

---

## 1. Overview

The Curated Data Standard (CDS) is an open standard for distributing curated, cryptographically signed, real-time data from verified sources. Version 0.2.0 converts all identities — events, sources, content types — to dereferenceable HTTP URIs, making every CDS event valid JSON-LD. With this change, every CDS event becomes 5-star Linked Data: machine-readable, openly licensed, structured in a non-proprietary format, described using W3C standards, and linked to other people's data via URIs.

Key properties of a CDS event remain unchanged:

- **Typed** — carries a `content_type` URI identifying the domain and schema
- **Signed** — RSA-PSS SHA-256 signature by the producer, verifiable by any consumer
- **Fingerprinted** — SHA-256 of the raw upstream API response, proving source bytes were not altered
- **Enriched** — optional LLM-generated `context.summary` in the declared language
- **Linked** — every entity is a dereferenceable HTTP URI returning JSON-LD (NEW in v0.2.0)

---

## 2. Linked Data principles

CDS v0.2.0 is designed to satisfy the four Linked Data rules articulated by Tim Berners-Lee.

### Rule 1: Use URIs as names for things

CDS names every entity with a URI. Events are identified by `https://signed-data.org/events/{uuid}`, content types by `https://signed-data.org/vocab/{domain}/{schema}`, and sources by `https://signed-data.org/sources/{source-id}`. These URIs are globally unique, unambiguous identifiers that can be used by any system on the web to refer to the same concept without coordination.

### Rule 2: Use HTTP URIs so that people can look up those names

All CDS URIs use the `https://signed-data.org` base. They are not opaque identifiers or URNs — they are HTTP(S) URIs that resolve to real endpoints on the web. Any agent, human or machine, can dereference a CDS URI by issuing a standard HTTP GET request and expect a meaningful response.

### Rule 3: When someone looks up a URI, provide useful information using the standards (RDF, SPARQL)

When a CDS URI is dereferenced, the server returns a JSON-LD document describing the resource. For example, dereferencing a source URI returns the source's name, description, upstream URL, and version. Dereferencing a content type URI returns the schema definition, domain, and related types. Because JSON-LD is a serialisation of RDF, this information is natively consumable by semantic web tools, SPARQL endpoints, and knowledge graphs.

### Rule 4: Include links to other URIs so that they can discover more things

CDS events contain links to other CDS resources. An event's `source.@id` links to a source document, which in turn links to the upstream domain. An event's `content_type` links to a vocabulary entry that describes the schema and its domain. The `@context` links to a JSON-LD context document that maps all keys to RDF predicates. This web of links allows crawlers and consumers to navigate from any single event to the full CDS knowledge graph.

---

## 3. 5-star open data rating

CDS v0.2.0 achieves the maximum 5-star open data rating as defined by Tim Berners-Lee:

```
★       Available online under an open license              ✓ (v0.1.0)
★★      Structured data (not a scanned image)               ✓ (v0.1.0)
★★★     Non-proprietary format (JSON)                       ✓ (v0.1.0)
★★★★    Use open W3C standards to identify things (JSON-LD)  ✓ NEW in v0.2.0
★★★★★   Link to other people's data (URI links)             ✓ NEW in v0.2.0
```

v0.1.0 already satisfied the first three stars. By introducing `@context`, `@type`, `@id`, and converting all identifiers to HTTP URIs, v0.2.0 adds the fourth and fifth stars.

---

## 4. Event envelope

Every CDS v0.2.0 event is a valid JSON-LD document:

```json
{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@type":    "https://signed-data.org/vocab/CuratedDataEvent",
  "@id":      "https://signed-data.org/events/a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d",
  "spec_version": "0.2.0",
  "id":           "a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d",
  "content_type": "https://signed-data.org/vocab/lottery-brazil/mega-sena-result",
  "source": {
    "@id":         "https://signed-data.org/sources/caixa.gov.br.loterias.v1",
    "fingerprint": "sha256:b310..."
  },
  "occurred_at":  "2026-03-29T00:00:00Z",
  "ingested_at":  "2026-03-29T00:00:04Z",
  "lang":         "pt-BR",
  "payload":      { },
  "context": {
    "summary":      "Mega Sena concurso 2800...",
    "model":        "rule-based-v1",
    "generated_at": "2026-03-29T00:00:05Z"
  },
  "integrity": {
    "hash":      "sha256:a1b2c3...",
    "signature": "MX6rj3...",
    "signed_by": "https://signed-data.org"
  }
}
```

The `@context`, `@type`, and `@id` fields MUST appear first in serialised output. The `id` field (plain UUID) is retained alongside `@id` (full URI) for convenience.

---

## 5. Field reference

| Field | v0.1.0 | v0.2.0 | Change |
|---|---|---|---|
| `@context` | absent | `"https://signed-data.org/contexts/cds/v1.jsonld"` | new |
| `@type` | absent | `"https://signed-data.org/vocab/CuratedDataEvent"` | new |
| `@id` | absent | `"https://signed-data.org/events/{uuid}"` | new |
| `spec_version` | `"0.1.0"` | `"0.2.0"` | bumped |
| `content_type` | `CDSContentType` object | URI string | **breaking** |
| `source.id` | opaque string | absent | **removed** |
| `source.@id` | absent | HTTP URI | **replaces** `source.id` |
| `integrity.signed_by` | `"signed-data.org"` | `"https://signed-data.org"` | **breaking** |

---

## 6. URI scheme

All CDS URIs share the base `https://signed-data.org`.

| Resource | Pattern | Example |
|---|---|---|
| Event | `/events/{uuid}` | `https://signed-data.org/events/a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d` |
| Content type | `/vocab/{domain-slug}/{schema-slug}` | `https://signed-data.org/vocab/lottery-brazil/mega-sena-result` |
| Source | `/sources/{source-id}` | `https://signed-data.org/sources/caixa.gov.br.loterias.v1` |
| Vocabulary root | `/vocab/` | `https://signed-data.org/vocab/` |
| JSON-LD context | `/contexts/cds/v1.jsonld` | `https://signed-data.org/contexts/cds/v1.jsonld` |
| Public key | `/.well-known/cds-public-key.pem` | `https://signed-data.org/.well-known/cds-public-key.pem` |

**Domain slugs**: dots in the domain name are replaced with hyphens. `lottery.brazil` becomes `lottery-brazil`. `sports.football` becomes `sports-football`.

**Schema slugs**: dots in the schema name are replaced with hyphens. `mega-sena.result` becomes `mega-sena-result`.

**Source IDs**: dots are kept as-is. `caixa.gov.br.loterias.v1` stays `caixa.gov.br.loterias.v1`.

---

## 7. Content type URIs

### URI pattern

```
https://signed-data.org/vocab/{domain-slug}/{schema-slug}
```

Where:
- `{domain-slug}` is the domain with dots replaced by hyphens
- `{schema-slug}` is the schema name with dots replaced by hyphens

The builder function signature is: `content_type_uri(domain, schema_name)` where both arguments use the original dot notation.

### Registered content types

#### lottery-brazil

| Constant | URI |
|---|---|
| `LOTTERY_MEGA_SENA` | `https://signed-data.org/vocab/lottery-brazil/mega-sena-result` |
| `LOTTERY_LOTOFACIL` | `https://signed-data.org/vocab/lottery-brazil/lotofacil-result` |
| `LOTTERY_QUINA` | `https://signed-data.org/vocab/lottery-brazil/quina-result` |
| `LOTTERY_LOTOMANIA` | `https://signed-data.org/vocab/lottery-brazil/lotomania-result` |
| `LOTTERY_DUPLA_SENA` | `https://signed-data.org/vocab/lottery-brazil/dupla-sena-result` |

#### sports-football

| Constant | URI |
|---|---|
| `FOOTBALL_MATCH_RESULT` | `https://signed-data.org/vocab/sports-football/match-result` |
| `FOOTBALL_MATCH_LIVE` | `https://signed-data.org/vocab/sports-football/match-live` |
| `FOOTBALL_STANDINGS` | `https://signed-data.org/vocab/sports-football/standings-update` |

#### weather

| Constant | URI |
|---|---|
| `WEATHER_CURRENT` | `https://signed-data.org/vocab/weather/forecast-current` |
| `WEATHER_DAILY` | `https://signed-data.org/vocab/weather/forecast-daily` |
| `WEATHER_ALERT` | `https://signed-data.org/vocab/weather/alert-severe` |

#### news

| Constant | URI |
|---|---|
| `NEWS_HEADLINE` | `https://signed-data.org/vocab/news/headline` |
| `NEWS_BREAKING` | `https://signed-data.org/vocab/news/breaking` |
| `NEWS_SUMMARY` | `https://signed-data.org/vocab/news/summary` |

#### finance

| Constant | URI |
|---|---|
| `FINANCE_STOCK` | `https://signed-data.org/vocab/finance/quote-stock` |
| `FINANCE_CRYPTO` | `https://signed-data.org/vocab/finance/quote-crypto` |
| `FINANCE_FOREX` | `https://signed-data.org/vocab/finance/quote-forex` |
| `FINANCE_INDEX` | `https://signed-data.org/vocab/finance/index-update` |

#### religion-bible

| Constant | URI |
|---|---|
| `BIBLE_VERSE` | `https://signed-data.org/vocab/religion-bible/verse` |
| `BIBLE_PASSAGE` | `https://signed-data.org/vocab/religion-bible/passage` |
| `BIBLE_DAILY` | `https://signed-data.org/vocab/religion-bible/daily` |

#### government-brazil

| Constant | URI |
|---|---|
| `GOV_BR_DIARIO` | `https://signed-data.org/vocab/government-brazil/diario-oficial` |
| `GOV_BR_LICITACAO` | `https://signed-data.org/vocab/government-brazil/licitacao` |
| `GOV_BR_LEI` | `https://signed-data.org/vocab/government-brazil/lei` |

---

## 8. Source registry

A source represents a verified upstream data provider. Each source is identified by a URI of the form `https://signed-data.org/sources/{source-id}`.

### Source document

Dereferencing a source URI (e.g., `GET https://signed-data.org/sources/caixa.gov.br.loterias.v1`) returns a JSON-LD document:

```json
{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@type":    "https://signed-data.org/vocab/DataSource",
  "@id":      "https://signed-data.org/sources/caixa.gov.br.loterias.v1",
  "name":     "Caixa Economica Federal — Loterias",
  "domain":   "caixa.gov.br",
  "version":  "v1",
  "upstream": "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena",
  "content_types": [
    "https://signed-data.org/vocab/lottery-brazil/mega-sena-result",
    "https://signed-data.org/vocab/lottery-brazil/lotofacil-result",
    "https://signed-data.org/vocab/lottery-brazil/quina-result"
  ]
}
```

### Registered sources

| Constant | Source URI |
|---|---|
| `CAIXA_LOTERIAS` | `https://signed-data.org/sources/caixa.gov.br.loterias.v1` |
| `API_FOOTBALL` | `https://signed-data.org/sources/api-football.com.v3` |
| `OPEN_METEO` | `https://signed-data.org/sources/open-meteo.com.v1` |
| `BRAPI` | `https://signed-data.org/sources/brapi.dev.v1` |
| `BIBLE_API` | `https://signed-data.org/sources/bible-api.com.v1` |

---

## 9. Vocabulary

The CDS ontology is published at `https://signed-data.org/vocab/`. It defines the classes and properties used in CDS events.

### Classes

| Class | URI | Description |
|---|---|---|
| `CuratedDataEvent` | `https://signed-data.org/vocab/CuratedDataEvent` | The top-level event envelope |
| `IntegrityMeta` | `https://signed-data.org/vocab/IntegrityMeta` | Cryptographic proof attached to an event |
| `DataSource` | `https://signed-data.org/vocab/DataSource` | A registered upstream data provider |

### Properties

| Property | URI | Domain | Range | Description |
|---|---|---|---|---|
| `specVersion` | `https://signed-data.org/vocab/specVersion` | `CuratedDataEvent` | `xsd:string` | Semver spec version |
| `contentType` | `https://signed-data.org/vocab/contentType` | `CuratedDataEvent` | URI | Links to a content type vocabulary entry |
| `source` | `https://signed-data.org/vocab/source` | `CuratedDataEvent` | `DataSource` | Links to the data source |
| `occurredAt` | `https://signed-data.org/vocab/occurredAt` | `CuratedDataEvent` | `xsd:dateTime` | When the upstream event occurred |
| `ingestedAt` | `https://signed-data.org/vocab/ingestedAt` | `CuratedDataEvent` | `xsd:dateTime` | When CDS ingested the event |
| `lang` | `https://signed-data.org/vocab/lang` | `CuratedDataEvent` | `xsd:string` | BCP-47 language tag |
| `payload` | `https://signed-data.org/vocab/payload` | `CuratedDataEvent` | JSON object | Domain-specific data |
| `context` | `https://signed-data.org/vocab/context` | `CuratedDataEvent` | JSON object | LLM-generated summary and metadata |
| `hash` | `https://signed-data.org/vocab/hash` | `IntegrityMeta` | `xsd:string` | SHA-256 of canonical bytes |
| `signature` | `https://signed-data.org/vocab/signature` | `IntegrityMeta` | `xsd:string` | Base64-encoded RSA-PSS signature |
| `signedBy` | `https://signed-data.org/vocab/signedBy` | `IntegrityMeta` | URI | The signing authority |
| `fingerprint` | `https://signed-data.org/vocab/fingerprint` | `DataSource` | `xsd:string` | SHA-256 of raw upstream response |

---

## 10. Signing algorithm

1. Serialise to canonical JSON — `sort_keys=True`, UTF-8, excluding `integrity` and `ingested_at`
2. `hash = "sha256:" + SHA256(canonical_bytes).hexdigest()`
3. Sign `canonical_bytes` with **RSA-PSS** (SHA-256 digest, MGF1, max salt length)
4. Encode signature as base64
5. Attach `IntegrityMeta { hash, signature, signed_by }`

Verification: re-serialise canonical bytes, check hash, verify RSA-PSS signature with the issuer public key published at `https://signed-data.org/.well-known/cds-public-key.pem`.

> **v0.2.0 note:** The canonical bytes now INCLUDE the `@context`, `@type`, and `@id` fields (which did not exist in v0.1.0). The exclusion set remains `integrity` and `ingested_at` only. This means a v0.1.0 event cannot be verified by a v0.2.0 verifier, and vice versa, because the canonical bytes differ.

---

## 11. JSON-LD compatibility

Every CDS v0.2.0 event is valid JSON-LD. The `@context` field at `https://signed-data.org/contexts/cds/v1.jsonld` maps the snake_case JSON keys used by CDS to their corresponding RDF predicates in the CDS vocabulary:

```json
{
  "@context": {
    "@vocab":       "https://signed-data.org/vocab/",
    "spec_version": "specVersion",
    "content_type": { "@id": "contentType", "@type": "@id" },
    "source":       { "@id": "source",      "@type": "@id" },
    "occurred_at":  "occurredAt",
    "ingested_at":  "ingestedAt",
    "signed_by":    { "@id": "signedBy",    "@type": "@id" },
    "fingerprint":  "fingerprint",
    "lang":         "lang",
    "payload":      "payload",
    "context":      "context",
    "hash":         "hash",
    "signature":    "signature",
    "integrity":    "integrity"
  }
}
```

This design achieves two goals simultaneously:

1. **Plain JSON consumers are unaffected.** A consumer that ignores `@context`, `@type`, and `@id` can read all other fields exactly as before (with the caveats listed in the breaking changes). No JSON-LD library is required.

2. **RDF consumers get valid triples.** A JSON-LD processor can expand any CDS event into an RDF graph. The `@context` maps `content_type` to `https://signed-data.org/vocab/contentType` with `@type: @id`, telling the processor that the value is a URI, not a string literal. Similarly, `source` and `signed_by` are typed as `@id` so they produce proper RDF links.

---

## 12. Breaking changes from v0.1.0

This section summarises the breaking changes. For detailed migration instructions, code examples, and SDK upgrade guides, see **[MIGRATION-v0.1-to-v0.2.md](MIGRATION-v0.1-to-v0.2.md)**.

| Change | v0.1.0 | v0.2.0 | Impact |
|---|---|---|---|
| `content_type` field type | `CDSContentType` object with `domain`, `schema_name`, `version`, `encoding` | URI string (e.g., `https://signed-data.org/vocab/lottery-brazil/mega-sena-result`) | All code that reads `content_type.domain` or `content_type.schema_name` must change |
| `source.id` renamed to `source.@id` | `source.id` (opaque string) | `source.@id` (HTTP URI) | JSON key change; use SDK helpers |
| `integrity.signed_by` | `"signed-data.org"` (bare domain) | `"https://signed-data.org"` (full URI) | String comparison will break |
| Canonical bytes | Exclude `integrity` and `ingested_at` | Same exclusions, but canonical bytes now include `@context`, `@type`, `@id` | v0.1.0 signatures cannot be verified by v0.2.0 verifiers |
| New required fields | N/A | `@context`, `@type`, `@id` must be present | Producers must include these fields |
