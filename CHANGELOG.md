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
