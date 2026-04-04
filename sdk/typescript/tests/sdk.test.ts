import { describe, it, expect, beforeAll } from "vitest";
import { mkdirSync, existsSync }            from "node:fs";
import { createHash }                       from "node:crypto";
import { CDSEvent }                         from "../src/schema.js";
import { CDSSigner, CDSVerifier, generateKeypair } from "../src/signer.js";
import { CDSVocab, CDSSources, CDS_CONTEXT_URI, CDS_EVENT_TYPE_URI } from "../src/vocab.js";
import { LotteryContentTypes }              from "../src/sources/lottery.js";
import { FootballContentTypes }             from "../src/sources/football.js";
import { FinanceContentTypes }              from "../src/sources/finance.js";
import { CompaniesContentTypes, validateCnpj, formatCnpj } from "../src/sources/companies.js";
import { CommodityContentTypes }            from "../src/sources/commodities.js";

let signer:   CDSSigner;
let verifier: CDSVerifier;

beforeAll(() => {
  if (!existsSync("test-keys")) mkdirSync("test-keys");
  if (!existsSync("test-keys/private.pem"))
    generateKeypair("test-keys/private.pem", "test-keys/public.pem");
  signer   = new CDSSigner("test-keys/private.pem", "https://signed-data.org");
  verifier = new CDSVerifier("test-keys/public.pem");
});

const makeEvent = () => new CDSEvent({
  content_type: CDSVocab.LOTTERY_MEGA_SENA,
  source:       { "@id": CDSSources.CAIXA_LOTERIAS, fingerprint: "sha256:mock" },
  occurred_at:  "2026-03-29T00:00:00Z",
  lang:         "pt-BR",
  payload:      { concurso: 2800, dezenas: ["04","12","25","36","47","59"] },
  context:      { summary: "Mega Sena 2800", model: "rule-based-v1", generated_at: new Date().toISOString() },
});

describe("CDSVocab", () => {
  it("lottery mega sena URI", () =>
    expect(CDSVocab.LOTTERY_MEGA_SENA)
      .toBe("https://signed-data.org/vocab/lottery-brazil/mega-sena-result"));
  it("football match result URI", () =>
    expect(CDSVocab.FOOTBALL_MATCH_RESULT)
      .toBe("https://signed-data.org/vocab/sports-football/match-result"));
  it("LotteryContentTypes equal CDSVocab", () =>
    expect(LotteryContentTypes.MEGA_SENA).toBe(CDSVocab.LOTTERY_MEGA_SENA));
  it("FootballContentTypes equal CDSVocab", () =>
    expect(FootballContentTypes.MATCH_RESULT).toBe(CDSVocab.FOOTBALL_MATCH_RESULT));
});

