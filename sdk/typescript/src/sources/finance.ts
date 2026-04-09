/**
 * SignedData CDS — Finance Brazil Source
 * Sources:
 *   BCB SGS API: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/{n}
 *   Brapi:       https://brapi.dev/api/quote/{tickers}
 */

import { createHash } from "node:crypto";
import { CDSEvent, ContextMeta, SourceMeta } from "../schema.js";
import { CDSSigner } from "../signer.js";
import { BaseIngestor } from "../ingestor.js";
import { CDSVocab, CDSSources } from "../vocab.js";

// ── Content Types ──────────────────────────────────────────

export const FinanceContentTypes = {
  SELIC:    CDSVocab.FINANCE_SELIC_RATE,
  CDI:      CDSVocab.FINANCE_CDI_RATE,
  IPCA:     CDSVocab.FINANCE_IPCA_INDEX,
  IGPM:     CDSVocab.FINANCE_IGPM_INDEX,
  USD_BRL:  CDSVocab.FINANCE_FX_USD_BRL,
  EUR_BRL:  CDSVocab.FINANCE_FX_EUR_BRL,
  STOCK:    CDSVocab.FINANCE_QUOTE_STOCK,
  FII:      CDSVocab.FINANCE_QUOTE_FII,
  CRYPTO:   CDSVocab.FINANCE_QUOTE_CRYPTO,
  COPOM:    CDSVocab.FINANCE_DECISION_COPOM,
} as const;

// ── Payload Types ──────────────────────────────────────────

export interface SELICRate {
  date: string;
  rate_annual: number;
  rate_daily: number;
  unit: string;
  effective_date: string;
}

export interface CDIRate {
  date: string;
  rate_annual: number;
  rate_daily: number;
  unit: string;
}

export interface IPCAIndex {
  date: string;
  monthly_pct: number;
  accumulated_12m: number;
  accumulated_year: number;
  base_year: number;
}

export interface IGPMIndex {
  date: string;
  monthly_pct: number;
}

export interface FXRate {
  date: string;
  buy: number;
  sell: number;
  mid: number;
  currency_from: string;
  currency_to: string;
  source: string;
}

export interface StockQuote {
  ticker: string;
  short_name: string;
  long_name: string;
  currency: string;
  market_price: number;
  change: number;
  change_pct: number;
  previous_close: number;
  open?: number;
  day_high: number;
  day_low: number;
  volume: number;
  market_cap?: number;
  exchange: string;
  market_state: string;
  timestamp: string;
}

export interface CopomDecision {
  meeting_number: number;
  meeting_date: string;
  decision: "raise" | "cut" | "maintain";
  rate_before: number;
  rate_after: number;
  rate_change_bps: number;
  vote_unanimous: boolean;
  statement_url?: string;
}

// ── Helpers ────────────────────────────────────────────────

const BCB_SGS_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/{n}";
const BRAPI_BASE = "https://brapi.dev/api";

type R = Record<string, unknown>;

function bcbUrl(seriesCode: number, lastN: number = 1): string {
  return BCB_SGS_BASE.replace("{code}", String(seriesCode)).replace("{n}", String(lastN));
}

function parseBcbDate(raw: string): string {
  const [d, m, y] = raw.split("/");
  return d && m && y ? `${y}-${m}-${d}` : raw;
}

function dailyRate(annualPct: number): number {
  return ((1 + annualPct / 100) ** (1 / 252) - 1) * 100;
}

function fingerprint(data: Buffer): string {
  return "sha256:" + createHash("sha256").update(data).digest("hex");
}

// ── BCB Rates Ingestor ─────────────────────────────────────

export class BCBRatesIngestor extends BaseIngestor {
  readonly contentType = FinanceContentTypes.SELIC;
  private readonly lastN: number;

  constructor(signer: CDSSigner, lastN: number = 1) {
    super(signer);
    this.lastN = lastN;
  }

