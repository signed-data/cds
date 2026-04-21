/**
 * SignedData CDS — Lottery Source
 */
import { CDSEvent } from "../schema.js";
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
    game: "mega_sena";
    concurso: number;
    data_apuracao: string;
    dezenas: string[];
    arrecadacao_total: number;
    acumulou: boolean;
    acumulada_prox_concurso: number;
    data_prox_concurso: string;
    premio_estimado_prox_concurso: number;
    premiacoes: PrizeTier[];
}
export declare class MegaSenaIngestor extends BaseIngestor {
    readonly contentType: string;
    fetch(): Promise<CDSEvent[]>;
}
//# sourceMappingURL=lottery.d.ts.map