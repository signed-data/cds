# Getting started

This guide takes you from zero to a running CDS pipeline in under 10 minutes.
You will generate a signing keypair, ingest your first signed event, and verify it.

---

## Prerequisites

- Python 3.12+ **or** Node.js 20+
- 5 minutes

---

## Step 1 — Install the SDK

**Python**
```bash
pip install signeddata-cds
```

**TypeScript**
```bash
npm install @signeddata/cds-sdk
```

---

## Step 2 — Generate a keypair

Every CDS producer needs an RSA-4096 keypair. Generate one:

**Python**
```python
from cds import generate_keypair
import os

os.makedirs("keys", exist_ok=True)
generate_keypair("keys/private.pem", "keys/public.pem")
```

**TypeScript**
```typescript
import { generateKeypair } from "@signeddata/cds-sdk";
import { mkdirSync } from "node:fs";

mkdirSync("keys", { recursive: true });
generateKeypair("keys/private.pem", "keys/public.pem");
```

> **Security:** `keys/private.pem` is your trust anchor. Add `keys/` to `.gitignore` immediately.
> In production, store it in AWS Secrets Manager, Azure Key Vault, or similar.

---

## Step 3 — Build your first event

**Python**
```python
from cds import CDSSigner, CDSEvent, SourceMeta, ContextMeta
from cds import CDSVocab, CDSSources
from datetime import datetime, timezone

signer = CDSSigner("keys/private.pem", issuer="https://myorg.example.com")

event = CDSEvent(
    content_type  = CDSVocab.WEATHER_CURRENT,
    source        = SourceMeta(id=CDSSources.OPEN_METEO),
    occurred_at   = datetime.now(timezone.utc),
    lang          = "en",
    payload       = {
        "location":    { "city": "London", "lat": 51.51, "lon": -0.13 },
        "temperature": { "current": 14.0, "feels_like": 12.0 },
        "condition":   "overcast",
    },
    event_context = ContextMeta(
        summary = "London: overcast, 14C (feels 12C).",
        model   = "rule-based-v1",
    ),
)

signer.sign(event)
print(event.integrity.hash)      # sha256:...
print(event.integrity.signed_by) # https://myorg.example.com
```

**TypeScript**
```typescript
import { CDSEvent, CDSSigner, CDSVocab, CDSSources } from "@signeddata/cds-sdk";

const signer = new CDSSigner("keys/private.pem", "https://myorg.example.com");

const event = new CDSEvent({
  content_type: CDSVocab.WEATHER_CURRENT,
  source:       { "@id": CDSSources.OPEN_METEO },
  occurred_at:  new Date(),
  lang:         "en",
  payload:      {
    location:    { city: "London", lat: 51.51, lon: -0.13 },
    temperature: { current: 14.0, feels_like: 12.0 },
    condition:   "overcast",
  },
  context: {
    summary:      "London: overcast, 14C (feels 12C).",
    model:        "rule-based-v1",
    generated_at: new Date().toISOString(),
  },
});

signer.sign(event);
console.log(event.toJSON());  // JSON-LD with @context, @type, @id
```

---

## Step 4 — Verify an event

The consumer only needs your **public** key.

**Python**
```python
from cds import CDSVerifier

verifier = CDSVerifier("keys/public.pem")

try:
    verifier.verify(event)
    print("Valid — data is authentic and unmodified")
except Exception as e:
    print(f"Invalid — {e}")
```

Modify any field in the payload and verify again — the signature will be rejected:

```python
event.payload["temperature"]["current"] = 99.0  # tamper!
verifier.verify(event)  # raises: Hash mismatch
```

---

## Step 5 — Use a built-in ingestor

CDS ships with ingestors for several domains. They handle HTTP, parsing,
fingerprinting, and signing automatically.

### Weather (Open-Meteo — no API key)

```python
from cds import CDSSigner
from cds.sources.weather import WeatherIngestor
import asyncio

signer   = CDSSigner("keys/private.pem", issuer="https://myorg.example.com")
ingestor = WeatherIngestor(signer=signer)

events = asyncio.run(ingestor.ingest())
for e in events:
    print(e.event_context.summary)
```

### Football (api-football.com — free plan: 100 req/day)

```python
from cds.sources.football import FootballIngestor, LEAGUE_IDS

ingestor = FootballIngestor(
    signer=signer,
    api_key="YOUR_API_KEY",
    league_ids=[LEAGUE_IDS["brasileirao_a"], LEAGUE_IDS["libertadores"]],
    season=2026,
)

events = asyncio.run(ingestor.ingest())
for e in events:
    print(e.event_context.summary)
```
### Other sources

Additional data sources (for example, lotteries or weather) will be documented here as they become available in the SDK.

---

## Step 6 — Use with Claude (MCP)

If you want to give Claude access to signed CDS data, you can use a Model Context Protocol (MCP) server.

Refer to the documentation of the specific CDS source package you are using for the recommended MCP server and installation instructions.

Once configured, add the MCP server to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`) under `mcpServers`, following the MCP server's README.
---

## Next steps

- [Architecture](architecture.md) — how the full pipeline works
- [Linked Data](linked-data.md) — why every event is valid JSON-LD
- [Signing algorithm](signing.md) — the cryptographic details
- [Content types](content-types.md) — the URI-based type system
- [Self-hosting](self-hosting.md) — run your own infrastructure
- [Spec v0.2.0](../spec/CDS-v0.2.0.md) — the formal specification
