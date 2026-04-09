/**
 * SignedData CDS — Core Schema
 * TypeScript 5 / ESM.  Issuer: signed-data.org
 */
export interface SourceMeta {
    id: string;
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
export interface CDSContentTypeOptions {
    domain: string;
    schema_name: string;
    version?: string;
    encoding?: string;
}
export declare class CDSContentType {
    readonly domain: string;
    readonly schema_name: string;
    readonly version: string;
    readonly encoding: string;
    constructor(opts: CDSContentTypeOptions);
    get mime_type(): string;
    toString(): string;
    toJSON(): Record<string, string>;
}
export interface CDSEventOptions {
    content_type: CDSContentType;
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
    readonly spec_version: string;
    readonly id: string;
    readonly content_type: CDSContentType;
    readonly source: SourceMeta;
    readonly occurred_at: string;
    readonly ingested_at: string;
    readonly lang: string;
    readonly payload: Record<string, unknown>;
    context?: ContextMeta;
    integrity?: IntegrityMeta;
    constructor(opts: CDSEventOptions);
    get domain(): string;
    get event_type(): string;
    canonicalBytes(): Buffer;
    toJSON(): Record<string, unknown>;
    static fromJSON(data: Record<string, unknown>): CDSEvent;
}
//# sourceMappingURL=schema.d.ts.map