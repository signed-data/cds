/**
 * SignedData CDS — Companies Brazil Source
 * Source: BrasilAPI — https://brasilapi.com.br/api/cnpj/v1/{cnpj}
 *
 * Query-driven: no scheduled ingestor. Called per CNPJ lookup.
 */

import { createHash } from "node:crypto";
import { CDSEvent, type ContextMeta, SourceMeta } from "../schema.js";
import type { CDSSigner } from "../signer.js";
import { CDSVocab, CDSSources } from "../vocab.js";

// ── Content Types ──────────────────────────────────────────

export const CompaniesContentTypes = {
  PROFILE:  CDSVocab.COMPANIES_PROFILE_CNPJ,
  PARTNERS: CDSVocab.COMPANIES_PARTNERS_CNPJ,
  CNAE:     CDSVocab.COMPANIES_CNAE_PROFILE,
} as const;

// ── Payload Types ──────────────────────────────────────────

export interface CNAECode {
  code: string;
  description: string;
}

export interface CompanyAddress {
  street: string;
  number: string;
  complement?: string;
  neighborhood: string;
  zip_code: string;
  city: string;
  state: string;
}

export interface CompanyProfile {
  cnpj: string;
  cnpj_formatted: string;
  company_name: string;
  trade_name?: string;
  registration_status: "ATIVA" | "BAIXADA" | "INAPTA" | "SUSPENSA" | "NULA";
  registration_date: string;
  registration_status_date?: string;
  legal_nature_code: string;
  legal_nature: string;
  size: string;
  share_capital?: number;
  main_cnae: CNAECode;
  secondary_cnaes: CNAECode[];
  address: CompanyAddress;
  phone?: string;
  email?: string;
  query_timestamp: string;
}

export interface CompanyPartner {
  name: string;
  qualifier: string;
  qualifier_code: number;
  entry_date?: string;
  country?: string;
  legal_representative?: string;
}

export interface CompanyPartners {
  cnpj: string;
  company_name: string;
  partners: CompanyPartner[];
  query_timestamp: string;
}

// ── CNPJ Validation ────────────────────────────────────────

export function validateCnpj(cnpj: string): string {
  const bare = cnpj.replace(/[.\-/]/g, "");
  if (bare.length !== 14 || !/^\d+$/.test(bare)) {
    throw new Error(`CNPJ must have 14 digits, got: ${cnpj}`);
  }
  if (new Set(bare).size === 1) {
    throw new Error(`Invalid CNPJ (all same digits): ${cnpj}`);
  }

  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  let total = 0;
  for (let i = 0; i < 12; i++) total += Number(bare[i]) * weights1[i];
  let remainder = total % 11;
  const d1 = remainder < 2 ? 0 : 11 - remainder;
  if (Number(bare[12]) !== d1) {
    throw new Error(`Invalid CNPJ check digit 1: ${cnpj}`);
  }

  const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  total = 0;
  for (let i = 0; i < 13; i++) total += Number(bare[i]) * weights2[i];
  remainder = total % 11;
  const d2 = remainder < 2 ? 0 : 11 - remainder;
  if (Number(bare[13]) !== d2) {
    throw new Error(`Invalid CNPJ check digit 2: ${cnpj}`);
  }

  return bare;
}

export function formatCnpj(bare: string): string {
  return `${bare.slice(0, 2)}.${bare.slice(2, 5)}.${bare.slice(5, 8)}/${bare.slice(8, 12)}-${bare.slice(12, 14)}`;
}

// ── Helpers ────────────────────────────────────────────────

const BRASILAPI_CNPJ_BASE = "https://brasilapi.com.br/api/cnpj/v1";

type R = Record<string, unknown>;

function fingerprint(data: Buffer): string {
  return "sha256:" + createHash("sha256").update(data).digest("hex");
}

// ── Fetcher ────────────────────────────────────────────────

export class CNPJFetcher {
  constructor(private readonly signer?: CDSSigner) {}

