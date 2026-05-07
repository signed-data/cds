# Migration Guide: CDS v0.1.0 to v0.2.0

This document covers all breaking changes introduced in CDS v0.2.0 and provides concrete migration examples for the Python and TypeScript SDKs.

---

## 1. Breaking changes

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

## 2. Python SDK migration

### content_type: object to URI

**Before (v0.1.0):**

```python
from cds.schema import CDSContentType

content_type = CDSContentType(
    domain="lottery.brazil",
    schema_name="mega-sena.result",
    version="1",
    encoding="json",
)
event = CDSEvent(content_type=content_type, ...)
```

**After (v0.2.0):**

```python
from cds.vocab import CDSVocab

event = CDSEvent(content_type=CDSVocab.LOTTERY_MEGA_SENA, ...)
# content_type is now a URI string:
# "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"
```

If you were reading the domain or schema from the content type object, use the new helper properties:

```python
# Before
event.content_type.domain       # "lottery.brazil"
event.content_type.schema_name  # "mega-sena.result"

# After
event.domain      # "lottery.brazil"    (computed from URI)
event.event_type  # "mega-sena.result"  (computed from URI)
```

### source: id to @id

**Before (v0.1.0):**

```python
from cds.schema import SourceMeta

source = SourceMeta(id="caixa.gov.br.loterias.v1", fingerprint="sha256:...")
```

**After (v0.2.0):**

```python
from cds.schema import SourceMeta
from cds.vocab import CDSSources

source = SourceMeta(id=CDSSources.CAIXA_LOTERIAS, fingerprint="sha256:...")
# Serialises to JSON as:
# { "@id": "https://signed-data.org/sources/caixa.gov.br.loterias.v1", "fingerprint": "sha256:..." }
```

Note: in the Python SDK, the `SourceMeta` constructor still uses `id=` as the keyword argument. The `@id` alias is applied during JSON serialisation via Pydantic's `alias="@id"`.

### context field: renamed to event_context

**Before (v0.1.0):**

```python
event.context.summary
event.context.model
```

**After (v0.2.0):**

```python
event.event_context.summary
event.event_context.model
```

The JSON key in the serialised output is still `"context"` (via Pydantic alias). The Python attribute was renamed to `event_context` to avoid shadowing Pydantic internals. If you are reading from raw JSON/dict, the key is still `"context"`.

### integrity.signed_by: bare domain to full URI

**Before (v0.1.0):**

```python
assert event.integrity.signed_by == "signed-data.org"
```

**After (v0.2.0):**

```python
assert event.integrity.signed_by == "https://signed-data.org"
```

### Full example

```python
from datetime import datetime, timezone
from cds.schema import CDSEvent, SourceMeta, ContextMeta
from cds.vocab import CDSVocab, CDSSources

event = CDSEvent(
    content_type  = CDSVocab.LOTTERY_MEGA_SENA,
    source        = SourceMeta(id=CDSSources.CAIXA_LOTERIAS, fingerprint="sha256:b310..."),
    occurred_at   = datetime.now(timezone.utc),
    lang          = "pt-BR",
    payload       = {"concurso": 2800, "dezenas": ["03", "17", "25", "38", "44", "55"]},
    event_context = ContextMeta(summary="Mega Sena concurso 2800 resultado..."),
)

jsonld = event.to_jsonld()
# jsonld["@context"] == "https://signed-data.org/contexts/cds/v1.jsonld"
# jsonld["@type"]    == "https://signed-data.org/vocab/CuratedDataEvent"
# jsonld["@id"]      == "https://signed-data.org/events/<uuid>"
```

---

## 3. TypeScript SDK migration

### content_type: object to URI

**Before (v0.1.0):**

```typescript
import { CDSContentType } from "@signeddata/cds-sdk";

const contentType = new CDSContentType({
  domain: "lottery.brazil",
  schema_name: "mega-sena.result",
  version: "1",
  encoding: "json",
});
const event = new CDSEvent({ content_type: contentType, ... });
```

**After (v0.2.0):**

```typescript
import { CDSEvent } from "@signeddata/cds-sdk";
import { CDSVocab } from "@signeddata/cds-sdk";

const event = new CDSEvent({
  content_type: CDSVocab.LOTTERY_MEGA_SENA,
  // "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"
  ...
});
```

