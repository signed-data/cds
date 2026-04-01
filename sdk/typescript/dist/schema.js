/**
 * SignedData CDS — Core Schema
 * TypeScript 5 / ESM.  Issuer: signed-data.org
 */
import { randomUUID } from "node:crypto";
export class CDSContentType {
    domain;
    schema_name;
    version;
    encoding;
    constructor(opts) {
        this.domain = opts.domain;
        this.schema_name = opts.schema_name;
        this.version = opts.version ?? "1";
        this.encoding = opts.encoding ?? "json";
    }
    get mime_type() {
        const d = this.domain.replace(/\./g, "-");
        const s = this.schema_name.replace(/\./g, "-");
        return `application/vnd.cds.${d}.${s}+${this.encoding};v=${this.version}`;
    }
    toString() { return this.mime_type; }
    toJSON() {
        return {
            domain: this.domain,
            schema_name: this.schema_name,
            version: this.version,
            encoding: this.encoding,
        };
    }
}
export class CDSEvent {
    spec_version;
    id;
    content_type;
    source;
    occurred_at;
    ingested_at;
    lang;
    payload;
    context;
    integrity;
    constructor(opts) {
        this.spec_version = opts.spec_version ?? "0.1.0";
        this.id = opts.id ?? randomUUID();
        this.content_type = opts.content_type;
        this.source = opts.source;
        this.occurred_at = opts.occurred_at instanceof Date
            ? opts.occurred_at.toISOString()
            : opts.occurred_at;
        this.ingested_at = new Date().toISOString();
        this.lang = opts.lang ?? "en";
        this.payload = opts.payload;
        this.context = opts.context;
        this.integrity = opts.integrity;
    }
    get domain() { return this.content_type.domain; }
    get event_type() { return this.content_type.schema_name; }
    canonicalBytes() {
        const { integrity: _i, ingested_at: _ia, ...rest } = this.toJSON();
        const sorted = Object.fromEntries(Object.entries(rest).sort(([a], [b]) => a.localeCompare(b)));
        return Buffer.from(JSON.stringify(sorted), "utf-8");
    }
    toJSON() {
        return {
            spec_version: this.spec_version,
            id: this.id,
            content_type: this.content_type.toJSON(),
            source: this.source,
            occurred_at: this.occurred_at,
            ingested_at: this.ingested_at,
            lang: this.lang,
            payload: this.payload,
            ...(this.context && { context: this.context }),
            ...(this.integrity && { integrity: this.integrity }),
        };
    }
    static fromJSON(data) {
        const ct = data["content_type"];
        return new CDSEvent({
            ...data,
            content_type: new CDSContentType({
                domain: ct["domain"],
                schema_name: ct["schema_name"],
                version: ct["version"],
                encoding: ct["encoding"],
            }),
        });
    }
}
//# sourceMappingURL=schema.js.map