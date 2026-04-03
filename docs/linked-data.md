# Linked Data

CDS v0.2.0 treats every event, source, and content type as a first-class
resource on the web. This document explains why, how, and what that buys you.

---

## 1. Why Linked Data

Tim Berners-Lee proposed four rules for publishing data on the web:

1. Use URIs as names for things.
2. Use HTTP URIs so that people can look those names up.
3. When someone looks up a URI, provide useful information (using standards).
4. Include links to other URIs so that they can discover more things.

**The Tower of Babel problem.** Different systems use different identifiers
for the same things. One lottery API calls the game `megasena`, another calls
it `mega-sena`, a third uses an opaque numeric ID. A weather API returns
`temp_c`, another returns `temperature_celsius`. The concepts are identical
but the names are not, so combining data from these systems requires
hand-written mapping code for every pair.

URIs solve this by providing a universal naming scheme. When two systems
refer to `https://signed-data.org/vocab/lottery-brazil/mega-sena-result`,
they mean the same thing -- no mapping required.

Without Linked Data, JSON payloads are isolated silos. Each consumer must
already know what every field means and where to get more information.
Linked Data connects those silos: every field that references an external
concept carries a dereferenceable URI that leads to a definition, and that
definition links onward to related resources.

---

## 2. How CDS implements each rule

### Rule 1 -- Use URIs as names for things

CDS assigns a stable URI to every entity in the system.

| Entity | URI pattern | Example |
|---|---|---|
| Event | `https://signed-data.org/events/{uuid}` | `https://signed-data.org/events/a3f1c9e0-7b2d-4e8a-9f01-abc123def456` |
| Source | `https://signed-data.org/sources/{source-id}` | `https://signed-data.org/sources/caixa.gov.br.loterias.v1` |
| Content type | `https://signed-data.org/vocab/{domain}/{type}` | `https://signed-data.org/vocab/lottery-brazil/mega-sena-result` |

These URIs are not just opaque identifiers -- they are addresses you can
fetch.

### Rule 2 -- Use HTTP URIs

All CDS URIs use HTTPS and are served by `signed-data.org`. No custom URI
schemes, no URNs, no proprietary namespaces. Any HTTP client on any
platform can resolve them.

### Rule 3 -- Provide useful information when a URI is looked up

Every CDS URI returns a JSON-LD document when dereferenced with an HTTP GET:

```
GET /sources/caixa.gov.br.loterias.v1 HTTP/1.1
Host: signed-data.org
Accept: application/ld+json

200 OK
Content-Type: application/ld+json

{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@id": "https://signed-data.org/sources/caixa.gov.br.loterias.v1",
  "name": "Caixa Econômica Federal — Loterias API v1",
  "url": "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena",
  "country": "BR",
  "domains": ["lottery-brazil"],
  ...
}
```

```
GET /vocab/ HTTP/1.1
Host: signed-data.org

200 OK
Content-Type: application/ld+json

{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@graph": [
    { "@id": "cds:contentType", "@type": "rdf:Property", ... },
    { "@id": "cds:occurredAt", "@type": "rdf:Property", ... },
    ...
  ]
}
```

### Rule 4 -- Include links to other URIs

Every CDS document contains outbound links:

- An **event** links to its source via `source.@id`.
- The **source** document links to its domains (e.g., `lottery-brazil`).
- The **domains** link to the vocabulary, which defines every content type
  and property.

This creates a navigable graph. Starting from any event, you can follow
links to discover what it means, where it came from, and what other data
the same source publishes.

---

## 3. JSON-LD: why not RDF/Turtle

Developer ergonomics.

JSON-LD is valid JSON. An existing consumer that reads JSON from an HTTP
endpoint does not need a JSON-LD processor, does not need to learn Turtle
syntax, and does not need to install an RDF library. The event payload
looks like ordinary JSON:

```json
{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@id": "https://signed-data.org/events/a3f1c9e0-...",
  "content_type": "https://signed-data.org/vocab/lottery-brazil/mega-sena-result",
  "occurred_at": "2026-03-29T00:00:00Z",
  "source": {
    "@id": "https://signed-data.org/sources/caixa.gov.br.loterias.v1"
  }
}
```

The `@context` is a single URL that maps snake_case keys to full RDF
predicates behind the scenes. For example, `content_type` maps to
`https://signed-data.org/vocab/cds#contentType` and `occurred_at` maps
to `https://signed-data.org/vocab/cds#occurredAt`. Consumers that do not
care about RDF ignore `@context` entirely and read the JSON as-is.

