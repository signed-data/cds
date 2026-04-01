# Curated Data Standard (CDS)

[![CI](https://github.com/signed-data/cds/actions/workflows/ci.yml/badge.svg)](https://github.com/signed-data/cds/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/signeddata-cds)](https://pypi.org/project/signeddata-cds/)
[![npm](https://img.shields.io/npm/v/@signeddata/cds-sdk)](https://www.npmjs.com/package/@signeddata/cds-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open standard for distributing **curated, cryptographically signed, real-time data** with embedded LLM context.

→ [signed-data.org](https://signed-data.org) · [Spec v0.1.0](spec/CDS-v0.1.0.md) · [Changelog](#changelog)

---

## The problem

Real-time data feeds have a provenance gap. You get a JSON payload and you have to trust the transport, the intermediary, and the source simultaneously. There is no cryptographic proof the data is authentic, unmodified, or from who it claims to be from.

At the same time, LLMs need data that is both machine-readable and human-understandable. Most feeds give you one or the other.

## The solution

CDS wraps any real-time data source in a universal signed envelope:

```json
{
  "spec_version": "0.1.0",
  "id": "a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d",
  "content_type": {
    "domain":      "sports.football",
    "schema_name": "match.result",
    "version":     "1"
  },
  "source": {
    "id":          "api-football.com.v3",
    "fingerprint": "sha256:b310739720e5f948..."
  },
  "occurred_at": "2026-03-22T21:00:00Z",
  "lang":        "pt-BR",
  "payload": {
    "home": { "name": "Flamengo",   "score": 2 },
    "away": { "name": "Fluminense", "score": 1 },
    "status": "finished",
    "competition": "Brasileirão Série A"
  },
  "context": {
    "summary":      "Flamengo beat Fluminense 2–1 at Maracanã. Brasileirão round 5.",
    "model":        "amazon.nova-micro-v1:0",
    "generated_at": "2026-03-22T21:00:05Z"
  },
  "integrity": {
    "hash":      "sha256:a1b2c3d4e5f6...",
    "signature": "MX6rj3qKQkpDIUbc1NXd...",
    "signed_by": "signed-data.org"
  }
}
```

Any consumer with the issuer's public key can verify the signature independently. Any LLM can read the `context.summary` without parsing the payload.

---

## Quick start

### Python

```bash
pip install signeddata-cds
```

```python
from cds import CDSSigner, CDSVerifier
from cds.sources.football import FootballIngestor, LEAGUE_IDS
import asyncio

# Producer — fetch and sign
signer   = CDSSigner("./keys/private.pem", issuer="your-org.example.com")
ingestor = FootballIngestor(
    signer=signer,
    api_key=os.environ["API_FOOTBALL_KEY"],
    league_ids=[LEAGUE_IDS["brasileirao_a"]],
    season=2026,
)
events = asyncio.run(ingestor.ingest())  # signed ✓

# Consumer — verify before use
verifier = CDSVerifier("./keys/public.pem")
for event in events:
    verifier.verify(event)              # raises if tampered
    print(event.context.summary)
```

### TypeScript

```bash
npm install @signeddata/cds-sdk
```

```typescript
import { FootballIngestor, CDSSigner, CDSVerifier, LEAGUE_IDS } from "@signeddata/cds-sdk";

const signer   = new CDSSigner("./keys/private.pem", "your-org.example.com");
const ingestor = new FootballIngestor(signer, {
  apiKey:    process.env.API_FOOTBALL_KEY!,
  leagueIds: [LEAGUE_IDS.brasileirao_a],
  season:    2026,
});

const events = await ingestor.ingest();   // signed ✓

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
│   ├── CDS-v0.1.0.md          # Formal specification
│   └── domains/               # Per-domain payload schemas
│       ├── lottery.brazil.md
│       └── ...
├── sdk/
│   ├── python/                # Python SDK  →  pip install signeddata-cds
│   │   ├── cds/
│   │   │   ├── schema.py      # CDSEvent, CDSContentType (core types)
│   │   │   ├── signer.py      # CDSSigner, CDSVerifier
│   │   │   ├── ingestor.py    # BaseIngestor
│   │   │   └── sources/       # Domain ingestors + models
│   │   │       ├── football_models.py
│   │   │       ├── football.py
│   │   │       ├── lottery_models.py
│   │   │       ├── lottery.py
│   │   │       └── weather.py
│   │   └── tests/
│   └── typescript/            # TypeScript SDK  →  npm install @signeddata/cds-sdk
│       └── src/
│           ├── schema.ts
│           ├── signer.ts
│           ├── ingestor.ts
│           └── sources/
│               ├── football.ts
│               └── lottery.ts
└── site/                      # signed-data.org static site
    └── index.html
```

---

## How signing works

Signing is deterministic RSA-PSS SHA-256 over a canonical JSON serialisation of the event.

**Sign (producer):**
1. Serialise the event to canonical JSON — `sort_keys=True`, UTF-8, excluding `integrity` and `ingested_at`
2. Compute `hash = "sha256:" + SHA256(canonical_bytes).hexdigest()`
3. Sign `canonical_bytes` with your RSA-4096 private key (PSS, MGF1, max salt)
4. Attach `integrity = { hash, signature, signed_by }`

**Verify (consumer):**
1. Re-serialise the event using the same canonical rules
2. Assert `hash == SHA256(canonical_bytes)`
3. Verify the RSA-PSS signature with the issuer's public key

Any modification to any field — including `context.summary`, `payload`, or `source.fingerprint` — invalidates the signature.

Full details: [spec/CDS-v0.1.0.md — Section 4](spec/CDS-v0.1.0.md)

---

## Content types

CDS uses MIME vendor extensions for semantic typing:

```
application/vnd.cds.{domain}.{schema}+{encoding};v={version}
```

The type encodes **what the data is**, not just how it is formatted. A consumer can route, validate, and deserialise purely from the content type — no runtime inspection of the payload needed.

Examples:

```
application/vnd.cds.sports-football.match-result+json;v=1
application/vnd.cds.lottery-brazil.mega-sena-result+json;v=1
application/vnd.cds.weather.forecast-current+json;v=1
```

---

## Registered domains

| Domain | Schema names | Source | Spec |
|---|---|---|---|
| `weather` | `forecast.current`, `forecast.daily`, `alert.severe` | Open-Meteo | [domains/weather.md](spec/domains/weather.md) |
| `sports.football` | `match.result`, `match.live`, `standings.update` | api-football.com | [domains/sports.football.md](spec/domains/sports.football.md) |
| `news` | `headline`, `breaking`, `summary` | various RSS/APIs | [domains/news.md](spec/domains/news.md) |
| `finance` | `quote.stock`, `quote.crypto`, `quote.forex` | various | [domains/finance.md](spec/domains/finance.md) |
| `religion.bible` | `verse`, `passage`, `daily` | public domain | [domains/religion.bible.md](spec/domains/religion.bible.md) |
| `government.brazil` | `diario.oficial`, `licitacao`, `lei` | official APIs | [domains/government.brazil.md](spec/domains/government.brazil.md) |
| `lottery.brazil` | `mega-sena.result`, `lotofacil.result`, `quina.result`, `lotomania.result`, `dupla-sena.result` | Caixa oficial | [domains/lottery.brazil.md](spec/domains/lottery.brazil.md) |

---

## MCP servers

CDS events are designed to be consumed by LLMs via the [Model Context Protocol](https://modelcontextprotocol.io).

| Server | Games / domains | Install |
|---|---|---|
| [mcp-lottery](https://github.com/signed-data/mcp-lottery) | Mega Sena, Lotofácil, Quina, Lotomania, Dupla Sena | `pip install signeddata-mcp-lottery` |

---

## Development

```bash
git clone git@github.com:signed-data/cds.git && cd cds

# Python SDK
cd sdk/python && pip install -e ".[dev]"
pytest                  # 19 tests
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

You do not need to use `signed-data.org` as your issuer. Run your own ingestors against this SDK, sign with your own keypair, and set `issuer` to your organisation's identifier.

```python
signer = CDSSigner("./keys/private.pem", issuer="mycompany.example.com")
```

Consumers verify with your public key. The trust anchor is your organisation, not ours.

For a complete self-hosting example with AWS CDK (Lambda + S3 + EventBridge), see the [magj/cds-services](https://github.com/magj/cds-services) reference deployment.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

To propose a new domain or schema, open an issue with the tag `domain-proposal`. Include: the data source, sample API response, and a draft payload schema.

---

## Changelog

### v0.1.0 — 2026-03 (current)

- Initial release
- Core envelope: `CDSEvent`, `CDSContentType`, `IntegrityMeta`
- RSA-PSS SHA-256 signing and verification
- Python SDK (`signeddata-cds`) and TypeScript SDK (`@signeddata/cds-sdk`)
- Domains: `weather`, `sports.football`, `news`, `finance`, `religion.bible`, `government.brazil`, `lottery.brazil`
- MCP server: `mcp-lottery` (Mega Sena, Lotofácil, Quina, Lotomania, Dupla Sena)

---

## License

MIT — see [LICENSE](LICENSE)
