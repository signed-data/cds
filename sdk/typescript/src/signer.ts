/**
 * SignedData CDS — Signer & Verifier
 * RSA-PSS SHA-256 via Node.js built-in crypto.  Zero external deps.
 */

import {
  createSign, createVerify,
  generateKeyPairSync, createHash,
} from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import type { CDSEvent } from "./schema.js";

export function generateKeypair(
  privateKeyPath = "keys/private.pem",
  publicKeyPath  = "keys/public.pem",
): void {
  const { privateKey, publicKey } = generateKeyPairSync("rsa", {
    modulusLength:      4096,
    publicKeyEncoding:  { type: "spki",  format: "pem" },
    privateKeyEncoding: { type: "pkcs8", format: "pem" },
  });
  writeFileSync(privateKeyPath, privateKey);
  writeFileSync(publicKeyPath,  publicKey);
  console.log(`✅ Keypair: ${privateKeyPath} / ${publicKeyPath}`);
}

function loadPem(pathOrPem: string): string {
  return pathOrPem.startsWith("-----") ? pathOrPem : readFileSync(pathOrPem, "utf-8");
}

const PSS_OPTS = { padding: 6, saltLength: -2 } as const;

export class CDSSigner {
  private readonly privateKey: string;
  readonly issuer: string;

  constructor(privateKey: string, issuer = "signed-data.org") {
    this.privateKey = loadPem(privateKey);
    this.issuer     = issuer;
  }

  sign(event: CDSEvent): CDSEvent {
    const canonical  = event.canonicalBytes();
    const hash       = "sha256:" + createHash("sha256").update(canonical).digest("hex");
    const signer     = createSign("SHA256");
    signer.update(canonical);
    signer.end();
    const signature  = signer.sign({ key: this.privateKey, ...PSS_OPTS }, "base64");
    event.integrity  = { hash, signature, signed_by: this.issuer };
    return event;
  }
}

export class CDSVerifier {
  private readonly publicKey: string;

  constructor(publicKey: string) {
    this.publicKey = loadPem(publicKey);
  }

  verify(event: CDSEvent): boolean {
    if (!event.integrity) throw new Error("Event has no integrity metadata.");
    const canonical = event.canonicalBytes();
    const expected  = "sha256:" + createHash("sha256").update(canonical).digest("hex");
    if (expected !== event.integrity.hash)
      throw new Error(`Hash mismatch. Expected ${expected}`);
    const v = createVerify("SHA256");
    v.update(canonical); v.end();
    const valid = v.verify({ key: this.publicKey, ...PSS_OPTS }, event.integrity.signature, "base64");
    if (!valid) throw new Error("Signature invalid — event may be tampered.");
    return true;
  }
}
