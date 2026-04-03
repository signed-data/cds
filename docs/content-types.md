# Content types

CDS v0.2.0 uses **URI-based content types** instead of MIME vendor extensions.
Every content type is a dereferenceable HTTP URI that resolves to a JSON-LD
description of the schema.

---

## The problem with opaque types

v0.1.0 used MIME strings like `application/vnd.cds.lottery-brazil.mega-sena-result+json;v=1`.
These were informative but not resolvable — you could not fetch the string to learn
what it described. They were opaque identifiers, not Linked Data.

---

## URI content types (v0.2.0)

```
https://signed-data.org/vocab/{domain-slug}/{schema-slug}
```

Every content type encodes:

| Part | Meaning | Example |
|---|---|---|
| Base | Fixed namespace | `https://signed-data.org/vocab/` |
| `{domain-slug}` | Semantic domain (dots→hyphens) | `lottery-brazil` |
| `{schema-slug}` | Event schema within the domain (dots→hyphens) | `mega-sena-result` |

Examples:

```
https://signed-data.org/vocab/lottery-brazil/mega-sena-result
https://signed-data.org/vocab/sports-football/match-result
https://signed-data.org/vocab/weather/forecast-current
https://signed-data.org/vocab/news/headline
https://signed-data.org/vocab/finance/quote-stock
https://signed-data.org/vocab/religion-bible/verse
https://signed-data.org/vocab/government-brazil/diario-oficial
```

Each URI resolves to a JSON-LD document describing the schema, its domain,
and links to the certified source.

---

## Slug transformation rules

Domain and schema names use dots in code (e.g., `lottery.brazil`, `mega-sena.result`).
In URIs, **all dots become hyphens**:

```
("lottery.brazil",  "mega-sena.result")   → .../vocab/lottery-brazil/mega-sena-result
("sports.football", "match.result")       → .../vocab/sports-football/match-result
("weather",         "forecast.current")   → .../vocab/weather/forecast-current
```

Source URIs are different — **dots are kept**:

```
"caixa.gov.br.loterias.v1" → .../sources/caixa.gov.br.loterias.v1
```

---

## Using content types in code

**Python**
```python
from cds.vocab import CDSVocab, CDSSources, content_type_uri
from cds.sources.lottery_models import LotteryContentTypes

# Pre-built constants
ct = CDSVocab.LOTTERY_MEGA_SENA
ct = LotteryContentTypes.MEGA_SENA   # same value

# Build from domain + schema
ct = content_type_uri("lottery.brazil", "mega-sena.result")
# → "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"

# On an event
event.content_type   # URI string
event.domain         # shortcut → "lottery.brazil"
event.event_type     # shortcut → "mega-sena.result"
```

**TypeScript**
```typescript
import { CDSVocab, contentTypeUri } from "@signeddata/cds-sdk";
import { LotteryContentTypes } from "@signeddata/cds-sdk";

const ct = CDSVocab.LOTTERY_MEGA_SENA;
const ct2 = contentTypeUri("lottery.brazil", "mega-sena.result");
// → "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"
```

---

## Routing by content type

Because the content type is a URI, systems can route events without
inspecting the payload:

**EventBridge rule (domain routing):**
```json
{
  "source": ["cds.lottery.brazil"],
  "detail-type": ["mega-sena.result"]
}
```

**Python consumer:**
```python
if event.domain == "lottery.brazil" and event.event_type == "mega-sena.result":
    result = MegaSenaResult(**event.payload)
```

---

## Dereferencing

A content type URI is not just a label — it resolves to a JSON-LD document:

```bash
curl https://signed-data.org/vocab/lottery-brazil/mega-sena-result
```

Returns the schema definition including its domain, description, and
link to the certified source.

---

## Naming conventions

- Domain: `lowercase`, dots for hierarchy → `sports.football`, `government.brazil`
- Schema name: `lowercase`, dots or hyphens → `match.result`, `mega-sena.result`
- In URIs: all dots become hyphens → `sports-football`, `mega-sena-result`
- In code: use the pre-built constants (e.g., `CDSVocab.LOTTERY_MEGA_SENA`)

---

## Registering a new content type

To add a new domain or schema to the standard:

1. Open an issue with the `domain-proposal` label
2. Include: data source, sample response, draft payload schema
3. Create a PR adding `spec/domains/{domain}.md` and `vocab/domains/{domain}.jsonld`
4. Add models and ingestor to the SDK

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full process.
