# Self-hosting

You do not need to use `signed-data.org` as your data provider.
CDS is a standard — the SDK, the spec, and the domain schemas are
infrastructure-free. Run your own ingestors, sign with your own key,
and serve your own events.

---

## What you need

| Component | Minimum viable | Production |
|---|---|---|
| Private key | Local PEM file | AWS Secrets Manager / KMS |
| Ingestor | Python script | Lambda / container (cron) |
| Event store | Local files | S3 (append-only, versioned) |
| Consumer API | Read from disk | API Gateway + Lambda |
| MCP server | `signeddata-mcp-lottery` | Lambda Function URL |

---

## Minimum viable setup (local)

```bash
pip install signeddata-cds

# Generate keys
python3 -c "
from cds import generate_keypair
import os; os.makedirs('keys', exist_ok=True)
generate_keypair('keys/private.pem', 'keys/public.pem')
"

# Run ingestor (football example)
python3 - << 'EOF'
import asyncio
from cds import CDSSigner
from cds.sources.football import FootballIngestor, LEAGUE_IDS

signer   = CDSSigner("keys/private.pem", issuer="localhost")
ingestor = FootballIngestor(
    signer=signer,
    api_key="YOUR_API_KEY",
    league_ids=[LEAGUE_IDS["brasileirao_a"]],
    season=2026,
)
events = asyncio.run(ingestor.ingest())

for e in events:
    print(e.context.summary)
    print(f"  signed_by: {e.integrity.signed_by}")
    print(f"  hash:      {e.integrity.hash[:32]}...")
EOF
```

---

## AWS deployment (CDK)

A complete reference deployment is available at
[magj/cds-services](https://github.com/magj/cds-services).

It deploys three CDK stacks to your AWS account:

```
SignedDataSiteStack   — CloudFront + S3 + Route53 for your domain
LotteryStack         — Lambda Function URLs for MCP servers (5 games)
IngestorStack        — Scheduled Lambdas → sign → S3 event store
```

**Deploy:**
```bash
git clone git@github.com:magj/cds-services.git && cd cds-services
chmod +x bootstrap.sh && ./bootstrap.sh
```

The bootstrap script creates the GitHub repo, sets up OIDC (no long-lived
AWS keys), generates a signing keypair, deploys CDK, and sets GitHub secrets
automatically.

**Estimated cost:** ~$2/month on AWS (primarily Amazon Bedrock for LLM enrichment).

---

## Docker (MCP server)

```bash
docker run -p 8001:8001 \
  -e CDS_PRIVATE_KEY_PATH=/keys/private.pem \
  -e CDS_ISSUER=myorg.example.com \
  -v ./keys:/keys:ro \
  signeddata/mcp-lottery mega-sena --transport sse --port 8001
```

Or all games at once:
```bash
docker compose up   # uses docker-compose.yml from mcp-lottery
```

---

## Issuer identity

Set your `issuer` to any string that identifies your organisation.
A domain name is conventional:

```python
signer = CDSSigner("keys/private.pem", issuer="mycompany.example.com")
```

**Publish your public key at:**
```
https://mycompany.example.com/.well-known/cds-public-key.pem
```

Consumers can then discover and verify your key automatically.

---

## What stays the same

When self-hosting, the envelope format, content types, signing algorithm,
and domain specs are identical to `signed-data.org`.

Your events are verifiable by any CDS consumer — they just use your public
key instead of ours.

---

## What changes

| Property | signed-data.org | Your deployment |
|---|---|---|
| `integrity.signed_by` | `"signed-data.org"` | `"mycompany.example.com"` |
| Public key URL | `signed-data.org/.well-known/...` | `mycompany.example.com/.well-known/...` |
| Infrastructure | Our AWS account | Your AWS / GCP / Azure account |
| Ingestor schedule | Our crons | Your crons |

---

## Consuming events from multiple issuers

A consumer can hold multiple public keys and verify against the declared issuer:

```python
KNOWN_ISSUERS = {
    "signed-data.org":       CDSVerifier("signed-data-org.pub.pem"),
    "mycompany.example.com": CDSVerifier("mycompany.pub.pem"),
}

verifier = KNOWN_ISSUERS.get(event.integrity.signed_by)
if not verifier:
    raise ValueError(f"Unknown issuer: {event.integrity.signed_by}")

verifier.verify(event)
```
