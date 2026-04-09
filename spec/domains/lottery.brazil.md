# Domain: lottery.brazil

**Status:** Active  
**Source:** Caixa Econômica Federal — Loterias  
**Source URI:** `https://signed-data.org/sources/caixa.gov.br.loterias.v1`  
**API base:** `https://servicebus2.caixa.gov.br/portaldeloterias/api`  
**Auth:** None (public)  
**Country:** BR

---

## Linked Data URIs

| Schema | Content type URI |
|---|---|
| Mega Sena result | `https://signed-data.org/vocab/lottery-brazil/mega-sena-result` |
| Lotofácil result | `https://signed-data.org/vocab/lottery-brazil/lotofacil-result` |
| Quina result | `https://signed-data.org/vocab/lottery-brazil/quina-result` |
| Lotomania result | `https://signed-data.org/vocab/lottery-brazil/lotomania-result` |
| Dupla Sena result | `https://signed-data.org/vocab/lottery-brazil/dupla-sena-result` |

Source document: `https://signed-data.org/sources/caixa.gov.br.loterias.v1`  
Domain vocabulary: `https://signed-data.org/vocab/domains/lottery-brazil.jsonld`

---

## Event example (v0.2.0)

```json
{
  "@context": "https://signed-data.org/contexts/cds/v1.jsonld",
  "@type":    "https://signed-data.org/vocab/CuratedDataEvent",
  "@id":      "https://signed-data.org/events/a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d",

  "spec_version": "0.2.0",
  "id":           "a3f8c2d1-4e2b-4f8a-9c1d-2e3f4a5b6c7d",

  "content_type": "https://signed-data.org/vocab/lottery-brazil/mega-sena-result",

  "source": {
    "@id":         "https://signed-data.org/sources/caixa.gov.br.loterias.v1",
    "fingerprint": "sha256:b310739720e5f948..."
  },

  "occurred_at":  "2026-03-29T00:00:00Z",
  "ingested_at":  "2026-03-29T00:00:04Z",
  "lang":         "pt-BR",

  "payload": {
    "concurso": 2800,
    "data_apuracao": "29/03/2026",
    "data_apuracao_iso": "2026-03-29",
    "dezenas": ["04", "12", "25", "36", "47", "59"],
    "acumulado": false,
    "premiacoes": [
      {
        "tier": 1,
        "description": "Sena",
        "winners": 2,
        "prize_amount": 45000000.00,
        "total_prize": 90000000.00
      }
    ]
  },

  "context": {
    "summary": "Mega Sena concurso 2800 (29/03/2026): dezenas: 04 · 12 · 25 · 36 · 47 · 59. 2 ganhadores da sena, prêmio de R$ 45.000.000,00 cada.",
    "model": "rule-based-v1",
    "generated_at": "2026-03-29T00:00:05Z"
  },

  "integrity": {
    "hash":      "sha256:a1b2c3d4e5f6...",
    "signature": "MX6rj3qKQkpDIUbc1NXd...",
    "signed_by": "https://signed-data.org"
  }
}
```

---

## Games

### Mega Sena

- **Content type:** `https://signed-data.org/vocab/lottery-brazil/mega-sena-result`
- **Numbers:** 6 from 1–60
- **Draws:** Wednesday and Saturday
- **Endpoint:** `GET /portaldeloterias/api/megasena/{concurso}`

### Lotofácil

- **Content type:** `https://signed-data.org/vocab/lottery-brazil/lotofacil-result`
- **Numbers:** 15 from 1–25
- **Draws:** Monday–Friday
- **Endpoint:** `GET /portaldeloterias/api/lotofacil/{concurso}`

### Quina

- **Content type:** `https://signed-data.org/vocab/lottery-brazil/quina-result`
- **Numbers:** 5 from 1–80
- **Draws:** Monday–Friday
- **Endpoint:** `GET /portaldeloterias/api/quina/{concurso}`

### Lotomania

- **Content type:** `https://signed-data.org/vocab/lottery-brazil/lotomania-result`
- **Numbers:** 20 of 100
- **Draws:** Monday, Wednesday, Friday
- **Endpoint:** `GET /portaldeloterias/api/lotomania/{concurso}`

### Dupla Sena

- **Content type:** `https://signed-data.org/vocab/lottery-brazil/dupla-sena-result`
- **Numbers:** Two draws of 6 from 1–50
- **Draws:** Monday, Friday
- **Endpoint:** `GET /portaldeloterias/api/duplasena/{concurso}`

---

## Payload schema (MegaSenaResult)

| Field | Type | Description |
|---|---|---|
| `concurso` | `int` | Draw number |
| `data_apuracao` | `string` | Draw date (DD/MM/YYYY) |
| `data_apuracao_iso` | `string` | Draw date (YYYY-MM-DD) |
| `local_sorteio` | `string` | Venue name |
| `cidade_uf` | `string` | City/state |
| `dezenas` | `string[]` | Drawn numbers, sorted |
| `dezenas_ordem_sorteio` | `string[]` | Numbers in draw order |
| `acumulado` | `boolean` | True if jackpot rolled over |
| `premiacoes` | `PrizeTier[]` | Prize breakdown by tier |
| `valor_arrecadado` | `number` | Total revenue (BRL) |
| `valor_acumulado_proximo` | `number` | Next jackpot estimate (BRL) |
| `data_proximo_concurso` | `string` | Next draw date |