No Turtle. No SPARQL required for basic use. If you need RDF, any JSON-LD
processor will expand the same document into N-Triples, Turtle, or
RDF/XML.

---

## 4. The 5-star rating

Tim Berners-Lee defined a 5-star scheme for open data. CDS earns all five.

| Stars | Criterion | How CDS meets it |
|---|---|---|
| &#9733; | Available on the web with an open license | All CDS schemas, libraries, and tooling are MIT-licensed. Events are published at HTTPS URIs. |
| &#9733;&#9733; | Available as machine-readable structured data | Events are JSON -- parseable by every language and platform. |
| &#9733;&#9733;&#9733; | Available in a non-proprietary open format | JSON is an open ECMA/IETF standard (RFC 8259), not a proprietary format like Excel or PDF. |
| &#9733;&#9733;&#9733;&#9733; | Published using open standards from W3C | Every event carries a JSON-LD `@context`. Fields map to W3C RDF predicates. |
| &#9733;&#9733;&#9733;&#9733;&#9733; | All of the above, plus links to other data | Events link to source URIs, source URIs link to domain vocabularies, vocabulary URIs link to RDF definitions. The graph is connected. |

---

## 5. Dereferencing a CDS event

Take a Mega Sena event and follow the links step by step.

**Step 1 -- Resolve the content type.**

The event contains:
```json
"content_type": "https://signed-data.org/vocab/lottery-brazil/mega-sena-result"
```

Dereference it:
```
GET /vocab/lottery-brazil/mega-sena-result HTTP/1.1
Host: signed-data.org

200 OK
{
  "@id": "https://signed-data.org/vocab/lottery-brazil/mega-sena-result",
  "label": "Mega Sena draw result",
  "description": "Official result of a Mega Sena lottery draw conducted by Caixa Econômica Federal.",
  "domain": "lottery-brazil"
}
```

Now you know what the event represents.

**Step 2 -- Resolve the source.**

The event contains:
```json
"source": {
  "@id": "https://signed-data.org/sources/caixa.gov.br.loterias.v1"
}
```

Dereference it:
```
GET /sources/caixa.gov.br.loterias.v1 HTTP/1.1
Host: signed-data.org

200 OK
{
  "@id": "https://signed-data.org/sources/caixa.gov.br.loterias.v1",
  "name": "Caixa Econômica Federal — Loterias API v1",
  "url": "https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena",
  "country": "BR",
  "license": "public-domain",
  "domains": ["lottery-brazil"]
}
```

Now you know where the data came from and how to reach the upstream API.

**Step 3 -- Resolve the context.**

The event contains:
```json
"@context": "https://signed-data.org/contexts/cds/v1.jsonld"
```

Dereference it:
```
GET /contexts/cds/v1.jsonld HTTP/1.1
Host: signed-data.org

200 OK
{
  "@context": {
    "cds": "https://signed-data.org/vocab/cds#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "content_type": { "@id": "cds:contentType", "@type": "@id" },
    "occurred_at":  { "@id": "cds:occurredAt",  "@type": "xsd:dateTime" },
    "source":       { "@id": "cds:source",       "@type": "@id" },
    "fingerprint":  { "@id": "cds:fingerprint" },
    "payload":      { "@id": "cds:payload" },
    ...
  }
}
```

Now you know the RDF mapping for every field in the event.

---

## 6. How events become RDF triples

A JSON-LD processor expands the compact event into a set of RDF triples by
applying the `@context`. Here is what happens to three representative
fields.

**Source event (compact):**
```json
{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@id": "https://signed-data.org/events/a3f1c9e0-7b2d-4e8a-9f01-abc123def456",
  "content_type": "https://signed-data.org/vocab/lottery-brazil/mega-sena-result",
  "occurred_at": "2026-03-29T00:00:00Z",
  "source": {
    "@id": "https://signed-data.org/sources/caixa.gov.br.loterias.v1"
  }
}
```

**Expanded RDF triples:**

| Subject | Predicate | Object |
|---|---|---|
| `<https://signed-data.org/events/a3f1c9e0-...>` | `cds:contentType` | `<https://signed-data.org/vocab/lottery-brazil/mega-sena-result>` |
| `<https://signed-data.org/events/a3f1c9e0-...>` | `cds:occurredAt` | `"2026-03-29T00:00:00Z"^^xsd:dateTime` |
| `<https://signed-data.org/events/a3f1c9e0-...>` | `cds:source` | `<https://signed-data.org/sources/caixa.gov.br.loterias.v1>` |

