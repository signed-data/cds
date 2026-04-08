## 0.4.0 - 2026-04-07

### Features
- Add `integrity.brazil` domain: federal sanction lookup (CEIS, CNEP, CEPIM) via Portal da Transparência API. Query-driven; signs the consolidated CEIS/CNEP/CEPIM result for a CNPJ as a single CDS event with cryptographic timestamp — auditable evidence for KYC/AML/due-diligence workflows.
- Add `mcp/integrity` MCP server (`signeddata-mcp-integrity`) exposing `check_sanctions_by_cnpj` as the Phase 1 primary tool. Pairs with `mcp/companies` to form a complete due-diligence primitive in two signed events.
- Add `cds/sources/integrity.py` Python module with `SanctionsFetcher`, parallel CEIS/CNEP/CEPIM fetching, and rule-based summary generation in `pt-BR`.
- Add `cds/sources/integrity_models.py` typed Pydantic models: `SanctionRecord`, `SanctionsConsolidated`, `IntegrityContentTypes`.
- Add 4 new content type URI constants: `INTEGRITY_SANCTIONS_CONSOLIDATED`, `INTEGRITY_SANCTIONS_CEIS`, `INTEGRITY_SANCTIONS_CNEP`, `INTEGRITY_SANCTIONS_CEPIM`.
- Add `CDSSources.PORTAL_TRANSPARENCIA` source URI constant.
- Register new JSON-LD source `api.portaldatransparencia.gov.br.v1` (api-key auth, LAI 12.527/2011 license).
- Register new JSON-LD domain `integrity-brazil.jsonld` with all four sanction content types.
- Add domain spec `spec/domains/integrity.brazil.md`.
- Add Python contract tests for the new module.

### Notes
- The `mcp/integrity` package is source-installed only (same convention as `mcp/finance`, `mcp/companies`, `mcp/commodities`); only `signeddata-cds` is published to PyPI by the release workflow.
- Portal da Transparência requires a free per-email `chave-api-dados` token. Rate limits: 90 req/min (06:00–23:59 BRT), 300 req/min (00:00–05:59 BRT).
- CEIS/CNEP/CEPIM records include public CPF/CNPJ of sanctioned parties as published by the Controladoria-Geral da União (CGU). The CDS signature attests to the source, not to appropriateness of redistribution.

## 0.3.1 - 2026-04-04

### Fixes
- Fix `mcp/commodities` packaging so the CLI installs and runs like the finance MCP package
- Add `mcp/commodities/README.md` with remote, local, and source install instructions

### Documentation
- Update CDS repo docs to list the finance and commodities MCP products explicitly
- Refresh architecture docs to describe the current operator deployment shape for finance and commodities

## 0.3.0 - 2026-04-04

### Features
- Add `finance.brazil` domain: BCB rates (SELIC, CDI), indices (IPCA, IGP-M), FX (USD/BRL, EUR/BRL), B3 stock/FII/crypto quotes, and Copom monetary policy decisions
- Add `companies.brazil` domain: CNPJ company profile and partner (QSA) lookup via BrasilAPI with full check-digit validation — query-driven, not scheduled
- Add `commodities.brazil` domain: B3 agro futures (soja, milho, boi gordo, café, açúcar, etanol), CONAB physical crop prices with defensive parsing, and World Bank commodity indices
- 3 new MCP servers (`mcp/finance`, `mcp/companies`, `mcp/commodities`) built with FastMCP
- Python and TypeScript SDK implementations for all 3 domains with typed models
- 67 new Python tests (106 total), 53 TypeScript tests — all passing
- 4 new JSON-LD source registries (BCB, BrasilAPI, CONAB, World Bank)
- 3 new JSON-LD domain vocabularies with full content type definitions

## 0.2.0 - 2026-03-29

### Features
- Linked Data v0.2.0: URI-based identities, JSON-LD context, `@context`/`@type`/`@id` fields
- Rebuilt Python and TypeScript SDKs for v0.2.0 spec
- Added vocabulary, context, source, and domain JSON-LD files

## 0.1.0 - 2026-03-15

### Features
- Initial CDS specification and SDK
- Lottery domain (Mega Sena) with Python and TypeScript ingestors
- RSA-PSS SHA-256 signing and verification
