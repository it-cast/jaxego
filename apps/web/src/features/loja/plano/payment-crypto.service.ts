import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/**
 * PaymentCryptoService — fetches the backend RSA public key and encrypts the card
 * IN THE BROWSER with RSA-OAEP (SHA-256) before it ever leaves the component
 * (D-02 / TH-A). The plaintext card NEVER goes to global state, a log, analytics,
 * storage, or the network — only the base64 ciphertext is sent in the POST body.
 *
 * Uses the Web Crypto API (SubtleCrypto) — no third-party crypto dependency.
 */
export interface CardPlain {
  nomeTitular: string;
  numeroCartao: string;
  validade: string; // MM/AAAA
  cvv: string;
}

@Injectable({ providedIn: 'root' })
export class PaymentCryptoService {
  private readonly http = inject(HttpClient);
  private publicKey: CryptoKey | null = null;

  /** Fetch + import the RSA public key once (GET /v1/payments/chave-publica). */
  private async getKey(): Promise<CryptoKey> {
    if (this.publicKey) return this.publicKey;
    const { public_key } = await firstValueFrom(
      this.http.get<{ public_key: string }>('/v1/payments/chave-publica'),
    );
    const der = this.pemToArrayBuffer(public_key);
    this.publicKey = await crypto.subtle.importKey(
      'spki',
      der,
      { name: 'RSA-OAEP', hash: 'SHA-256' },
      false,
      ['encrypt'],
    );
    return this.publicKey;
  }

  /**
   * Encrypt the card JSON with RSA-OAEP → base64. The card object is consumed here
   * and never retained — the caller passes it transiently and forgets it.
   */
  async encryptCard(card: CardPlain): Promise<string> {
    const key = await this.getKey();
    const data = new TextEncoder().encode(JSON.stringify(card));
    const cipher = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, key, data);
    return this.arrayBufferToBase64(cipher);
  }

  private pemToArrayBuffer(pem: string): ArrayBuffer {
    const body = pem
      .replace(/-----BEGIN [^-]+-----/, '')
      .replace(/-----END [^-]+-----/, '')
      .replace(/\s+/g, '');
    const bin = atob(body);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes.buffer;
  }

  private arrayBufferToBase64(buf: ArrayBuffer): string {
    const bytes = new Uint8Array(buf);
    let bin = '';
    for (const byte of bytes) bin += String.fromCharCode(byte);
    return btoa(bin);
  }
}
