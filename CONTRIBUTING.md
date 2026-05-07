# Contributing to SignedData CDS

## Branching model

```
main        — stable, protected, auto-deploys to production
develop     — integration branch
feat/*      — new features
fix/*       — bug fixes
chore/*     — maintenance (deps, CI, tooling)
```

## Development setup

```bash
git clone git@github.com:signed-data/cds.git && cd cds

# Python SDK
cd sdk/python
pip install -e ".[dev]"
pytest                 # run all tests
ruff check .           # lint
mypy cds               # type check

# TypeScript SDK
cd sdk/typescript
npm install
npm run typecheck
npm test

# Infra
cd infra && npm install && npx cdk synth
```

## Releasing

```bash
# Python SDK  →  triggers release-python.yml  →  PyPI
git tag sdk-py-v0.2.0 && git push origin sdk-py-v0.2.0

# TypeScript SDK  →  triggers release-typescript.yml  →  npm
git tag sdk-ts-v0.2.0 && git push origin sdk-ts-v0.2.0

# Site     — auto on push to main when site/** changes
# Infra    — auto on push to main when infra/** changes
```

## Required GitHub Secrets

| Secret | Description |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | IAM OIDC role — run `infra/scripts/oidc-role.sh` |
| `NPM_TOKEN` | npmjs.com Automation token |
| `CODECOV_TOKEN` | codecov.io (optional) |

Secrets `SITE_BUCKET` and `CF_DISTRIBUTION_ID` are read from CDK stack outputs after first deploy — see `infra/scripts/post-deploy.sh`.

## Commit style

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `chore:`, `docs:`, `test:`
