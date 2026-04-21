/**
 * CDS TypeScript SDK — Core Schema v0.2.0
 */
import { randomUUID } from "node:crypto";
import { CDS_CONTEXT_URI, CDS_EVENT_TYPE_URI, eventUri } from "./vocab.js";
export class CDSEvent {
    ["@context"];
    ["@type"];
    ["@id"];
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
        const id = opts.id ?? randomUUID();
        this["@context"] = CDS_CONTEXT_URI;
        this["@type"] = CDS_EVENT_TYPE_URI;
        this["@id"] = eventUri(id);
        this.spec_version = opts.spec_version ?? "0.2.0";
        this.id = id;
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
    get domain() {
        try {
            const seg = this.content_type.split("/vocab/")[1] ?? "";
            return (seg.split("/")[0] ?? "").replace(/-/g, ".");
        }
        catch {
            return "";
        }
    }
    get event_type() {
        try {
            const seg = this.content_type.split("/vocab/")[1] ?? "";
            const parts = seg.split("/");
            const slug = parts[1] ?? "";
            // Reverse the LAST hyphen to a dot (the original schema_name separator)
            const idx = slug.lastIndexOf("-");
            if (idx >= 0)
                return slug.slice(0, idx) + "." + slug.slice(idx + 1);
            return slug;
        }
        catch {
            return "";
        }
    }
    toJSON() {
        return {
            "@context": this["@context"],
            "@type": this["@type"],
            "@id": this["@id"],
            spec_version: this.spec_version,
            id: this.id,
            content_type: this.content_type,
            source: this.source,
            occurred_at: this.occurred_at,
            ingested_at: this.ingested_at,
            lang: this.lang,
            payload: this.payload,
            ...(this.context ? { context: this.context } : {}),
            ...(this.integrity ? { integrity: this.integrity } : {}),
        };
    }
    canonicalBytes() {
        const { integrity: _i, ingested_at: _ia, ...rest } = this.toJSON();
        const sorted = Object.fromEntries(Object.entries(rest).sort(([a], [b]) => a.localeCompare(b)));
        return Buffer.from(JSON.stringify(sorted), "utf-8");
    }
    static fromJSON(data) {
        return new CDSEvent({
            id: data["id"],
            content_type: data["content_type"],
            source: data["source"],
            occurred_at: data["occurred_at"],
            lang: data["lang"],
            payload: data["payload"],
            context: data["context"],
            integrity: data["integrity"],
        });
    }
}
//# sourceMappingURL=schema.js.map