Note: `event.content_type` is now a `string` (was a `CDSContentType` object). If you were accessing `event.content_type.domain`, use the new getter:

```typescript
// Before
event.content_type.domain       // "lottery.brazil"
event.content_type.schema_name  // "mega-sena.result"

// After
event.domain      // "lottery.brazil"    (computed from URI)
event.event_type  // "mega-sena.result"  (computed from URI)
```

### source: id to @id

**Before (v0.1.0):**

```typescript
const source = { id: "caixa.gov.br.loterias.v1", fingerprint: "sha256:..." };
```

**After (v0.2.0):**

```typescript
import { CDSSources } from "@signeddata/cds-sdk";

const source = {
  "@id": CDSSources.CAIXA_LOTERIAS,
  // "https://signed-data.org/sources/caixa.gov.br.loterias.v1"
  fingerprint: "sha256:...",
};
```

The `SourceMeta` interface now uses `"@id"` instead of `id`. This is a breaking change in the object shape.

### integrity.signed_by: bare domain to full URI

**Before (v0.1.0):**

```typescript
event.integrity.signed_by === "signed-data.org"
```

**After (v0.2.0):**

```typescript
event.integrity.signed_by === "https://signed-data.org"
```

### Full example

```typescript
import { CDSEvent } from "@signeddata/cds-sdk";
import { CDSVocab, CDSSources } from "@signeddata/cds-sdk";

const event = new CDSEvent({
  content_type: CDSVocab.LOTTERY_MEGA_SENA,
  source: {
    "@id": CDSSources.CAIXA_LOTERIAS,
    fingerprint: "sha256:b310...",
  },
  occurred_at: new Date(),
  lang: "pt-BR",
  payload: { concurso: 2800, dezenas: ["03", "17", "25", "38", "44", "55"] },
  context: {
    summary: "Mega Sena concurso 2800 resultado...",
    model: "rule-based-v1",
    generated_at: new Date().toISOString(),
  },
});

const json = event.toJSON();
// json["@context"] === "https://signed-data.org/contexts/cds/v1.jsonld"
// json["@type"]    === "https://signed-data.org/vocab/CuratedDataEvent"
// json["@id"]      === "https://signed-data.org/events/<uuid>"
```

---

## 4. Signature compatibility

**v0.1.0 events cannot be verified by a v0.2.0 verifier.** The canonical bytes used for signing differ between versions:

- **v0.1.0 canonical bytes:** JSON-serialised event excluding `integrity` and `ingested_at`. Does not include `@context`, `@type`, or `@id` (these fields did not exist).
- **v0.2.0 canonical bytes:** JSON-serialised event excluding `integrity` and `ingested_at`. Includes `@context`, `@type`, and `@id`.

Because the canonical byte representations differ, a signature produced under v0.1.0 will not match the canonical bytes computed by a v0.2.0 verifier. The hash will differ, and RSA-PSS verification will fail.

If you need to verify historical v0.1.0 events, you must use a v0.1.0-compatible verifier that computes canonical bytes without the `@context`, `@type`, and `@id` fields.

---

## 5. v0.1.0 event validity

v0.1.0 events remain valid under their own specification. The CDS v0.1.0 spec is not retracted or deprecated — it simply does not support Linked Data features. A v0.1.0 event with `spec_version: "0.1.0"` can still be verified using v0.1.0 canonical byte rules and the same RSA-PSS algorithm.

Consumers SHOULD check the `spec_version` field to determine which canonical byte computation to use during verification:

```python
# Python
if event_data["spec_version"] == "0.1.0":
    # use v0.1.0 canonical bytes (no @context/@type/@id)
    pass
elif event_data["spec_version"] == "0.2.0":
    # use v0.2.0 canonical bytes (includes @context/@type/@id)
    pass
```

```typescript
// TypeScript
if (eventData.spec_version === "0.1.0") {
  // use v0.1.0 canonical bytes (no @context/@type/@id)
} else if (eventData.spec_version === "0.2.0") {
  // use v0.2.0 canonical bytes (includes @context/@type/@id)
}
```