  async fetchProfile(cnpj: string): Promise<CDSEvent> {
    const bare = validateCnpj(cnpj);
    const queryTs = new Date().toISOString();

    const resp = await globalThis.fetch(`${BRASILAPI_CNPJ_BASE}/${bare}`);
    if (!resp.ok) throw new Error(`BrasilAPI HTTP ${resp.status}`);
    const buf = Buffer.from(await resp.arrayBuffer());
    const fp = fingerprint(buf);
    const raw = JSON.parse(buf.toString("utf-8")) as R;

    const cnpjBare = String(raw["cnpj"] ?? "").padStart(14, "0");
    const profile: CompanyProfile = {
      cnpj: cnpjBare,
      cnpj_formatted: formatCnpj(cnpjBare),
      company_name: (raw["razao_social"] as string) ?? "",
      trade_name: (raw["nome_fantasia"] as string) || undefined,
      registration_status: (raw["descricao_situacao_cadastral"] as CompanyProfile["registration_status"]) ?? "ATIVA",
      registration_date: (raw["data_inicio_atividade"] as string) ?? "",
      legal_nature_code: String(raw["codigo_natureza_juridica"] ?? ""),
      legal_nature: (raw["natureza_juridica"] as string) ?? "",
      size: (raw["porte"] as string) ?? "DEMAIS",
      share_capital: raw["capital_social"] as number | undefined,
      main_cnae: {
        code: String(raw["cnae_fiscal"] ?? "").padStart(7, "0"),
        description: (raw["cnae_fiscal_descricao"] as string) ?? "",
      },
      secondary_cnaes: ((raw["cnaes_secundarios"] as R[]) ?? [])
        .map(s => ({
          code: String(s["codigo"] ?? "").padStart(7, "0"),
          description: (s["descricao"] as string) ?? "",
        }))
        .filter(s => s.code !== "0000000"),
      address: {
        street: (raw["logradouro"] as string) ?? "",
        number: (raw["numero"] as string) ?? "",
        complement: (raw["complemento"] as string) || undefined,
        neighborhood: (raw["bairro"] as string) ?? "",
        zip_code: String(raw["cep"] ?? ""),
        city: (raw["municipio"] as string) ?? "",
        state: (raw["uf"] as string) ?? "",
      },
      phone: (raw["ddd_telefone_1"] as string) || undefined,
      email: (raw["email"] as string) || undefined,
      query_timestamp: queryTs,
    };

    const name = profile.trade_name ?? profile.company_name;
    const summary = `${name} (${profile.cnpj_formatted}): ${profile.registration_status}`;

    const event = new CDSEvent({
      content_type: CompaniesContentTypes.PROFILE,
      source: { "@id": CDSSources.BRASILAPI, fingerprint: fp },
      occurred_at: queryTs,
      lang: "pt-BR",
      payload: profile as unknown as R,
      context: {
        summary,
        model: "rule-based-v1",
        generated_at: queryTs,
      } satisfies ContextMeta,
    });

    if (this.signer) this.signer.sign(event);
    return event;
  }

  async fetchPartners(cnpj: string): Promise<CDSEvent> {
    const bare = validateCnpj(cnpj);
    const queryTs = new Date().toISOString();

    const resp = await globalThis.fetch(`${BRASILAPI_CNPJ_BASE}/${bare}`);
    if (!resp.ok) throw new Error(`BrasilAPI HTTP ${resp.status}`);
    const buf = Buffer.from(await resp.arrayBuffer());
    const fp = fingerprint(buf);
    const raw = JSON.parse(buf.toString("utf-8")) as R;

    const partners: CompanyPartners = {
      cnpj: String(raw["cnpj"] ?? "").padStart(14, "0"),
      company_name: (raw["razao_social"] as string) ?? "",
      partners: ((raw["qsa"] as R[]) ?? []).map(q => ({
        name: (q["nome_socio"] as string) ?? "",
        qualifier: (q["qualificacao_socio"] as string) ?? "",
        qualifier_code: Number(q["codigo_qualificacao_socio"] ?? 0),
        entry_date: (q["data_entrada_sociedade"] as string) || undefined,
        country: (q["pais"] as string) || undefined,
        legal_representative: (q["nome_representante_legal"] as string) || undefined,
      })),
      query_timestamp: queryTs,
    };

    const n = partners.partners.length;
    const event = new CDSEvent({
      content_type: CompaniesContentTypes.PARTNERS,
      source: { "@id": CDSSources.BRASILAPI, fingerprint: fp },
      occurred_at: queryTs,
      lang: "pt-BR",
      payload: partners as unknown as R,
      context: {
        summary: `${partners.company_name}: ${n} sócio${n !== 1 ? "s" : ""}`,
        model: "rule-based-v1",
        generated_at: queryTs,
      } satisfies ContextMeta,
    });

    if (this.signer) this.signer.sign(event);
    return event;
  }
}
