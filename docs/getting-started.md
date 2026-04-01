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
# ✅ keys/private.pem — keep this secret, never commit
# ✅ keys/public.pem  — distribute this to your consumers
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

You can sign any structured data as a CDS event. Here is a minimal example
using a custom domain before we get to the built-in ingestors.

**Python**
```python
from cds import CDSSigner, CDSEvent, CDSContentType, SourceMeta, ContextMeta
from datetime import datetime, timezone

signer = CDSSigner("keys/private.pem", issuer="myorg.example.com")

event = CDSEvent(
    content_type = CDSContentType(domain="weather", schema_name="forecast.current"),
    source       = SourceMeta(id="open-meteo.com.v1"),
    occurred_at  = datetime.now(timezone.utc),
    lang         = "en",
    payload      = {
        "location":    { "city": "London", "lat": 51.51, "lon": -0.13 },
        "temperature": { "current": 14.0, "feels_like": 12.0 },
        "condition":   "overcast",
    },
    context = ContextMeta(
        summary = "London: overcast, 14°C (feels 12°C).",
        model   = "rule-based-v1",
    ),
)

signer.sign(event)
print(event.integrity.hash)      # sha256:...
print(event.integrity.signed_by) # myorg.example.com
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
    print("✅ Valid — data is authentic and unmodified")
except Exception as e:
    print(f"❌ Invalid — {e}")
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
    print(e.context.summary)
```

### Other sources

Additional data sources (for example, lotteries or weather) will be documented
here as they become available in the SDK.

---

## Step 6 — Use with Claude (MCP)

If you want to give Claude access to signed CDS data, install the MCP server:

```bash
pip install signeddata-mcp-lottery
```

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "lottery": {
      "command": "signeddata-mcp-lottery",
      "env": {
        "CDS_PRIVATE_KEY_PATH": "/path/to/keys/private.pem",
        "CDS_ISSUER": "myorg.example.com"
      }
    }
  }
}
```

Claude can now call `get_mega_sena_latest`, `check_mega_sena_ticket`, and more.

---

## Next steps

- [Architecture](architecture.md) — how the full pipeline works
- [Signing algorithm](signing.md) — the cryptographic details
- [Content types](content-types.md) — the MIME type system
- [Self-hosting](self-hosting.md) — run your own infrastructure
- [Spec v0.1.0](../spec/CDS-v0.1.0.md) — the formal specification
