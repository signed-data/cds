# SignedData — Curated Data Standard (CDS)

> Open standard for distributing curated, cryptographically signed, real-time data with embedded LLM context.

**Website:** https://signed-data.org  
**Organisation:** SignedData.Org  
**License:** MIT

## Monorepo structure

```
signed-data/
├── sdk/
│   ├── python/          # Python 3.12+ SDK  →  pip install signeddata-cds
│   └── typescript/      # TypeScript 5 SDK  →  npm install @signeddata/cds-sdk
├── infra/               # AWS CDK — Lambda, SQS, S3, EventBridge, Bedrock, Route53, ACM
├── site/                # signed-data.org static site
└── spec/                # CDS specification (Markdown + JSON Schema)
```

## Quick start

```bash
# Python
pip install signeddata-cds

# TypeScript / Node
npm install @signeddata/cds-sdk
```

## Development

```bash
git clone git@github.com:signed-data/cds.git && cd cds

# Python SDK
cd sdk/python && pip install -e ".[dev]" && pytest

# TypeScript SDK
cd sdk/typescript && npm install && npm test

# Infra (requires AWS credentials)
cd infra && npm install && cdk synth
```

## License

MIT — see [LICENSE](LICENSE)
