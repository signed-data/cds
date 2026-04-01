/**
 * SignedData CDS — Brazil Lottery Source
 * Source: Caixa Econômica Federal public API (no auth required)
 *
 * Endpoints:
 *   Latest:   GET /portaldeloterias/api/megasena/
 *   Specific: GET /portaldeloterias/api/megasena/{concurso}
 *
 * Other games:
 *   /portaldeloterias/api/lotofacil/{concurso}
 *   /portaldeloterias/api/quina/{concurso}
 *   /portaldeloterias/api/lotomania/{concurso}
 */

import { createHash } from "node:crypto";
import { CDSContentType, CDSEvent, ContextMeta, SourceMeta } from "../schema.js";
import { CDSSigner } from "../signer.js";
import { BaseIngestor } from "../ingestor.js";

// ── Content Types ──────────────────────────────────────────

export const LotteryContentTypes = {
  MEGA_SENA:  new CDSContentType({ domain: "lottery.brazil", schema_name: "mega-sena.result"  }),
  LOTOFACIL:  new CDSContentType({ domain: "lottery.brazil", schema_name: "lotofacil.result"  }),
  QUINA:      new CDSContentType({ domain: "lottery.brazil", schema_name: "quina.result"       }),
  LOTOMANIA:  new CDSContentType({ domain: "lottery.brazil", schema_name: "lotomania.result"   }),
  TIMEMANIA:  new CDSContentType({ domain: "lottery.brazil", schema_name: "timemania.result"   }),
  DUPLA_SENA: new CDSContentType({ domain: "lottery.brazil", schema_name: "dupla-sena.result"  }),
} as const;

// ── Payload Types ──────────────────────────────────────────

export interface PrizeTier {
  tier: number;
  description: string;
  winners: number;
  prize_amount: number;   // BRL per winner
  total_prize: number;    // winners * prize_amount
}

export interface MegaSenaResult {
  concurso: number;
  data_apuracao: string;          // "29/03/2026"
  data_apuracao_iso: string;      // "2026-03-29"
  local_sorteio: string;
  cidade_uf: string;
  dezenas: string[];              // sorted: ["04","12","25","36","47","59"]
  dezenas_ordem_sorteio: string[];// draw order
  acumulado: boolean;
  premiacoes: PrizeTier[];
  valor_arrecadado: number;
  valor_acumulado_proximo: number;
  data_proximo_concurso: string;
  concurso_anterior?: number;
  concurso_proximo?: number;
}

// ── Helpers ────────────────────────────────────────────────

const CAIXA_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api";
const SOURCE_ID  = "caixa.gov.br.loterias.v1";

type R = Record<string, unknown>;

function parseDateIso(brDate: string): string {
  const [d, m, y] = brDate.split("/");
  return d && m && y ? `${y}-${m}-${d}` : brDate;
}

function brl(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency", currency: "BRL", minimumFractionDigits: 2,
  }).format(value);
}

function parsePremiacao(raw: R[]): PrizeTier[] {
  return raw.map((item, i) => {
    const winners = Number(item["numeroDeGanhadores"] ?? 0);
    const prize   = Number(item["valorPremio"] ?? 0);
    return {
      tier:        i + 1,
      description: (item["descricao"] as string) ?? `Faixa ${i + 1}`,
      winners,
      prize_amount: prize,
      total_prize:  winners * prize,
    };
  });
}

function buildSummary(r: MegaSenaResult): string {
  const dezenas = r.dezenas.join(" · ");
  if (r.acumulado) {
    return (
      `Mega Sena concurso ${r.concurso} (${r.data_apuracao}): ` +
      `ACUMULOU — dezenas: ${dezenas}. ` +
      `Próximo prêmio estimado: ${brl(r.valor_acumulado_proximo)} em ${r.data_proximo_concurso}.`
    );
  }
  const tier1   = r.premiacoes.find(t => t.tier === 1);
  const winners = tier1?.winners ?? 0;
  const prize   = tier1?.prize_amount ?? 0;
  const plural  = winners === 1 ? "ganhador" : "ganhadores";
  return (
    `Mega Sena concurso ${r.concurso} (${r.data_apuracao}): ` +
    `dezenas: ${dezenas}. ` +
    `${winners} ${plural} da sena, prêmio de ${brl(prize)} cada.`
  );
}

