/**
 * SignedData CDS — MegaSenaIngestor Tests
 */
import { describe, it, expect, vi, beforeAll } from "vitest";
import { mkdirSync, existsSync } from "node:fs";
import { MegaSenaIngestor, LotteryContentTypes } from "../src/index.js";
import { CDSSigner, generateKeypair } from "../src/signer.js";

// ── Fixtures ───────────────────────────────────────────────

const SAMPLE_ACCUMULATED: Record<string, unknown> = {
  numero: 2799,
  dataApuracao: "26/03/2026",
  localSorteio: "Local do Sorteio",
  nomeMunicipiUFSorteio: "São Paulo/SP",
  listaDezenas: ["04", "12", "25", "36", "47", "59"],
  listaDezenasOrdemSorteio: ["47", "12", "04", "59", "25", "36"],
  acumulado: true,
  listaRateioPremio: [
    { descricao: "Sena",   numeroDeGanhadores: 0,    valorPremio: 0 },
    { descricao: "Quina",  numeroDeGanhadores: 42,   valorPremio: 15000 },
    { descricao: "Quadra", numeroDeGanhadores: 3870, valorPremio: 800 },
  ],
  valorArrecadado: 85000000,
  valorEstimadoProximoConcurso: 100000000,
  dataProximoConcurso: "29/03/2026",
  numeroConcursoAnterior: 2798,
  numeroConcursoProximo: 2800,
};

const SAMPLE_WON: Record<string, unknown> = {
  numero: 2800,
  dataApuracao: "29/03/2026",
  localSorteio: "Local do Sorteio",
  nomeMunicipiUFSorteio: "São Paulo/SP",
  listaDezenas: ["03", "11", "17", "27", "42", "55"],
  listaDezenasOrdemSorteio: ["17", "03", "55", "11", "27", "42"],
  acumulado: false,
  listaRateioPremio: [
    { descricao: "Sena",   numeroDeGanhadores: 1,    valorPremio: 45000000 },
    { descricao: "Quina",  numeroDeGanhadores: 55,   valorPremio: 12000 },
    { descricao: "Quadra", numeroDeGanhadores: 4200, valorPremio: 650 },
  ],
  valorArrecadado: 90000000,
  valorEstimadoProximoConcurso: 3000000,
  dataProximoConcurso: "01/04/2026",
  numeroConcursoAnterior: 2799,
  numeroConcursoProximo: 2801,
};

function mockFetchOnce(data: unknown) {
  const buf = Buffer.from(JSON.stringify(data));
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce({
    ok: true,
    arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength),
  }));
}

// ── Setup ──────────────────────────────────────────────────

let signer: CDSSigner;

beforeAll(() => {
  if (!existsSync("test-keys")) mkdirSync("test-keys");
  if (!existsSync("test-keys/private.pem"))
    generateKeypair("test-keys/private.pem", "test-keys/public.pem");
  signer = new CDSSigner("test-keys/private.pem", "test.signed-data.org");
});

// ── Tests ──────────────────────────────────────────────────

describe("LotteryContentTypes", () => {
  it("has all five lottery types", () => {
    expect(Object.keys(LotteryContentTypes)).toHaveLength(5);
  });
  it("all content types are distinct URIs", () => {
    const uris = Object.values(LotteryContentTypes);
    expect(new Set(uris).size).toBe(uris.length);
  });
});

describe("MegaSenaIngestor", () => {
  it("contentType is MEGA_SENA", () => {
    const ingestor = new MegaSenaIngestor(signer);
    expect(ingestor.contentType).toBe(LotteryContentTypes.MEGA_SENA);
  });

  it("ingest() returns a signed event for an accumulated draw", async () => {
    mockFetchOnce(SAMPLE_ACCUMULATED);

    const ingestor = new MegaSenaIngestor(signer);
    const events = await ingestor.ingest();

    expect(events).toHaveLength(1);
    const event = events[0];

    expect(event.domain).toBe("lottery.brazil");
    expect(event.event_type).toBe("mega-sena.result");
    expect(event.lang).toBe("pt-BR");
    expect(event.integrity).toBeDefined();
    expect(event.integrity!.signed_by).toBe("test.signed-data.org");

    const payload = event.payload as Record<string, unknown>;
    expect(payload["concurso"]).toBe(2799);
    expect(payload["acumulado"]).toBe(true);
    expect(payload["dezenas"]).toEqual(["04", "12", "25", "36", "47", "59"]);
    expect(payload["data_apuracao_iso"]).toBe("2026-03-26");

    expect(event.context?.summary).toContain("2799");
    expect(event.context?.summary).toContain("ACUMULOU");
    expect(event.context?.summary).toContain("100.000.000");

    vi.unstubAllGlobals();
  });

  it("ingest() returns a signed event for a won draw", async () => {
    mockFetchOnce(SAMPLE_WON);

    const ingestor = new MegaSenaIngestor(signer);
    const events = await ingestor.ingest();

    expect(events).toHaveLength(1);
    const event = events[0];

    const payload = event.payload as Record<string, unknown>;
    expect(payload["concurso"]).toBe(2800);
    expect(payload["acumulado"]).toBe(false);
    expect(payload["dezenas"]).toEqual(["03", "11", "17", "27", "42", "55"]);

    expect(event.context?.summary).toContain("2800");
    expect(event.context?.summary).toContain("1 ganhador");
    expect(event.context?.summary).toContain("45.000.000");

    vi.unstubAllGlobals();
  });

  it("occurred_at is midnight UTC the next day after draw date (21:00 BRT → 00:00 UTC)", async () => {
    mockFetchOnce(SAMPLE_WON);

    const ingestor = new MegaSenaIngestor(signer);
    const events = await ingestor.fetch();

    // Draw date 29/03/2026 at 21:00 BRT (UTC−03:00) = 00:00 UTC on 30/03/2026
    expect(events[0].occurred_at).toBe("2026-03-30T00:00:00.000Z");

    vi.unstubAllGlobals();
  });

  it("fetch() with specific concursos fetches each one", async () => {
    const buf1 = Buffer.from(JSON.stringify(SAMPLE_ACCUMULATED));
    const buf2 = Buffer.from(JSON.stringify(SAMPLE_WON));
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        arrayBuffer: async () => buf1.buffer.slice(buf1.byteOffset, buf1.byteOffset + buf1.byteLength),
      })
      .mockResolvedValueOnce({
        ok: true,
        arrayBuffer: async () => buf2.buffer.slice(buf2.byteOffset, buf2.byteOffset + buf2.byteLength),
      }),
    );

    const ingestor = new MegaSenaIngestor(signer, { concursos: [2799, 2800] });
    const events = await ingestor.fetch();

    expect(events).toHaveLength(2);
    expect((events[0].payload as Record<string, unknown>)["concurso"]).toBe(2799);
    expect((events[1].payload as Record<string, unknown>)["concurso"]).toBe(2800);

    vi.unstubAllGlobals();
  });

  it("fetch() throws on HTTP error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce({ ok: false, status: 500 }));

    const ingestor = new MegaSenaIngestor(signer);
    await expect(ingestor.fetch()).rejects.toThrow("HTTP 500");

    vi.unstubAllGlobals();
  });

  it("source fingerprint is sha256: prefixed", async () => {
    mockFetchOnce(SAMPLE_WON);

    const ingestor = new MegaSenaIngestor(signer);
    const events = await ingestor.fetch();

    expect(events[0].source.fingerprint).toMatch(/^sha256:[0-9a-f]{64}$/);

    vi.unstubAllGlobals();
  });
});
