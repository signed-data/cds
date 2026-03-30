# Curated Data Standard (CDS) — Specification v0.1.0

**Status:** Draft  
**Issuer:** SignedData.Org  
**Website:** https://signed-data.org  
**License:** MIT

---

## 1. Overview

The Curated Data Standard (CDS) defines a universal envelope for distributing real-time data from verified sources. Every CDS event is:

- **Typed** — carries a `CDSContentType` encoding domain, schema, and version as a MIME-like string
- **Signed** — RSA-PSS SHA-256 signature by the producer, verifiable by any consumer with the issuer public key
- **Fingerprinted** — SHA-256 of the raw upstream API response, proving the source bytes were not altered
- **Enriched** — optional LLM-generated `context.summary` in the declared language

---

## 2. Event envelope

```json
{
  "spec_version": "0.1.0",
  "id":           "<uuid-v4>",
  "content_type": {
    "domain":      "<string>",
    "schema_name": "<string>",
    "version":     "<string>",
    "encoding":    "json"
  },
  "source": {
    "id":          "<source-id>",
    "fingerprint": "sha256:<hex>"
  },
  "occurred_at":  "<iso8601>",
  "ingested_at":  "<iso8601>",
  "lang":         "<bcp47>",
  "payload":      {},
  "context": {
    "summary":      "<string>",
    "model":        "<string>",
    "generated_at": "<iso8601>"
  },
  "integrity": {
    "hash":      "sha256:<hex>",
    "signature": "<base64-rsa-pss>",
    "signed_by": "<issuer-id>"
  }
}
```

---

## 3. Content type

```
application/vnd.cds.<domain>.<schema>+<encoding>;v=<version>
```

| Domain | MIME example |
|---|---|
| `weather` | `application/vnd.cds.weather.forecast-current+json;v=1` |
| `sports.football` | `application/vnd.cds.sports-football.match-result+json;v=1` |
| `news` | `application/vnd.cds.news.headline+json;v=1` |
| `finance` | `application/vnd.cds.finance.quote-stock+json;v=1` |
| `religion.bible` | `application/vnd.cds.religion-bible.verse+json;v=1` |
| `government.brazil` | `application/vnd.cds.government-brazil.diario-oficial+json;v=1` |

---

## 4. Signing algorithm

1. Serialise to canonical JSON — `sort_keys=True`, UTF-8, excluding `integrity` and `ingested_at`
2. `hash = "sha256:" + SHA256(canonical_bytes).hexdigest()`
3. Sign `canonical_bytes` with **RSA-PSS** (SHA-256 digest, MGF1, max salt length)
4. Encode signature as base64
5. Attach `IntegrityMeta { hash, signature, signed_by }`

Verification: re-serialise canonical bytes, check hash, verify RSA-PSS signature with the issuer public key published at `https://signed-data.org/.well-known/cds-public-key.pem`.

---

## 5. Registered domains

| Domain | Description |
|---|---|
| `weather` | Weather conditions and forecasts |
| `sports.football` | Football matches, standings, player stats |
| `news` | Headlines and articles |
| `finance` | Quotes, prices, market indices |
| `religion.bible` | Bible verses and passages |
| `government.brazil` | Brazilian government data |

---

## 6. SDK conformance

A conformant SDK MUST:

- Implement `CDSEvent` with all required fields
- Implement canonical serialisation excluding `integrity` and `ingested_at`
- Support RSA-PSS SHA-256 signing and verification
- Expose `CDSSigner`, `CDSVerifier`, and `BaseIngestor`

Reference implementations:
- Python: `pip install signeddata-cds`
- TypeScript: `npm install @signeddata/cds-sdk`

---

## 7. Versioning

`spec_version` uses semver. Breaking changes increment the major version. `content_type.version` versions domain schemas independently.
