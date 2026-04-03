import { describe, it, expect, beforeAll } from "vitest";
import { mkdirSync, existsSync }            from "node:fs";
import { createHash }                       from "node:crypto";
import { CDSEvent }                         from "../src/schema.js";
import { CDSSigner, CDSVerifier, generateKeypair } from "../src/signer.js";
import { CDSVocab, CDSSources, CDS_CONTEXT_URI, CDS_EVENT_TYPE_URI } from "../src/vocab.js";
import { LotteryContentTypes }              from "../src/sources/lottery.js";
import { FootballContentTypes }             from "../src/sources/football.js";

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
