/**
 * SignedData CDS — Commodities Brazil Source
 * Sources:
 *   B3 Futures: https://brapi.dev/api/quote/{tickers}
 *   CONAB:      https://consultaweb.conab.gov.br/consultas/consultaGrao/listar
 */

import { createHash } from "node:crypto";
import { CDSEvent, ContextMeta, SourceMeta } from "../schema.js";
import { CDSSigner } from "../signer.js";
import { BaseIngestor } from "../ingestor.js";
import { CDSVocab, CDSSources } from "../vocab.js";

// ── Content Types ──────────────────────────────────────────

export const CommodityContentTypes = {
  FUTURES_SOJA:    CDSVocab.COMMODITY_FUTURES_SOJA,
  FUTURES_MILHO:   CDSVocab.COMMODITY_FUTURES_MILHO,
  FUTURES_BOI:     CDSVocab.COMMODITY_FUTURES_BOI,
  FUTURES_CAFE:    CDSVocab.COMMODITY_FUTURES_CAFE,
  FUTURES_ACUCAR:  CDSVocab.COMMODITY_FUTURES_ACUCAR,
  FUTURES_ETANOL:  CDSVocab.COMMODITY_FUTURES_ETANOL,
  SPOT_SOJA:       CDSVocab.COMMODITY_SPOT_SOJA,
  SPOT_MILHO:      CDSVocab.COMMODITY_SPOT_MILHO,
  SPOT_TRIGO:      CDSVocab.COMMODITY_SPOT_TRIGO,
  SPOT_ALGODAO:    CDSVocab.COMMODITY_SPOT_ALGODAO,
  INDEX_WORLDBANK: CDSVocab.COMMODITY_INDEX_WORLDBANK,
} as const;

// ── Payload Types ──────────────────────────────────────────

export interface CommodityFutures {
  commodity: string;
  ticker: string;
  exchange: string;
  unit: string;
  contract_month: string;
  price: number;
  change: number;
  change_pct: number;
  open: number;
  day_high: number;
  day_low: number;
  volume: number;
  open_interest?: number;
  settlement_date?: string;
  timestamp: string;
}

export interface CommoditySpot {
  commodity: string;
  state: string;
  city?: string;
  unit: string;
  price: number;
  week: string;
  date_from: string;
  date_to: string;
  source: string;
  conab_notes?: string;
}

export interface CommodityIndex {
  indicator: string;
  name: string;
  date: string;
  value: number;
  unit: string;
  source: string;
}

// ── B3 ticker mapping ──────────────────────────────────────

export const B3_COMMODITY_TICKERS: Record<string, [string, string]> = {
  SFI: ["soja",      CommodityContentTypes.FUTURES_SOJA],
  CCM: ["milho",     CommodityContentTypes.FUTURES_MILHO],
  BGI: ["boi gordo", CommodityContentTypes.FUTURES_BOI],
  ICF: ["café",      CommodityContentTypes.FUTURES_CAFE],
  SWV: ["açúcar",    CommodityContentTypes.FUTURES_ACUCAR],
  ETN: ["etanol",    CommodityContentTypes.FUTURES_ETANOL],
};

// ── Helpers ────────────────────────────────────────────────

const BRAPI_BASE = "https://brapi.dev/api";

type R = Record<string, unknown>;

function fingerprint(data: Buffer): string {
  return "sha256:" + createHash("sha256").update(data).digest("hex");
}

// ── B3 Futures Ingestor ────────────────────────────────────

export interface B3FuturesOptions {
  commodities?: string[];
}

export class B3FuturesIngestor extends BaseIngestor {
  readonly contentType = CommodityContentTypes.FUTURES_SOJA;
  private readonly tickers: string[];

  constructor(signer: CDSSigner, opts: B3FuturesOptions = {}) {
    super(signer);
    this.tickers = opts.commodities
      ? opts.commodities.filter(t => t in B3_COMMODITY_TICKERS)
      : Object.keys(B3_COMMODITY_TICKERS);
  }

  async fetch(): Promise<CDSEvent[]> {
    const events: CDSEvent[] = [];
    const tickerStr = this.tickers.join(",");

    const resp = await globalThis.fetch(`${BRAPI_BASE}/quote/${tickerStr}`);
    if (!resp.ok) throw new Error(`Brapi HTTP ${resp.status}`);
    const buf = Buffer.from(await resp.arrayBuffer());
    const fp = fingerprint(buf);
    const data = JSON.parse(buf.toString("utf-8")) as R;
    const results = (data["results"] as R[]) ?? [];

    for (const item of results) {
      const symbol = (item["symbol"] as string) ?? "";
      const mapping = B3_COMMODITY_TICKERS[symbol];
      if (!mapping) continue;

      const [commodityName, contentType] = mapping;
      const price = Number(item["regularMarketPrice"] ?? 0);
      const changePct = Number(item["regularMarketChangePercent"] ?? 0);
      const timestamp = (item["regularMarketTime"] as string) ?? new Date().toISOString();

      const futures: CommodityFutures = {
        commodity: commodityName,
        ticker: symbol,
        exchange: "B3",
        unit: "R$/saca",
        contract_month: "",
        price,
        change: Number(item["regularMarketChange"] ?? 0),
        change_pct: changePct,
        open: Number(item["regularMarketOpen"] ?? 0),
        day_high: Number(item["regularMarketDayHigh"] ?? 0),
        day_low: Number(item["regularMarketDayLow"] ?? 0),
        volume: Number(item["regularMarketVolume"] ?? 0),
        timestamp,
      };

      let occurred: string;
      try {
        occurred = new Date(timestamp).toISOString();
      } catch {
        occurred = new Date().toISOString();
      }

      events.push(new CDSEvent({
        content_type: contentType,
        source: { "@id": CDSSources.BRAPI, fingerprint: fp },
        occurred_at: occurred,
        lang: "pt-BR",
        payload: futures as unknown as R,
        context: {
          summary: `${commodityName.charAt(0).toUpperCase() + commodityName.slice(1)} B3 (${symbol}): R$ ${price.toFixed(2)} (${changePct >= 0 ? "+" : ""}${changePct.toFixed(2)}%)`,
          model: "rule-based-v1",
          generated_at: new Date().toISOString(),
        } satisfies ContextMeta,
      }));
    }

    return events;
  }
}
