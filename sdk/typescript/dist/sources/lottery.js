/**
 * SignedData CDS — Lottery Source
 */
import { BaseIngestor } from "../ingestor.js";
import { CDSVocab } from "../vocab.js";
export const LotteryContentTypes = {
    MEGA_SENA: CDSVocab.LOTTERY_MEGA_SENA,
    LOTOFACIL: CDSVocab.LOTTERY_LOTOFACIL,
    QUINA: CDSVocab.LOTTERY_QUINA,
    LOTOMANIA: CDSVocab.LOTTERY_LOTOMANIA,
    DUPLA_SENA: CDSVocab.LOTTERY_DUPLA_SENA,
};
export class MegaSenaIngestor extends BaseIngestor {
    contentType = LotteryContentTypes.MEGA_SENA;
    async fetch() {
        return [];
    }
}
//# sourceMappingURL=lottery.js.map