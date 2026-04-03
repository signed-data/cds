/**
 * CDS TypeScript SDK — Core Schema v0.2.0
 */
import { randomUUID } from "node:crypto";
import { CDS_CONTEXT_URI, CDS_EVENT_TYPE_URI, eventUri } from "./vocab.js";

export interface SourceMeta {
  "@id":        string;   // URI — use CDSSources constants
  fingerprint?: string;
}

export interface ContextMeta {
  summary:       string;
  model:         string;
  generated_at:  string;
}

export interface IntegrityMeta {
  hash:      string;   // "sha256:<hex>"
  signature: string;   // base64 RSA-PSS
  signed_by: string;   // URI — "https://signed-data.org"
}

export interface CDSEventOptions {
  content_type:  string;           // URI — use CDSVocab constants
  source:        SourceMeta;
  occurred_at:   Date | string;
  payload:       Record<string, unknown>;
  lang?:         string;
  context?:      ContextMeta;
  integrity?:    IntegrityMeta;
  id?:           string;
  spec_version?: string;
}

export class CDSEvent {
  readonly ["@context"]: string;
  readonly ["@type"]:    string;
  readonly ["@id"]:      string;
  readonly spec_version: string;
  readonly id:           string;
  readonly content_type: string;
  readonly source:       SourceMeta;
  readonly occurred_at:  string;
  readonly ingested_at:  string;
  readonly lang:         string;
  readonly payload:      Record<string, unknown>;
  readonly context?:     ContextMeta;
  integrity?:            IntegrityMeta;

  constructor(opts: CDSEventOptions) {
    const id           = opts.id ?? randomUUID();
    this["@context"]   = CDS_CONTEXT_URI;
    this["@type"]      = CDS_EVENT_TYPE_URI;
    this["@id"]        = eventUri(id);
    this.spec_version  = opts.spec_version ?? "0.2.0";
    this.id            = id;
    this.content_type  = opts.content_type;
    this.source        = opts.source;
    this.occurred_at   = opts.occurred_at instanceof Date
      ? opts.occurred_at.toISOString()
      : opts.occurred_at;
    this.ingested_at   = new Date().toISOString();
    this.lang          = opts.lang ?? "en";
    this.payload       = opts.payload;
    this.context       = opts.context;
    this.integrity     = opts.integrity;
  }

  get domain(): string {
    try {
      const seg = this.content_type.split("/vocab/")[1] ?? "";
      return (seg.split("/")[0] ?? "").replace(/-/g, ".");
    } catch { return ""; }
  }

  get event_type(): string {
    try {
      const seg   = this.content_type.split("/vocab/")[1] ?? "";
      const parts = seg.split("/");
      const slug  = parts[1] ?? "";
      // Reverse the LAST hyphen to a dot (the original schema_name separator)
      const idx = slug.lastIndexOf("-");
      if (idx >= 0) return slug.slice(0, idx) + "." + slug.slice(idx + 1);
      return slug;
    } catch { return ""; }
  }

  toJSON(): Record<string, unknown> {
    return {
      "@context":   this["@context"],
      "@type":      this["@type"],
      "@id":        this["@id"],
      spec_version: this.spec_version,
      id:           this.id,
      content_type: this.content_type,
      source:       this.source,
      occurred_at:  this.occurred_at,
      ingested_at:  this.ingested_at,
      lang:         this.lang,
      payload:      this.payload,
      ...(this.context   ? { context:   this.context   } : {}),
      ...(this.integrity ? { integrity: this.integrity } : {}),
    };
  }

  canonicalBytes(): Buffer {
    const { integrity: _i, ingested_at: _ia, ...rest } = this.toJSON();
    const sorted = Object.fromEntries(
      Object.entries(rest).sort(([a], [b]) => a.localeCompare(b))
    );
    return Buffer.from(JSON.stringify(sorted), "utf-8");
  }

  static fromJSON(data: Record<string, unknown>): CDSEvent {
    return new CDSEvent({
      id:           data["id"]           as string,
      content_type: data["content_type"] as string,
      source:       data["source"]       as SourceMeta,
      occurred_at:  data["occurred_at"]  as string,
      lang:         data["lang"]         as string | undefined,
      payload:      data["payload"]      as Record<string, unknown>,
      context:      data["context"]      as ContextMeta | undefined,
      integrity:    data["integrity"]    as IntegrityMeta | undefined,
    });
  }
}