The `@context` is the bridge. The compact form uses developer-friendly
snake_case keys; the expanded form uses full RDF predicates. Both
representations carry the same semantics.

In N-Triples syntax the first triple looks like:

```
<https://signed-data.org/events/a3f1c9e0-7b2d-4e8a-9f01-abc123def456>
  <https://signed-data.org/vocab/cds#contentType>
  <https://signed-data.org/vocab/lottery-brazil/mega-sena-result> .
```

---

## 7. The source registry

The source registry is the canonical list of data sources that CDS
recognises. Each entry is a JSON-LD document served from
`https://signed-data.org/sources/{source-id}`.

**Fields in a source document:**

| Field | Type | Description |
|---|---|---|
| `name` | string | Human-readable name of the source |
| `url` | string | Base URL of the upstream API |
| `auth` | string | Authentication method (`none`, `api-key`, `oauth2`) |
| `license` | string | License of the source data (`public-domain`, `cc-by-4.0`, etc.) |
| `country` | string | ISO 3166-1 alpha-2 country code |
| `domains` | string[] | List of domain identifiers (e.g., `["lottery-brazil"]`) |
| `fingerprint_algorithm` | string | Hash algorithm used for source fingerprints (e.g., `sha256`) |
| `certified_at` | string | ISO 8601 timestamp when the source was certified |
| `certified_by` | string | Identifier of the entity that certified the source |

**Looking up a source:**

```
GET https://signed-data.org/sources/caixa.gov.br.loterias.v1
```

Under the hood, CloudFront rewrites dots in the source ID to hyphens in the
S3 filename. The request above resolves to the object
`sources/caixa-gov-br-loterias-v1.json` in the backing bucket. This avoids
problems with dots in S3 key paths while keeping the logical URI clean.

---

## 8. Self-hosting vocabulary

If you run your own CDS issuer, you are not required to use
`signed-data.org`. You can publish your own vocabulary and source
definitions at your own domain.

**Minimum requirements:**

1. **Vocabulary.** Serve your ontology at
   `https://yourorg.example.com/vocab/`. Publish a `cds.jsonld` file at
   the root that defines your custom content types and properties.

2. **Source documents.** Serve source metadata at
   `https://yourorg.example.com/sources/{source-id}` using the same
   schema described in section 7.

3. **JSON-LD context.** Serve a context document at
   `https://yourorg.example.com/contexts/cds/v1.jsonld` that maps your
   field names to your vocabulary namespace.

4. **Public key.** Publish your RSA public key at
   `https://yourorg.example.com/.well-known/cds-public-key.pem`
   so that consumers can verify event signatures without out-of-band key
   exchange.

Your events will then reference your own URIs:

```json
{
  "@context": "https://yourorg.example.com/contexts/cds/v1.jsonld",
  "@id": "https://yourorg.example.com/events/...",
  "source": {
    "@id": "https://yourorg.example.com/sources/my-source.v1"
  }
}
```

Consumers that understand JSON-LD can follow these URIs exactly the same
way they follow `signed-data.org` URIs. The protocol is the same; only the
domain changes.

---

## 9. Future: SPARQL

Because CDS events are valid JSON-LD, they are valid RDF. This means any
collection of events can be loaded into a triple store (Apache Jena,
Blazegraph, Amazon Neptune, Oxigraph, etc.) and queried with SPARQL.

**Example: find all lottery events from March 2026.**

```sparql
PREFIX cds: <https://signed-data.org/vocab/cds#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?event ?contentType ?occurredAt
WHERE {
  ?event cds:contentType ?contentType ;
         cds:occurredAt  ?occurredAt .

  FILTER (
    STRSTARTS(STR(?contentType), "https://signed-data.org/vocab/lottery-brazil/")
    && ?occurredAt >= "2026-03-01T00:00:00Z"^^xsd:dateTime
    && ?occurredAt <  "2026-04-01T00:00:00Z"^^xsd:dateTime
  )
}
ORDER BY ?occurredAt
```

This is not a feature CDS needs to build -- it falls out of the data model
for free. Any standards-compliant SPARQL endpoint will accept these queries
once the events are loaded. The investment in Linked Data pays forward:
every new event that enters the triple store is immediately queryable
alongside every other event, across sources, domains, and time ranges,
without writing any new code.
