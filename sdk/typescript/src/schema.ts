/**
 * SignedData CDS — Core Schema
 * TypeScript 5 / ESM.  Issuer: signed-data.org
 */

import { randomUUID } from "node:crypto";

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

export class CDSContentType {
  readonly domain: string;
  readonly schema_name: string;
  readonly version: string;
  readonly encoding: string;

  constructor(opts: CDSContentTypeOptions) {
    this.domain      = opts.domain;
    this.schema_name = opts.schema_name;
    this.version     = opts.version  ?? "1";
    this.encoding    = opts.encoding ?? "json";
  }

  get mime_type(): string {
    const d = this.domain.replace(/\./g, "-");
    const s = this.schema_name.replace(/\./g, "-");
    return `application/vnd.cds.${d}.${s}+${this.encoding};v=${this.version}`;
  }

  toString(): string { return this.mime_type; }

  toJSON(): Record<string, string> {
    return {
      domain:      this.domain,
      schema_name: this.schema_name,
      version:     this.version,
      encoding:    this.encoding,
    };
  }
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

export class CDSEvent {
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

  constructor(opts: CDSEventOptions) {
    this.spec_version = opts.spec_version ?? "0.1.0";
    this.id           = opts.id ?? randomUUID();
    this.content_type = opts.content_type;
    this.source       = opts.source;
    this.occurred_at  = opts.occurred_at instanceof Date
      ? opts.occurred_at.toISOString()
      : opts.occurred_at;
    this.ingested_at  = new Date().toISOString();
    this.lang         = opts.lang ?? "en";
    this.payload      = opts.payload;
    this.context      = opts.context;
    this.integrity    = opts.integrity;
  }

  get domain(): string      { return this.content_type.domain; }
  get event_type(): string  { return this.content_type.schema_name; }

  canonicalBytes(): Buffer {
    const { integrity: _i, ingested_at: _ia, ...rest } = this.toJSON();
    const sorted = Object.fromEntries(
      Object.entries(rest).sort(([a], [b]) => a.localeCompare(b))
    );
    return Buffer.from(JSON.stringify(sorted), "utf-8");
  }

  toJSON(): Record<string, unknown> {
    return {
      spec_version: this.spec_version,
      id:           this.id,
      content_type: this.content_type.toJSON(),
      source:       this.source,
      occurred_at:  this.occurred_at,
      ingested_at:  this.ingested_at,
      lang:         this.lang,
      payload:      this.payload,
      ...(this.context   && { context:   this.context }),
      ...(this.integrity && { integrity: this.integrity }),
    };
  }

  static fromJSON(data: Record<string, unknown>): CDSEvent {
    const ct = data["content_type"] as Record<string, string>;
    return new CDSEvent({
      ...(data as unknown as CDSEventOptions),
      content_type: new CDSContentType({
        domain:      ct["domain"]!,
        schema_name: ct["schema_name"]!,
        version:     ct["version"],
        encoding:    ct["encoding"],
      }),
    });
  }
}
