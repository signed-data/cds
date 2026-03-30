/**
 * SignedData CDS — TypeScript SDK Test Suite
 */
import { describe, it, expect, beforeAll } from "vitest";
import { mkdirSync, existsSync } from "node:fs";
import { CDSEvent, CDSContentType } from "../src/schema.js";
import { CDSSigner, CDSVerifier, generateKeypair } from "../src/signer.js";
import { FootballContentTypes } from "../src/sources/football.js";
import type { FootballMatchPayload } from "../src/sources/football.js";

let signer:   CDSSigner;
let verifier: CDSVerifier;

beforeAll(() => {
  if (!existsSync("test-keys")) mkdirSync("test-keys");
  if (!existsSync("test-keys/private.pem"))
    generateKeypair("test-keys/private.pem", "test-keys/public.pem");
  signer   = new CDSSigner("test-keys/private.pem", "test.signed-data.org");
  verifier = new CDSVerifier("test-keys/public.pem");
});

function makeEvent(): CDSEvent {
  const payload: FootballMatchPayload = {
    home: { name: "Flamengo",   short_name: "FLA", score: 2, logo_url: "" },
    away: { name: "Fluminense", short_name: "FLU", score: 1, logo_url: "" },
    status: "finished", competition: "Brasileirão Série A", season: "2026",
    venue: { name: "", city: "", country: "" }, referee: "", match_date: "2026-03-22",
  };
  const event = new CDSEvent({
    content_type: FootballContentTypes.MATCH_RESULT,
    source:       { id: "api-football.com.v3", fingerprint: "sha256:abc" },
    occurred_at:  "2026-03-22T21:00:00Z",
    lang:         "en",
    payload:      payload as unknown as Record<string, unknown>,
    context: { summary: "Flamengo 2 x 1 Fluminense", model: "rule-based-v1", generated_at: new Date().toISOString() },
  });
  signer.sign(event);
  return event;
}

describe("CDSContentType", () => {
  it("generates correct MIME for weather", () => {
    const ct = new CDSContentType({ domain: "weather", schema_name: "forecast.current" });
    expect(ct.mime_type).toBe("application/vnd.cds.weather.forecast-current+json;v=1");
  });
  it("generates correct MIME for football", () => {
    expect(FootballContentTypes.MATCH_RESULT.mime_type)
      .toBe("application/vnd.cds.sports-football.match-result+json;v=1");
  });
  it("serialises to JSON", () => {
    const j = FootballContentTypes.MATCH_RESULT.toJSON();
    expect(j.domain).toBe("sports.football");
    expect(j.schema_name).toBe("match.result");
  });
});

describe("CDSEvent", () => {
  it("canonical bytes are deterministic", () => {
    const e = makeEvent();
    expect(e.canonicalBytes().toString("hex")).toBe(e.canonicalBytes().toString("hex"));
  });
  it("canonical excludes integrity and ingested_at", () => {
    const parsed = JSON.parse(makeEvent().canonicalBytes().toString("utf-8"));
    expect(parsed.integrity).toBeUndefined();
    expect(parsed.ingested_at).toBeUndefined();
  });
  it("domain / event_type shortcuts", () => {
    const e = makeEvent();
    expect(e.domain).toBe("sports.football");
    expect(e.event_type).toBe("match.result");
  });
  it("fromJSON round-trip", () => {
    const e = makeEvent();
    const r = CDSEvent.fromJSON(JSON.parse(JSON.stringify(e.toJSON())));
    expect(r.id).toBe(e.id);
    expect(r.content_type.mime_type).toBe(e.content_type.mime_type);
  });
});

describe("CDSSigner", () => {
  it("attaches integrity", () => {
    const e = makeEvent();
    expect(e.integrity).toBeDefined();
    expect(e.integrity!.hash).toMatch(/^sha256:/);
    expect(e.integrity!.signed_by).toBe("test.signed-data.org");
  });
  it("hash matches canonical bytes", async () => {
    const { createHash } = await import("node:crypto");
    const e = makeEvent();
    const expected = "sha256:" + createHash("sha256").update(e.canonicalBytes()).digest("hex");
    expect(e.integrity!.hash).toBe(expected);
  });
});

describe("CDSVerifier", () => {
  it("verifies valid event", () => {
    expect(verifier.verify(makeEvent())).toBe(true);
  });
  it("rejects tampered score", () => {
    const e = makeEvent();
    const r = CDSEvent.fromJSON(JSON.parse(JSON.stringify(e.toJSON())));
    (r.payload["home"] as Record<string, unknown>)["score"] = 99;
    expect(() => verifier.verify(r)).toThrow();
  });
  it("rejects tampered summary", () => {
    const e = makeEvent();
    const r = CDSEvent.fromJSON(JSON.parse(JSON.stringify(e.toJSON())));
    r.context!.summary = "tampered";
    expect(() => verifier.verify(r)).toThrow();
  });
  it("throws on missing integrity", () => {
    const e = new CDSEvent({
      content_type: FootballContentTypes.MATCH_RESULT,
      source: { id: "test" }, occurred_at: new Date().toISOString(), payload: {},
    });
    expect(() => verifier.verify(e)).toThrow("no integrity");
  });
  it("verifies after JSON round-trip", () => {
    const e = makeEvent();
    const r = CDSEvent.fromJSON(JSON.parse(JSON.stringify(e.toJSON())));
    expect(verifier.verify(r)).toBe(true);
  });
});
