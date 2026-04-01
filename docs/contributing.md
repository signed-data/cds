# Contributing

Contributions are welcome — bug fixes, new domains, SDK improvements,
and documentation. This file covers the practical details.

---

## What kind of contributions are in scope

**In scope:**
- Bug fixes in the SDK (Python or TypeScript)
- New domain specs and ingestors
- Performance improvements
- Documentation corrections
- Additional tests
- New MCP servers (open a PR against `signed-data/mcp-{domain}`)

**Out of scope for this repo:**
- Infrastructure changes (goes to [magj/cds-services](https://github.com/magj/cds-services) or your own fork)
- MCP server code (goes to `signed-data/mcp-{domain}`)
- Breaking changes to the envelope format (requires a spec proposal)

---

## Development setup

```bash
git clone git@github.com:signed-data/cds.git && cd cds

# Python
cd sdk/python
pip install -e ".[dev]"
pytest                  # must pass
ruff check cds/
mypy cds/

# TypeScript
cd sdk/typescript
npm install
npm run typecheck
npm test
```

All PRs must pass CI before review.

---

## Proposing a new domain

New domains require a spec before implementation.

1. Open an issue tagged `domain-proposal`
2. Include:
   - Data source name and URL
   - Authentication requirements (CDS prefers public/free APIs)
   - Sample raw API response (JSON)
   - Draft payload schema
   - Proposed content types (domain name + schema names)
   - Draw/update frequency

3. Once the domain spec is approved (maintainer comment), open a PR with:
   - `sdk/python/cds/sources/{domain}_models.py` — Pydantic models
   - `sdk/python/cds/sources/{domain}.py` — ingestor
   - `sdk/typescript/src/sources/{domain}.ts` — TypeScript equivalent
   - Tests in `sdk/python/tests/test_sdk.py`
   - Update `spec/CDS-v0.1.0.md` — add to registered domains table
   - Update `sdk/python/cds/__init__.py` — export new types
   - Update `sdk/typescript/src/index.ts` — export new types

**Domain naming rules:**
- Lowercase, dots for hierarchy: `sports.basketball`, `finance.crypto`
- Schema names: lowercase, dots for sub-type: `match.result`, `quote.spot`
- No abbreviations: `sports.football` not `sports.fb`

---

## Commit style

[Conventional Commits](https://www.conventionalcommits.org):

```
feat(lottery): add Dupla Sena ingestor
fix(signer):   handle PEM strings with trailing newline
docs(arch):    clarify trust model section
test(football):add standings payload roundtrip test
chore(deps):   bump cryptography to 43.0
```

---

## PR checklist

- [ ] All tests pass (`pytest`, `npm test`)
- [ ] No new linting errors (`ruff check`, `tsc --noEmit`)
- [ ] New ingestors have at least one test with mock data
- [ ] New domain specs follow the domain spec format described in `spec/CDS-v0.1.0.md`
- [ ] `CHANGELOG` entry in the relevant section of `README.md`

---

## Releasing

Maintainers only. Tags trigger CI/CD:

```bash
# Python SDK
git tag sdk-py-v0.2.0 && git push origin sdk-py-v0.2.0
# → release-python.yml → PyPI

# TypeScript SDK
git tag sdk-ts-v0.2.0 && git push origin sdk-ts-v0.2.0
# → release-typescript.yml → npm
```

---

## Code of conduct

Be direct and technically precise. Respect other contributors' time.
No personal attacks. Disagreements about technical decisions are fine;
disagreements about people are not.
