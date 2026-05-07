# CDS — Product Narrative v2

_Approved positioning document for Wdotnet MCP server product line._

---

## The problem

Real-time data feeds have a provenance gap. When a JSON payload arrives at your AI agent, you trust the transport, the intermediaries, and the source simultaneously. There is no cryptographic proof the data is authentic, unmodified, or from who it claims to be from.

LLMs compound this: they need data that is both machine-readable *and* verifiably sourced. A hallucination and a tampered data feed look identical to the model — both arrive as text.

---

## What SignedData is

**SignedData** is an open standard for cryptographically signed, real-time data feeds. Every event is a W3C Verifiable Credential: a machine-readable fact with a cryptographic proof, an issuer URI, and a human-readable summary embedded alongside the payload.

The standard has three components:

- **CDS (Curated Data Standard)** — a JSON-LD envelope that wraps any real-time event in a signed, linked-data structure. URI-based identities, dereferenceable everywhere.
- **SDKs** in Python and TypeScript — libraries that produce, sign, and verify CDS events with ECDSA P-256 (v0.6.0+) or RSA-4096 PSS (legacy).
- **Vocab registry** — a growing set of content-type URIs and source identifiers covering 15+ domains of Brazilian data.

The standard is MIT licensed. The SDKs are public. Anyone can run ingestors and operators.

---

## What Wdotnet builds

**Wdotnet** is a software company based in Jundiaí, São Paulo, Brazil. SignedData was started by Wdotnet to solve a real problem in the Brazilian data intelligence market: AI agents that need verifiable, real-time data from authoritative sources.

Today, Wdotnet produces signed feeds for:

| Domain | Source | Endpoint |
| ------ | ------ | -------- |
| Finance | BCB (SELIC, IPCA, FX), B3 (quotes, Copom) | `finance.mcp.signed-data.org` |
| Commodities | B3 futures, CONAB spot, basis spreads | `commodities.mcp.signed-data.org` |
| Companies | CNPJ profiles, partners (BrasilAPI) | `companies.mcp.signed-data.org` |
| Gov-BR | Portal da Transparência — sanctions, licitações | `gov-br.mcp.signed-data.org` |
| Lottery | Mega Sena, Lotofácil, Quina, Timemania | `lottery.mcp.signed-data.org` |
| IBGE | Municipal demographics, PIB, Census 2022 | `ibge.mcp.signed-data.org` |
| B3 Fundamentus | Equity indicators — P/L, EV/EBITDA, dividends | `b3.mcp.signed-data.org` |
| Currency | 150+ currencies vs BRL (BCB PTAX + AwesomeAPI) | `currency.mcp.signed-data.org` |
| Processo | Judicial processes via DataJud/CNJ | `processo.mcp.signed-data.org` |
| Notícias | Brazilian news headlines (GDELT) | `noticias.mcp.signed-data.org` |
| CEP | Postal address lookup (ViaCEP) | `cep.mcp.signed-data.org` |
| ANVISA | Drug, cosmetic, and food registrations | `anvisa.mcp.signed-data.org` |
| Bible | Verses and passages — Almeida (pt), KJV, WEB | `bible.mcp.signed-data.org` |
| Energia | ANEEL electricity tariffs by distributor | `energia.mcp.signed-data.org` |
| Weather | Current conditions and forecasts (Open-Meteo) | `weather.mcp.signed-data.org` |
| Sports | Football matches, standings, live scores | `sports.mcp.signed-data.org` |
| CAGED | Formal employment balance (MTE/BrasilAPI) | `caged.mcp.signed-data.org` |
| BCB Focus | Market consensus macroeconomic forecasts | `focus.mcp.signed-data.org` |

Each server is operated with uptime SLAs, API key authentication, and WAF protection.

---

## Built in Brazil

Wdotnet is a software company based in Jundiaí, São Paulo. The Brazilian data stack is our home turf: BCB, IBGE, BrasilAPI, DataJud, Portal da Transparência, ANVISA — we know the sources, the quirks, the release schedules.

Our MCP servers don't scrape HTML or cache stale CSVs. Every tool call hits the authoritative source, wraps the result in a W3C Verifiable Credential signed with our ECDSA P-256 key, and returns it with provenance embedded.

---

## Who this is for

**AI developers** building agents that need real-time Brazilian data: finance apps, legal due diligence pipelines, HR analytics, regulatory compliance tools, news monitoring.

**Enterprise teams** that need verifiable data provenance for audit trails, compliance, or multi-agent pipelines where tamper-evidence matters.

**Researchers** working on the Brazilian economy, labor markets, judiciary, or public health who want machine-readable, citable data with cryptographic provenance.

---

## How it works

1. Your AI agent calls a tool via the MCP protocol (HTTP Streamable Transport).
2. The server fetches from the authoritative source (BCB, IBGE, BrasilAPI, etc.).
3. The result is wrapped in a CDS event — a W3C Verifiable Credential with `DataIntegrityProof`.
4. The signed credential is returned. Your agent gets both the data and cryptographic proof it came from Wdotnet.
5. Verification: any consumer can independently verify the credential using the CDS SDK or any W3C VC library.

---

## Principles

- **Provenance, not only TLS.** HTTPS secures the channel; W3C VC signatures anchor the payload to the issuer.
- **Standard is the contract.** The CDS standard and SDKs are infrastructure-agnostic. Wdotnet operates the servers; anyone can run ingestors.
- **Linked Data.** URI-based identities, JSON-LD envelopes, dereferenceable everything.
- **LLM-ready.** Every event carries a `context.summary` so data and meaning travel together.
- **Open.** MIT licensed. The standard, SDKs, and MCP server source are all public.

---

## Contact

Wdotnet operates the signed-data.org MCP server fleet.

→ **[wdotnet.com.br](https://wdotnet.com.br)**  
→ **[mcp@wdotnet.com.br](mailto:mcp@wdotnet.com.br)**

API key access, SLA agreements, and custom data integrations: contact us directly.
