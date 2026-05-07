/**
 * SignedData CDS — Base Ingestor
 */
import type { CDSEvent } from "./schema.js";
import type { CDSSigner } from "./signer.js";

export abstract class BaseIngestor {
  abstract readonly contentType: string;  // URI — use CDSVocab constants
  constructor(protected readonly signer: CDSSigner) {}
  abstract fetch(): Promise<CDSEvent[]>;
  async ingest(): Promise<CDSEvent[]> {
    return (await this.fetch()).map(e => this.signer.sign(e));
  }
}
