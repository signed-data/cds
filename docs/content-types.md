# Content types

CDS extends the MIME vendor extension convention to carry semantic meaning
alongside format information.

---

## The problem with existing approaches

`Content-Type: application/json` tells you the format. It says nothing about
what is inside.

`file.pdf`, `data.xml`, `response.json` — the extension or MIME type tells you
how to deserialise, not what you are deserialising.

In practice, APIs document their schemas out-of-band. Consumers parse the
response, then infer the meaning from context. Type information is lost in transit.

---

## CDS content types

```
application/vnd.cds.{domain}.{schema}+{encoding};v={version}
```

Every CDS content type encodes:

| Part | Meaning | Example |
|---|---|---|
| `vnd.cds` | Vendor prefix — identifies the CDS standard | fixed |
| `{domain}` | Semantic domain | `lottery-brazil` |
| `{schema}` | Event schema within the domain | `mega-sena-result` |
| `{encoding}` | Wire format | `json` |
| `v={version}` | Schema version | `1` |

Examples:

```
application/vnd.cds.lottery-brazil.mega-sena-result+json;v=1
application/vnd.cds.sports-football.match-result+json;v=1
application/vnd.cds.weather.forecast-current+json;v=1
application/vnd.cds.news.headline+json;v=1
```

---

## Using content types in code

**Python**
```python
from cds.schema import CDSContentType
from cds.sources.lottery_models import LotteryContentTypes

# Create
ct = CDSContentType(domain="lottery.brazil", schema_name="mega-sena.result")
print(ct.mime_type)
# application/vnd.cds.lottery-brazil.mega-sena-result+json;v=1

# Pre-built constants
ct = LotteryContentTypes.MEGA_SENA
ct = LotteryContentTypes.LOTOFACIL

# On an event
event.content_type.domain      # "lottery.brazil"
event.content_type.schema_name # "mega-sena.result"
event.domain                   # shortcut → "lottery.brazil"
event.event_type               # shortcut → "mega-sena.result"
```

**TypeScript**
```typescript
import { CDSContentType } from "@signeddata/cds-sdk";
import { LotteryContentTypes } from "@signeddata/cds-sdk";

const ct = new CDSContentType({ domain: "lottery.brazil", schema_name: "mega-sena.result" });
console.log(ct.mime_type);
// application/vnd.cds.lottery-brazil.mega-sena-result+json;v=1

const ct2 = LotteryContentTypes.MEGA_SENA;
```

---

## Routing by content type

Because the content type is part of the event envelope, systems can route
events without inspecting the payload:

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

**PAYLOAD_REGISTRY (auto-deserialise):**
```python
from cds.sources.lottery_models import PAYLOAD_REGISTRY

model_class = PAYLOAD_REGISTRY[event.content_type]
payload = model_class(**event.payload)
```

---

## Versioning

The `v=` parameter versions the **payload schema**, not the CDS envelope.
The envelope spec version is in `spec_version`.

When a domain schema changes in a breaking way (field renamed, type changed,
field removed), the version increments:

```
application/vnd.cds.weather.forecast-current+json;v=1  →  current
application/vnd.cds.weather.forecast-current+json;v=2  →  future breaking change
```

Non-breaking additions (new optional fields) do not increment the version.

---

## Naming conventions

- Domain: `lowercase`, dots for hierarchy → `sports.football`, `government.brazil`
- Schema name: `lowercase`, dots for sub-type → `match.result`, `mega-sena.result`
- In MIME type: dots become hyphens (MIME restriction) → `sports-football`, `mega-sena-result`
- In code: use the pre-built constants (e.g. `LotteryContentTypes.MEGA_SENA`)
  rather than constructing strings manually

---

## Registering a new content type

To add a new domain or schema to the standard:

1. Open an issue with the `domain-proposal` label
2. Include: data source, sample response, draft payload schema
3. Create a PR adding `spec/domains/{domain}.md`
4. Add models and ingestor to the SDK

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full process.
