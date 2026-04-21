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
import { CDSEvent } from "../schema.js";
import { BaseIngestor } from "../ingestor.js";
import { CDSVocab, CDSSources } from "../vocab.js";
// ── Content Types ──────────────────────────────────────────
export const LotteryContentTypes = {
    MEGA_SENA: CDSVocab.LOTTERY_MEGA_SENA,
    LOTOFACIL: CDSVocab.LOTTERY_LOTOFACIL,
    QUINA: CDSVocab.LOTTERY_QUINA,
    LOTOMANIA: CDSVocab.LOTTERY_LOTOMANIA,
    DUPLA_SENA: CDSVocab.LOTTERY_DUPLA_SENA,
};
// ── Helpers ────────────────────────────────────────────────
const CAIXA_BASE = "https://servicebus2.caixa.gov.br/portaldeloterias/api";
function parseDateIso(brDate) {
    const [d, m, y] = brDate.split("/");
    return d && m && y ? `${y}-${m}-${d}` : brDate;
}
function brl(value) {
    return new Intl.NumberFormat("pt-BR", {
        style: "currency", currency: "BRL", minimumFractionDigits: 2,
    }).format(value);
}
function parsePremiacao(raw) {
    return raw.map((item, i) => {
        const winners = Number(item["numeroDeGanhadores"] ?? 0);
        const prize = Number(item["valorPremio"] ?? 0);
        return {
            tier: i + 1,
            description: item["descricao"] ?? `Faixa ${i + 1}`,
            winners,
            prize_amount: prize,
            total_prize: winners * prize,
        };
    });
}
function buildSummary(r) {
    const dezenas = r.dezenas.join(" · ");
    if (r.acumulado) {
        return (`Mega Sena concurso ${r.concurso} (${r.data_apuracao}): ` +
            `ACUMULOU — dezenas: ${dezenas}. ` +
            `Próximo prêmio estimado: ${brl(r.valor_acumulado_proximo)} em ${r.data_proximo_concurso}.`);
    }
    const tier1 = r.premiacoes.find(t => t.tier === 1);
    const winners = tier1?.winners ?? 0;
    const prize = tier1?.prize_amount ?? 0;
    const plural = winners === 1 ? "ganhador" : "ganhadores";
    return (`Mega Sena concurso ${r.concurso} (${r.data_apuracao}): ` +
        `dezenas: ${dezenas}. ` +
        `${winners} ${plural} da sena, prêmio de ${brl(prize)} cada.`);
}
function parseResponse(raw) {
    const brDate = raw["dataApuracao"] ?? "";
    const dezenas = (raw["listaDezenas"] ?? []).slice().sort();
    return {
        concurso: Number(raw["numero"] ?? 0),
        data_apuracao: brDate,
        data_apuracao_iso: parseDateIso(brDate),
        local_sorteio: raw["localSorteio"] ?? "",
        cidade_uf: raw["nomeMunicipiUFSorteio"] ?? "",
        dezenas,
        dezenas_ordem_sorteio: raw["listaDezenasOrdemSorteio"] ?? [],
        acumulado: Boolean(raw["acumulado"] ?? false),
        premiacoes: parsePremiacao(raw["listaRateioPremio"] ?? []),
        valor_arrecadado: Number(raw["valorArrecadado"] ?? 0),
        valor_acumulado_proximo: Number(raw["valorEstimadoProximoConcurso"] ?? 0),
        data_proximo_concurso: raw["dataProximoConcurso"] ?? "",
        concurso_anterior: raw["numeroConcursoAnterior"],
        concurso_proximo: raw["numeroConcursoProximo"],
    };
}
export class MegaSenaIngestor extends BaseIngestor {
    contentType = LotteryContentTypes.MEGA_SENA;
    concursos;
    constructor(signer, opts = {}) {
        super(signer);
        this.concursos = opts.concursos;
    }
    async fetch() {
        const targets = this.concursos?.length ? this.concursos : [undefined];
        const events = [];
        for (const concurso of targets) {
            const url = concurso
                ? `${CAIXA_BASE}/megasena/${concurso}`
                : `${CAIXA_BASE}/megasena/`;
            const resp = await globalThis.fetch(url, {
                headers: { "Accept": "application/json" },
                redirect: "follow",
            });
            if (!resp.ok)
                throw new Error(`Caixa API HTTP ${resp.status} for concurso ${concurso}`);
            const buf = Buffer.from(await resp.arrayBuffer());
            const fp = "sha256:" + createHash("sha256").update(buf).digest("hex");
            const raw = JSON.parse(buf.toString("utf-8"));
            const result = parseResponse(raw);
            // occurred_at = draw date at 21:00 BRT (00:00 UTC next day ~ 21:00 UTC)
            let occurred;
            try {
                const [d, m, y] = result.data_apuracao.split("/");
                occurred = new Date(`${y}-${m}-${d}T21:00:00-03:00`).toISOString();
            }
            catch {
                occurred = new Date().toISOString();
            }
            events.push(new CDSEvent({
                content_type: LotteryContentTypes.MEGA_SENA,
                source: { "@id": CDSSources.CAIXA_LOTERIAS, fingerprint: fp },
                occurred_at: occurred,
                lang: "pt-BR",
                payload: result,
                context: {
                    summary: buildSummary(result),
                    model: "rule-based-v1",
                    generated_at: new Date().toISOString(),
                },
            }));
        }
        return events;
    }
}
//# sourceMappingURL=lottery.js.map