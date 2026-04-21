/**
 * SignedData CDS — Lottery Source
 */

import { CDSEvent } from "../schema.js";
import { BaseIngestor } from "../ingestor.js";
import { CDSVocab } from "../vocab.js";

export const LotteryContentTypes = {
  MEGA_SENA: CDSVocab.LOTTERY_MEGA_SENA,
  LOTOFACIL: CDSVocab.LOTTERY_LOTOFACIL,
  QUINA: CDSVocab.LOTTERY_QUINA,
  LOTOMANIA: CDSVocab.LOTTERY_LOTOMANIA,
  DUPLA_SENA: CDSVocab.LOTTERY_DUPLA_SENA,
} as const;

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

export class MegaSenaIngestor extends BaseIngestor {
  readonly contentType = LotteryContentTypes.MEGA_SENA;

  async fetch(): Promise<CDSEvent[]> {
    return [];
  }
}