  async fetch(): Promise<CDSEvent[]> {
    const events: CDSEvent[] = [];

    // SELIC
    const selicResp = await globalThis.fetch(bcbUrl(11, this.lastN));
    if (!selicResp.ok) throw new Error(`BCB SGS HTTP ${selicResp.status}`);
    const selicBuf = Buffer.from(await selicResp.arrayBuffer());
    const selicFp = fingerprint(selicBuf);
    const selicData = JSON.parse(selicBuf.toString("utf-8")) as R[];

    for (const item of selicData) {
      const dateIso = parseBcbDate(item["data"] as string);
      const annual = Number(item["valor"]);
      const rate: SELICRate = {
        date: dateIso,
        rate_annual: annual,
        rate_daily: Math.round(dailyRate(annual) * 1e6) / 1e6,
        unit: "% a.a.",
        effective_date: dateIso,
      };
      events.push(new CDSEvent({
        content_type: FinanceContentTypes.SELIC,
        source: { "@id": CDSSources.BCB_API, fingerprint: selicFp },
        occurred_at: `${dateIso}T18:30:00-03:00`,
        lang: "pt-BR",
        payload: rate as unknown as R,
        context: {
          summary: `SELIC: ${rate.rate_annual}% a.a. (${rate.date})`,
          model: "rule-based-v1",
          generated_at: new Date().toISOString(),
        } satisfies ContextMeta,
      }));
    }

    // CDI
    const cdiResp = await globalThis.fetch(bcbUrl(4391, this.lastN));
    if (!cdiResp.ok) throw new Error(`BCB SGS HTTP ${cdiResp.status}`);
    const cdiBuf = Buffer.from(await cdiResp.arrayBuffer());
    const cdiFp = fingerprint(cdiBuf);
    const cdiData = JSON.parse(cdiBuf.toString("utf-8")) as R[];

    for (const item of cdiData) {
      const dateIso = parseBcbDate(item["data"] as string);
      const annual = Number(item["valor"]);
      const rate: CDIRate = {
        date: dateIso,
        rate_annual: annual,
        rate_daily: Math.round(dailyRate(annual) * 1e6) / 1e6,
        unit: "% a.a.",
      };
      events.push(new CDSEvent({
        content_type: FinanceContentTypes.CDI,
        source: { "@id": CDSSources.BCB_API, fingerprint: cdiFp },
        occurred_at: `${dateIso}T18:30:00-03:00`,
        lang: "pt-BR",
        payload: rate as unknown as R,
        context: {
          summary: `CDI: ${rate.rate_annual}% a.a. (${rate.date})`,
          model: "rule-based-v1",
          generated_at: new Date().toISOString(),
        } satisfies ContextMeta,
      }));
    }

    return events;
  }
}

// ── Brapi Quotes Ingestor ──────────────────────────────────

export interface BrapiQuotesOptions {
  tickers?: string[];
}

export class BrapiQuotesIngestor extends BaseIngestor {
  readonly contentType = FinanceContentTypes.STOCK;
  private readonly tickers: string[];

  constructor(signer: CDSSigner, opts: BrapiQuotesOptions = {}) {
    super(signer);
    this.tickers = opts.tickers ?? ["PETR4", "VALE3", "ITUB4"];
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
      const ticker = (item["symbol"] as string) ?? "";
      const quote: StockQuote = {
        ticker,
        short_name: (item["shortName"] as string) ?? "",
        long_name: (item["longName"] as string) ?? "",
        currency: (item["currency"] as string) ?? "BRL",
        market_price: Number(item["regularMarketPrice"] ?? 0),
        change: Number(item["regularMarketChange"] ?? 0),
        change_pct: Number(item["regularMarketChangePercent"] ?? 0),
        previous_close: Number(item["regularMarketPreviousClose"] ?? 0),
        open: item["regularMarketOpen"] as number | undefined,
        day_high: Number(item["regularMarketDayHigh"] ?? 0),
        day_low: Number(item["regularMarketDayLow"] ?? 0),
        volume: Number(item["regularMarketVolume"] ?? 0),
        market_cap: item["marketCap"] as number | undefined,
        exchange: (item["fullExchangeName"] as string) ?? "SAO",
        market_state: (item["marketState"] as string) ?? "CLOSED",
        timestamp: (item["regularMarketTime"] as string) ?? new Date().toISOString(),
      };

      const ct = ticker.endsWith("11") && ticker.length === 6
        ? FinanceContentTypes.FII
        : FinanceContentTypes.STOCK;

      let occurred: string;
      try {
        occurred = new Date(quote.timestamp).toISOString();
      } catch {
        occurred = new Date().toISOString();
      }

      events.push(new CDSEvent({
        content_type: ct,
        source: { "@id": CDSSources.BRAPI, fingerprint: fp },
        occurred_at: occurred,
        lang: "pt-BR",
        payload: quote as unknown as R,
        context: {
          summary: `${quote.ticker}: R$ ${quote.market_price.toFixed(2)} (${quote.change_pct >= 0 ? "+" : ""}${quote.change_pct.toFixed(2)}%) — ${quote.market_state}`,
          model: "rule-based-v1",
          generated_at: new Date().toISOString(),
        } satisfies ContextMeta,
      }));
    }

    return events;
  }
}
