/**
 * SignedData CDS — Signer & Verifier
 * RSA-PSS SHA-256 via Node.js built-in crypto.  Zero external deps.
 */
import { CDSEvent } from "./schema.js";
export declare function generateKeypair(privateKeyPath?: string, publicKeyPath?: string): void;
export declare class CDSSigner {
    private readonly privateKey;
    readonly issuer: string;
    constructor(privateKey: string, issuer?: string);
    sign(event: CDSEvent): CDSEvent;
}
export declare class CDSVerifier {
    private readonly publicKey;
    constructor(publicKey: string);
    verify(event: CDSEvent): boolean;
}
//# sourceMappingURL=signer.d.ts.map