describe("CDSEvent construction", () => {
  it("@context is set",   () => expect(makeEvent()["@context"]).toBe(CDS_CONTEXT_URI));
  it("@type is set",      () => expect(makeEvent()["@type"]).toBe(CDS_EVENT_TYPE_URI));
  it("@id is set",        () => expect(makeEvent()["@id"]).toMatch(/^https:\/\/signed-data\.org\/events\//));
  it("content_type is URI", () => expect(makeEvent().content_type).toMatch(/^https:\/\/signed-data\.org\/vocab\//));
  it("source @id is URI",   () => expect(makeEvent().source["@id"]).toMatch(/^https:\/\/signed-data\.org\/sources\//));
  it("spec_version is 0.2.0", () => expect(makeEvent().spec_version).toBe("0.2.0"));
  it("domain shortcut",   () => expect(makeEvent().domain).toBe("lottery.brazil"));
  it("event_type shortcut", () => expect(makeEvent().event_type).toBe("mega-sena.result"));
});

describe("canonicalBytes", () => {
  it("includes @context/@type/@id", () => {
    const d = JSON.parse(makeEvent().canonicalBytes().toString("utf-8"));
    expect(d["@context"]).toBeDefined();
    expect(d["@type"]).toBeDefined();
    expect(d["@id"]).toBeDefined();
  });
  it("excludes integrity", () => {
    const e = makeEvent(); signer.sign(e);
    expect(JSON.parse(e.canonicalBytes().toString("utf-8"))["integrity"]).toBeUndefined();
  });
  it("excludes ingested_at", () =>
    expect(JSON.parse(makeEvent().canonicalBytes().toString("utf-8"))["ingested_at"])
      .toBeUndefined());
  it("is deterministic", () => {
    const e = makeEvent();
    expect(e.canonicalBytes().toString("hex")).toBe(e.canonicalBytes().toString("hex"));
  });
});

describe("signing and verification", () => {
  it("verifies valid event", () => { const e = makeEvent(); signer.sign(e); expect(verifier.verify(e)).toBe(true); });
  it("signed_by is URI",     () => { const e = makeEvent(); signer.sign(e); expect(e.integrity!.signed_by).toBe("https://signed-data.org"); });
  it("rejects tampered payload", () => {
    const e = makeEvent(); signer.sign(e);
    (e.payload["concurso"] as unknown) = 9999;
    expect(() => verifier.verify(e)).toThrow();
  });
  it("verifies after roundtrip", () => {
    const e = makeEvent(); signer.sign(e);
    const r = CDSEvent.fromJSON(JSON.parse(JSON.stringify(e.toJSON())));
    expect(verifier.verify(r)).toBe(true);
  });
  it("throws with no integrity", () =>
    expect(() => verifier.verify(makeEvent())).toThrow());
});

// ── Finance Brazil ───────────────────────────────────────

const makeFinanceEvent = () => new CDSEvent({
  content_type: CDSVocab.FINANCE_SELIC_RATE,
  source:       { "@id": CDSSources.BCB_API, fingerprint: "sha256:mock" },
  occurred_at:  "2026-04-02T18:30:00-03:00",
  lang:         "pt-BR",
  payload:      { date: "2026-04-02", rate_annual: 13.75, rate_daily: 0.0529, unit: "% a.a.", effective_date: "2026-04-02" },
  context:      { summary: "SELIC: 13.75% a.a. (2026-04-02)", model: "rule-based-v1", generated_at: new Date().toISOString() },
});

describe("Finance Brazil content types", () => {
  it("SELIC URI", () =>
    expect(FinanceContentTypes.SELIC)
      .toBe("https://signed-data.org/vocab/finance-brazil/rate-selic"));
  it("STOCK URI", () =>
    expect(FinanceContentTypes.STOCK)
      .toBe("https://signed-data.org/vocab/finance-brazil/quote-stock"));
  it("COPOM URI", () =>
    expect(FinanceContentTypes.COPOM)
      .toBe("https://signed-data.org/vocab/finance-brazil/decision-copom"));
  it("all are URIs", () => {
    for (const ct of Object.values(FinanceContentTypes)) {
      expect(ct).toMatch(/^https:\/\/signed-data\.org\/vocab\/finance-brazil\//);
    }
  });
  it("FinanceContentTypes equal CDSVocab", () => {
    expect(FinanceContentTypes.SELIC).toBe(CDSVocab.FINANCE_SELIC_RATE);
    expect(FinanceContentTypes.STOCK).toBe(CDSVocab.FINANCE_QUOTE_STOCK);
  });
});

describe("Finance Brazil event construction", () => {
  it("domain is finance.brazil", () =>
    expect(makeFinanceEvent().domain).toBe("finance.brazil"));
  it("event_type is rate.selic", () =>
    expect(makeFinanceEvent().event_type).toBe("rate.selic"));
  it("source @id is BCB", () =>
    expect(makeFinanceEvent().source["@id"]).toBe(CDSSources.BCB_API));
  it("signs and verifies", () => {
    const e = makeFinanceEvent();
    signer.sign(e);
    expect(e.integrity).toBeDefined();
    expect(verifier.verify(e)).toBe(true);
  });
  it("verifies after roundtrip", () => {
    const e = makeFinanceEvent();
    signer.sign(e);
    const r = CDSEvent.fromJSON(JSON.parse(JSON.stringify(e.toJSON())));
    expect(verifier.verify(r)).toBe(true);
  });
});

// ── Companies Brazil ─────────────────────────────────────

describe("Companies Brazil content types", () => {
  it("PROFILE URI", () =>
    expect(CompaniesContentTypes.PROFILE)
      .toBe("https://signed-data.org/vocab/companies-brazil/profile-cnpj"));
  it("PARTNERS URI", () =>
    expect(CompaniesContentTypes.PARTNERS)
      .toBe("https://signed-data.org/vocab/companies-brazil/partners-cnpj"));
  it("all are URIs", () => {
    for (const ct of Object.values(CompaniesContentTypes)) {
      expect(ct).toMatch(/^https:\/\/signed-data\.org\/vocab\/companies-brazil\//);
    }
  });
  it("equals CDSVocab", () => {
    expect(CompaniesContentTypes.PROFILE).toBe(CDSVocab.COMPANIES_PROFILE_CNPJ);
    expect(CompaniesContentTypes.PARTNERS).toBe(CDSVocab.COMPANIES_PARTNERS_CNPJ);
  });
});

describe("CNPJ validation", () => {
  it("validates correct CNPJ", () =>
    expect(validateCnpj("33000167000101")).toBe("33000167000101"));
  it("accepts formatted input", () =>
    expect(validateCnpj("33.000.167/0001-01")).toBe("33000167000101"));
  it("rejects invalid check digits", () =>
    expect(() => validateCnpj("33000167000199")).toThrow("check digit"));
  it("rejects too short", () =>
    expect(() => validateCnpj("1234")).toThrow("14 digits"));
  it("rejects all same digits", () =>
    expect(() => validateCnpj("11111111111111")).toThrow("same digits"));
  it("formats CNPJ correctly", () =>
    expect(formatCnpj("33000167000101")).toBe("33.000.167/0001-01"));
});

describe("Companies Brazil event construction", () => {
  const makeCompanyEvent = () => new CDSEvent({
    content_type: CDSVocab.COMPANIES_PROFILE_CNPJ,
    source: { "@id": CDSSources.BRASILAPI, fingerprint: "sha256:mock" },
    occurred_at: "2026-04-02T14:30:00-03:00",
    lang: "pt-BR",
    payload: { cnpj: "33000167000101", company_name: "PETROBRAS" },
    context: { summary: "PETROBRAS", model: "rule-based-v1", generated_at: new Date().toISOString() },
  });

  it("domain is companies.brazil", () =>
    expect(makeCompanyEvent().domain).toBe("companies.brazil"));
  it("event_type is profile.cnpj", () =>
    expect(makeCompanyEvent().event_type).toBe("profile.cnpj"));
  it("source @id is BrasilAPI", () =>
    expect(makeCompanyEvent().source["@id"]).toBe(CDSSources.BRASILAPI));
  it("signs and verifies", () => {
    const e = makeCompanyEvent();
    signer.sign(e);
    expect(verifier.verify(e)).toBe(true);
  });
});

// ── Commodities Brazil ───────────────────────────────────

describe("Commodities Brazil content types", () => {
  it("FUTURES_SOJA URI", () =>
    expect(CommodityContentTypes.FUTURES_SOJA)
      .toBe("https://signed-data.org/vocab/commodities-brazil/futures-soja"));
  it("SPOT_SOJA URI", () =>
    expect(CommodityContentTypes.SPOT_SOJA)
      .toBe("https://signed-data.org/vocab/commodities-brazil/spot-soja"));
  it("all are URIs", () => {
    for (const ct of Object.values(CommodityContentTypes)) {
      expect(ct).toMatch(/^https:\/\/signed-data\.org\/vocab\/commodities-brazil\//);
    }
  });
  it("equals CDSVocab", () => {
    expect(CommodityContentTypes.FUTURES_SOJA).toBe(CDSVocab.COMMODITY_FUTURES_SOJA);
    expect(CommodityContentTypes.SPOT_MILHO).toBe(CDSVocab.COMMODITY_SPOT_MILHO);
  });
});

describe("Commodities Brazil event construction", () => {
  const makeFuturesEvent = () => new CDSEvent({
    content_type: CDSVocab.COMMODITY_FUTURES_SOJA,
    source: { "@id": CDSSources.BRAPI, fingerprint: "sha256:mock" },
    occurred_at: "2026-04-02T14:30:00-03:00",
    lang: "pt-BR",
    payload: { commodity: "soja", ticker: "SFI", price: 146.50 },
    context: { summary: "Soja B3 (SFI): R$ 146.50", model: "rule-based-v1", generated_at: new Date().toISOString() },
  });

  it("domain is commodities.brazil", () =>
    expect(makeFuturesEvent().domain).toBe("commodities.brazil"));
  it("event_type is futures.soja", () =>
    expect(makeFuturesEvent().event_type).toBe("futures.soja"));
  it("source @id is Brapi", () =>
    expect(makeFuturesEvent().source["@id"]).toBe(CDSSources.BRAPI));
  it("signs and verifies", () => {
    const e = makeFuturesEvent();
    signer.sign(e);
    expect(e.integrity).toBeDefined();
    expect(verifier.verify(e)).toBe(true);
  });
});
