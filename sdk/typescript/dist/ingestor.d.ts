/**
 * SignedData CDS — Base Ingestor
 */
import { CDSContentType, CDSEvent } from "./schema.js";
import { CDSSigner } from "./signer.js";
export declare abstract class BaseIngestor {
    protected readonly signer: CDSSigner;
    abstract readonly contentType: CDSContentType;
    constructor(signer: CDSSigner);
    abstract fetch(): Promise<CDSEvent[]>;
    ingest(): Promise<CDSEvent[]>;
}
//# sourceMappingURL=ingestor.d.ts.map