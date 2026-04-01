# Architecture

A CDS deployment has four layers. Understanding where each sits
makes it clear why they are separated the way they are.

```
┌─────────────────────────────────────────────────────────┐
│                    Data sources                         │
│   Open-Meteo · api-football.com · Caixa · NewsAPI ...   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (no auth or API key)
┌────────────────────────▼────────────────────────────────┐
│                      Ingestor                           │
│   Fetches · fingerprints · normalises · signs           │
│   CDSSigner(private_key, issuer)                        │
└────────────────────────┬────────────────────────────────┘
                         │ CDSEvent (signed JSON)
┌────────────────────────▼────────────────────────────────┐
│                   Transport / Store                     │
│   S3 (immutable) · SQS · EventBridge · HTTP             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                     Consumer                            │
│   CDSVerifier(public_key) · MCP server · App            │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Data sources

CDS only ingests from APIs with structured, reliable output. No scraping.
Every source is registered in the domain spec with its `source.id` and the
expected response schema.

The raw API response is SHA-256 fingerprinted before parsing:
```
fingerprint = "sha256:" + SHA256(raw_response_bytes).hexdigest()
```

This is stored in `source.fingerprint` — it lets you prove what bytes were
received from the upstream, independent of the normalised payload.

---

## Layer 2 — Ingestor

The ingestor is the only component that holds the **private key**.

Responsibilities:
1. Fetch from source, capture raw bytes
2. Parse and normalise into the domain payload schema
3. Generate `context.summary` via a lightweight LLM (or rule-based logic)
4. Build the `CDSEvent` envelope
5. Sign: compute canonical bytes → SHA-256 hash → RSA-PSS signature

The ingestor is a producer. It runs on a schedule (cron) or on-demand.
Its output is a stream of signed `CDSEvent` objects.

```python
class BaseIngestor(ABC):
    async def fetch(self) -> list[CDSEvent]: ...  # implement per domain
    async def ingest(self) -> list[CDSEvent]:
        return [self.signer.sign(e) for e in await self.fetch()]
```

---

## Layer 3 — Transport and store

CDS is transport-agnostic. Signed events are JSON blobs — they can be:

- **Stored in S3** (append-only, partitioned by `domain/date/event_id`)
- **Queued in SQS** (between ingestor and processor)
- **Routed via EventBridge** (by `domain` and `event_type`)
- **Served over HTTP** (API Gateway + Lambda)
- **Embedded in MCP responses** (tools return the event dict)

The signature is inside the event — it survives any transport. You can
copy the JSON to a database, a file, a message queue, or a response body
and the integrity guarantee is preserved.

---

## Layer 4 — Consumer

The consumer holds the **public key** only.

Before using any CDS event, a conformant consumer must call `CDSVerifier.verify()`.
This is a local operation — no network call, no trusted third party.

```python
verifier = CDSVerifier("keys/public.pem")
verifier.verify(event)  # raises ValueError or cryptography.exceptions.InvalidSignature
```

The public key can be distributed:
- In the SDK itself (for well-known issuers)
- Via `https://signed-data.org/.well-known/cds-public-key.pem`
- Out-of-band for private deployments

---

## Reference deployment (AWS)

The reference deployment at `signed-data.org` uses:

```
EventBridge Schedule (cron)
        │
Lambda (ingestor)          ← runs CDSSigner, reads key from Secrets Manager
        │ SQS
Lambda (processor)         ← enriches with Amazon Bedrock Nova Micro
        │ S3
Lambda (API handler)       ← GET /events?domain=lottery.brazil
        │ API Gateway v1
```

Source code: signed-data/cds infra (CDK TypeScript).
Personal operator deployment: [magj/cds-services](https://github.com/magj/cds-services).

---

## MCP layer (optional)

An MCP server is a CDS **consumer** with a FastMCP interface on top.
It verifies events, wraps them in tool responses, and exposes them
to Claude or any other MCP-compatible LLM client.

```
Claude Desktop
      │ MCP (stdio / SSE)
FastMCP server
      │ CDSVerifier.verify()
      │ CDSEvent JSON (from S3 or direct Caixa API fetch)
      └── returns dict to Claude
```

The MCP server does not hold the private key. It only verifies.

---

## Trust model

```
Issuer (signed-data.org)       holds private key
       │ signs every event
Consumer (any app, Claude)     holds public key
       └── verifies every event
```

The issuer says: *"I fetched this data from that source, at this time.
The payload has not changed since I signed it."*

The consumer does not need to trust the transport, the database, the queue,
or any intermediary. The signature is the only trust anchor.

This is the same model as code signing, X.509 certificates, and GPG.
The innovation is applying it to real-time curated data feeds.
