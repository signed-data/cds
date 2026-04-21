export interface SourceMeta {
    "@id": string;
    fingerprint?: string;
}
export interface ContextMeta {
    summary: string;
    model: string;
    generated_at: string;
}
export interface IntegrityMeta {
    hash: string;
    signature: string;
    signed_by: string;
}
export interface CDSEventOptions {
    content_type: string;
    source: SourceMeta;
    occurred_at: Date | string;
    payload: Record<string, unknown>;
    lang?: string;
    context?: ContextMeta;
    integrity?: IntegrityMeta;
    id?: string;
    spec_version?: string;
}
export declare class CDSEvent {
    readonly ["@context"]: string;
    readonly ["@type"]: string;
    readonly ["@id"]: string;
    readonly spec_version: string;
    readonly id: string;
    readonly content_type: string;
    readonly source: SourceMeta;
    readonly occurred_at: string;
    readonly ingested_at: string;
    readonly lang: string;
    readonly payload: Record<string, unknown>;
    readonly context?: ContextMeta;
    integrity?: IntegrityMeta;
    constructor(opts: CDSEventOptions);
    get domain(): string;
    get event_type(): string;
    toJSON(): Record<string, unknown>;
    canonicalBytes(): Buffer;
    static fromJSON(data: Record<string, unknown>): CDSEvent;
}
//# sourceMappingURL=schema.d.ts.map