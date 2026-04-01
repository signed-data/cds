export class BaseIngestor {
    signer;
    constructor(signer) {
        this.signer = signer;
    }
    async ingest() {
        return (await this.fetch()).map(e => this.signer.sign(e));
    }
}
//# sourceMappingURL=ingestor.js.map