function parseResponse(raw: R): MegaSenaResult {
  const brDate  = (raw["dataApuracao"] as string) ?? "";
  const dezenas = ((raw["listaDezenas"] as string[]) ?? []).slice().sort();

  return {
    concurso:               Number(raw["numero"]   ?? 0),
    data_apuracao:          brDate,
    data_apuracao_iso:      parseDateIso(brDate),
    local_sorteio:          (raw["localSorteio"] as string)           ?? "",
    cidade_uf:              (raw["nomeMunicipiUFSorteio"] as string)  ?? "",
    dezenas,
    dezenas_ordem_sorteio:  (raw["listaDezenasOrdemSorteio"] as string[]) ?? [],
    acumulado:              Boolean(raw["acumulado"] ?? false),
    premiacoes:             parsePremiacao((raw["listaRateioPremio"] as R[]) ?? []),
    valor_arrecadado:       Number(raw["valorArrecadado"]                 ?? 0),
    valor_acumulado_proximo:Number(raw["valorEstimadoProximoConcurso"]   ?? 0),
    data_proximo_concurso:  (raw["dataProximoConcurso"] as string)        ?? "",
    concurso_anterior:      raw["numeroConcursoAnterior"] as number | undefined,
    concurso_proximo:       raw["numeroConcursoProximo"]  as number | undefined,
  };
}

// ── Ingestor ───────────────────────────────────────────────

export interface MegaSenaIngestorOptions {
  /** Specific draw numbers to fetch. Omit to fetch only the latest. */
  concursos?: number[];
}

export class MegaSenaIngestor extends BaseIngestor {
  readonly contentType = LotteryContentTypes.MEGA_SENA;
  private readonly concursos: number[] | undefined;

  constructor(signer: CDSSigner, opts: MegaSenaIngestorOptions = {}) {
    super(signer);
    this.concursos = opts.concursos;
  }

  async fetch(): Promise<CDSEvent[]> {
    const targets = this.concursos?.length ? this.concursos : [undefined];
    const events: CDSEvent[] = [];

    for (const concurso of targets) {
      const url = concurso
        ? `${CAIXA_BASE}/megasena/${concurso}`
        : `${CAIXA_BASE}/megasena/`;

      const resp = await globalThis.fetch(url, {
        headers: { "Accept": "application/json" },
        redirect: "follow",
      });
      if (!resp.ok) throw new Error(`Caixa API HTTP ${resp.status} for concurso ${concurso}`);

      const buf    = Buffer.from(await resp.arrayBuffer());
      const fp     = "sha256:" + createHash("sha256").update(buf).digest("hex");
      const raw    = JSON.parse(buf.toString("utf-8")) as R;
      const result = parseResponse(raw);

      // occurred_at = draw date at 21:00 BRT (UTC−03:00), which is 00:00 UTC the next day
      let occurred: string;
      try {
        const [d, m, y] = result.data_apuracao.split("/");
        occurred = new Date(`${y}-${m}-${d}T21:00:00-03:00`).toISOString();
      } catch {
        occurred = new Date().toISOString();
      }

      events.push(new CDSEvent({
        content_type: LotteryContentTypes.MEGA_SENA,
        source:       { id: SOURCE_ID, fingerprint: fp } satisfies SourceMeta,
        occurred_at:  occurred,
        lang:         "pt-BR",
        payload:      result as unknown as Record<string, unknown>,
        context: {
          summary:      buildSummary(result),
          model:        "rule-based-v1",
          generated_at: new Date().toISOString(),
        } satisfies ContextMeta,
      }));
    }

    return events;
  }
}
