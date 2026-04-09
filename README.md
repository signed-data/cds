<div align="center">

# Curated Data Standard (CDS)

**An open standard for distributing curated, cryptographically signed, real-time data as 5-star Linked Data with embedded LLM context.**

[![CI](https://github.com/signed-data/cds/actions/workflows/ci.yml/badge.svg)](https://github.com/signed-data/cds/actions/workflows/ci.yml)
[![Spec](https://img.shields.io/badge/spec-v0.2.0-blue?logo=w3c)](spec/CDS-v0.2.0.md)
[![Linked Data](https://img.shields.io/badge/Linked_Data-%E2%98%85%E2%98%85%E2%98%85%E2%98%85%E2%98%85-brightgreen?logo=semanticweb)](https://www.w3.org/DesignIssues/LinkedData.html)
[![JSON-LD](https://img.shields.io/badge/JSON--LD-valid-blue?logo=json)](https://json-ld.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?logo=opensourceinitiative)](LICENSE)

[![PyPI](https://img.shields.io/pypi/v/signeddata-cds?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/signeddata-cds/)
[![npm](https://img.shields.io/npm/v/@signeddata/cds-sdk?logo=npm&logoColor=white&label=npm)](https://www.npmjs.com/package/@signeddata/cds-sdk)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/typescript-5+-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)

[![Signing](https://img.shields.io/badge/signing-RSA--PSS_SHA--256-critical?logo=letsencrypt&logoColor=white)](docs/signing.md)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2?logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)

[Website](https://signed-data.org) ·
[Spec v0.2.0](spec/CDS-v0.2.0.md) ·
[Linked Data](docs/linked-data.md) ·
[Getting Started](docs/getting-started.md) ·
[Changelog](#changelog)

</div>

---

## The problem

Real-time data feeds have a provenance gap. You get a JSON payload and you have to trust the transport, the intermediary, and the source simultaneously. There is no cryptographic proof the data is authentic, unmodified, or from who it claims to be from.

At the same time, identities in data feeds are opaque strings — you cannot look them up to learn what they mean. LLMs need data that is both machine-readable and human-understandable. Most feeds give you one or the other.

## The solution

CDS wraps any real-time data source in a universal signed **JSON-LD** envelope. Every identity is a dereferenceable HTTP URI:

```json
{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@type":    "https://signed-data.org/vocab/CuratedDataEvent",
  "@id":      "https://signed-data.org/events/a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d",

  "spec_version": "0.2.0",
  "id":           "a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d",

  "content_type": "https://signed-data.org/vocab/sports-football/match-result",

  "source": {
    "@id":         "https://signed-data.org/sources/api-football.com.v3",
    "fingerprint": "sha256:b310739720e5f948..."
  },

  "occurred_at": "2026-03-22T21:00:00Z",
  "lang":        "pt-BR",

  "payload": {
    "home": { "name": "Flamengo",   "score": 2 },
    "away": { "name": "Fluminense", "score": 1 },
    "status": "finished",
    "competition": "Brasileirao Serie A"
  },

  "context": {
    "summary":      "Flamengo beat Fluminense 2-1 at Maracana. Brasileirao round 5.",
    "model":        "amazon.nova-micro-v1:0",
    "generated_at": "2026-03-22T21:00:05Z"
  },

  "integrity": {
    "hash":      "sha256:a1b2c3d4e5f6...",
    "signature": "MX6rj3qKQkpDIUbc1NXd...",
    "signed_by": "https://signed-data.org"
  }
}
```

Any consumer with the issuer's public key can verify the signature independently. Any LLM can read the `context.summary` without parsing the payload. Every URI is dereferenceable — follow the links to discover what the data is and where it came from.

### 5-star Linked Data

CDS v0.2.0 achieves the highest level of Tim Berners-Lee's open data rating:

| Stars | Criteria | CDS |
|---|---|---|
| ★ | Available online, open license | MIT |
| ★★ | Structured machine-readable data | JSON |
| ★★★ | Non-proprietary format | JSON (not Excel) |
| ★★★★ | Use open W3C standards | JSON-LD |
| ★★★★★ | Link to other data | URI-based identities |

---

## Quick start

### Python

```bash
pip install signeddata-cds
```

```python
from cds import CDSSigner, CDSVerifier, CDSVocab, CDSSources, SourceMeta
from cds.sources.football import FootballIngestor, LEAGUE_IDS
import asyncio, os

# Producer — fetch and sign
signer   = CDSSigner("./keys/private.pem", issuer="https://your-org.example.com")
ingestor = FootballIngestor(
    signer=signer,
    api_key=os.environ["API_FOOTBALL_KEY"],
    league_ids=[LEAGUE_IDS["brasileirao_a"]],
    season=2026,
)
events = asyncio.run(ingestor.ingest())  # signed JSON-LD

# Consumer — verify before use
verifier = CDSVerifier("./keys/public.pem")
for event in events:
    verifier.verify(event)              # raises if tampered
    print(event.event_context.summary)
```

### TypeScript

```bash
npm install @signeddata/cds-sdk
```

```typescript
import { FootballIngestor, CDSSigner, CDSVerifier, LEAGUE_IDS } from "@signeddata/cds-sdk";

const signer   = new CDSSigner("./keys/private.pem", "https://your-org.example.com");
const ingestor = new FootballIngestor(signer, {
  apiKey:    process.env.API_FOOTBALL_KEY!,
  leagueIds: [LEAGUE_IDS.brasileirao_a],
  season:    2026,
});

const events = await ingestor.ingest();   // signed JSON-LD

const verifier = new CDSVerifier("./keys/public.pem");
for (const event of events) {
  verifier.verify(event);                 // throws if tampered
  console.log(event.context?.summary);
}
```

### Generate a keypair

```python
from cds import generate_keypair
import os; os.makedirs("keys", exist_ok=True)
generate_keypair("keys/private.pem", "keys/public.pem")
```

---

## Repository structure

```
cds/
├── spec/
│   ├── CDS-v0.1.0.md              # v0.1.0 specification
│   ├── CDS-v0.2.0.md              # v0.2.0 specification (Linked Data)
│   ├── MIGRATION-v0.1-to-v0.2.md  # Migration guide
│   └── domains/
│       ├── finance.brazil.md
│       ├── commodities.brazil.md
│       └── lottery.brazil.md
├── vocab/                          # Linked Data vocabulary (JSON-LD)
│   ├── cds.jsonld                  # Core ontology
│   ├── domains/                    # Domain definitions
│   └── sources/                    # Source registry
├── contexts/
│   └── cds/v1.jsonld               # JSON-LD context document
├── sdk/
│   ├── python/                     # Python SDK  →  pip install signeddata-cds
│   │   ├── cds/
│   │   │   ├── schema.py           # CDSEvent (JSON-LD envelope)
│   │   │   ├── vocab.py            # CDSVocab, CDSSources (URI constants)
│   │   │   ├── signer.py           # CDSSigner, CDSVerifier
│   │   │   ├── ingestor.py         # BaseIngestor
│   │   │   └── sources/            # Domain ingestors + models
│   │   └── tests/
│   └── typescript/                 # TypeScript SDK  →  npm install @signeddata/cds-sdk
│       └── src/
│           ├── schema.ts
│           ├── vocab.ts
│           ├── signer.ts
│           ├── ingestor.ts
│           └── sources/
├── mcp/
│   ├── finance/                    # signeddata-mcp-finance
│   ├── commodities/                # signeddata-mcp-commodities
│   └── lottery/                    # signeddata-mcp-lottery
└── docs/
    ├── getting-started.md
    ├── architecture.md
    ├── linked-data.md              # Why Linked Data, how CDS implements it
    ├── signing.md
    ├── content-types.md
    └── self-hosting.md
```

---

## How signing works

CDS signing uses RSA-PSS SHA-256 over a canonical JSON serialisation of the event.
The canonical bytes — and therefore the hash — are deterministic; RSA-PSS signatures
use a random salt per the standard.

**Sign (producer):**
1. Serialise the event to canonical JSON — `sort_keys=True`, UTF-8, excluding `integrity` and `ingested_at`; including `@context`, `@type`, `@id`
2. Compute `hash = "sha256:" + SHA256(canonical_bytes).hexdigest()`
3. Sign `canonical_bytes` with your RSA-4096 private key (PSS, MGF1, max salt)
4. Attach `integrity = { hash, signature, signed_by }`

**Verify (consumer):**
1. Re-serialise the event using the same canonical rules
2. Assert `hash == SHA256(canonical_bytes)`
3. Verify the RSA-PSS signature with the issuer's public key

Any modification to any field — including `context.summary`, `payload`, or `source.fingerprint` — invalidates the signature.

Full details: [spec/CDS-v0.2.0.md](spec/CDS-v0.2.0.md)

---

## Content types

CDS v0.2.0 uses URI-based content types:

```
https://signed-data.org/vocab/{domain-slug}/{schema-slug}
```

Every URI is dereferenceable — follow it to learn what the data schema is, what domain it belongs to, and which source produces it.

Examples:

```
https://signed-data.org/vocab/sports-football/match-result
https://signed-data.org/vocab/lottery-brazil/mega-sena-result
https://signed-data.org/vocab/weather/forecast-current
```

---

## Registered domains

| Domain | Schema names | Source | Vocab |
|---|---|---|---|
| `weather` | `forecast.current`, `forecast.daily`, `alert.severe` | Open-Meteo | [weather.jsonld](vocab/domains/weather.jsonld) |
| `sports.football` | `match.result`, `match.live`, `standings.update` | api-football.com | [sports-football.jsonld](vocab/domains/sports-football.jsonld) |
| `news` | `headline`, `breaking`, `summary` | various | [news.jsonld](vocab/domains/news.jsonld) |
| `finance` | `quote.stock`, `quote.crypto`, `quote.forex`, `index.update` | Brapi | [finance.jsonld](vocab/domains/finance.jsonld) |
| `finance.brazil` | `rate.selic`, `index.ipca`, `fx.usd-brl`, `decision.copom`, `quote.stock` | Banco Central + Brapi | [finance-brazil.jsonld](vocab/domains/finance-brazil.jsonld) |
| `commodities.brazil` | `futures.soja`, `spot.soja`, `spot.milho`, `index.worldbank` | Brapi + CONAB + World Bank | [commodities-brazil.jsonld](vocab/domains/commodities-brazil.jsonld) |
| `religion.bible` | `verse`, `passage`, `daily` | bible-api.com | [religion-bible.jsonld](vocab/domains/religion-bible.jsonld) |
| `government.brazil` | `diario.oficial`, `licitacao`, `lei` | official APIs | [government-brazil.jsonld](vocab/domains/government-brazil.jsonld) |
| `lottery.brazil` | `mega-sena.result`, `lotofacil.result`, `quina.result`, `lotomania.result`, `dupla-sena.result` | Caixa | [lottery-brazil.jsonld](vocab/domains/lottery-brazil.jsonld) |

---

## MCP servers

CDS events are designed to be consumed by LLMs via the [Model Context Protocol](https://modelcontextprotocol.io).

| Server | Games / domains | Install |
|---|---|---|
| [`mcp/finance`](mcp/finance) | SELIC, IPCA, PTAX FX, B3 quotes, Copom | `pip install signeddata-mcp-finance` |
| [`mcp/commodities`](mcp/commodities) | B3 agro futures, CONAB spot prices, basis spreads | `pip install signeddata-mcp-commodities` |
| [mcp-lottery](https://github.com/signed-data/mcp-lottery) | Mega Sena, Lotofacil, Quina, Lotomania, Dupla Sena | `pip install signeddata-mcp-lottery` |

---

## Development

```bash
git clone git@github.com:signed-data/cds.git && cd cds

# Python SDK
cd sdk/python && pip install -e ".[dev]"
pytest
ruff check cds/
mypy cds/

# TypeScript SDK
cd sdk/typescript && npm install
npm run typecheck
npm test
```

CI runs on every push and pull request. See [.github/workflows/ci.yml](.github/workflows/ci.yml).

---

## Self-hosting

You do not need to use `signed-data.org` as your issuer. Run your own ingestors against this SDK, sign with your own keypair, and set `issuer` to your organisation's URI.

```python
signer = CDSSigner("./keys/private.pem", issuer="https://mycompany.example.com")
```

Consumers verify with your public key. The trust anchor is your organisation, not ours. Publish your vocabulary and public key at your domain for full Linked Data compliance.

For a complete self-hosting example with AWS CDK (Lambda + S3 + EventBridge), see the [magj/cds-services](https://github.com/magj/cds-services) reference deployment.

---

## Contributing

See [CONTRIBUTING.md](docs/contributing.md).

To propose a new domain or schema, open an issue with the tag `domain-proposal`. Include: the data source, sample API response, and a draft payload schema.

---

## Changelog

### v0.2.0 — 2026-04 (current)

- **Linked Data rebuild** — every identity is now a dereferenceable HTTP URI
- Events are valid JSON-LD with `@context`, `@type`, `@id`
- `content_type` is a URI string (was `CDSContentType` object) — **breaking**
- `source.@id` replaces `source.id` — **breaking**
- `integrity.signed_by` is a full URI — **breaking**
- New `CDSVocab` and `CDSSources` URI constants in both SDKs
- Vocabulary, context, and source registry as JSON-LD files
- Domain specs and vocab for `finance.brazil` and `commodities.brazil`
- MCP packages for `signeddata-mcp-finance` and `signeddata-mcp-commodities`
- 5-star Linked Data rating achieved
- See [MIGRATION-v0.1-to-v0.2.md](spec/MIGRATION-v0.1-to-v0.2.md)

### v0.1.0 — 2026-03

- Initial release
- Core envelope: `CDSEvent`, `CDSContentType`, `IntegrityMeta`
- RSA-PSS SHA-256 signing and verification
- Python SDK (`signeddata-cds`) and TypeScript SDK (`@signeddata/cds-sdk`)
- Domains: `weather`, `sports.football`, `news`, `finance`, `religion.bible`, `government.brazil`, `lottery.brazil`
- MCP server: `mcp-lottery` (Mega Sena, Lotofacil, Quina, Lotomania, Dupla Sena)

---

## License

MIT — see [LICENSE](LICENSE)
