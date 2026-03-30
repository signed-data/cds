/**
 * SignedData CDS — Base Ingestor
 */
import { CDSContentType, CDSEvent } from "./schema.js";
import { CDSSigner } from "./signer.js";

export abstract class BaseIngestor {
  abstract readonly contentType: CDSContentType;
  constructor(protected readonly signer: CDSSigner) {}
  abstract fetch(): Promise<CDSEvent[]>;
  async ingest(): Promise<CDSEvent[]> {
    return (await this.fetch()).map(e => this.signer.sign(e));
  }
}
