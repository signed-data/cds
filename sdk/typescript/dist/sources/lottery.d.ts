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
import { CDSEvent } from "../schema.js";
import { CDSSigner } from "../signer.js";
import { BaseIngestor } from "../ingestor.js";
export declare const LotteryContentTypes: {
    readonly MEGA_SENA: string;
    readonly LOTOFACIL: string;
    readonly QUINA: string;
    readonly LOTOMANIA: string;
    readonly DUPLA_SENA: string;
};
export interface PrizeTier {
    tier: number;
    description: string;
    winners: number;
    prize_amount: number;
    total_prize: number;
}
export interface MegaSenaResult {
    concurso: number;
    data_apuracao: string;
    data_apuracao_iso: string;
    local_sorteio: string;
    cidade_uf: string;
    dezenas: string[];
    dezenas_ordem_sorteio: string[];
    acumulado: boolean;
    premiacoes: PrizeTier[];
    valor_arrecadado: number;
    valor_acumulado_proximo: number;
    data_proximo_concurso: string;
    concurso_anterior?: number;
    concurso_proximo?: number;
}
export interface MegaSenaIngestorOptions {
    /** Specific draw numbers to fetch. Omit to fetch only the latest. */
    concursos?: number[];
}
export declare class MegaSenaIngestor extends BaseIngestor {
    readonly contentType: string;
    private readonly concursos;
    constructor(signer: CDSSigner, opts?: MegaSenaIngestorOptions);
    fetch(): Promise<CDSEvent[]>;
}
//# sourceMappingURL=lottery.d.ts.map