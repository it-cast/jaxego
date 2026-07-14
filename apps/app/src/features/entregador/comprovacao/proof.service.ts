import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface ProofResult {
  delivery_id: number;
  state: string;
  geofence_ok: boolean;
  low_confidence: boolean;
}

export type ProofKind = 'pickup' | 'delivery' | 'refusal';

interface PresignResponse {
  storage_key: string;
  upload_url: string;
  method: string;
  headers: Record<string, string>;
  expires_in: number;
}

/**
 * ProofService — F-06 proof flow client (Phase 9). Presign → PUT to B2 → submit.
 *
 * The photo is uploaded DIRECT to B2 via the presigned PUT (bytes never transit the
 * backend). The submit carries the storage_key + the client GPS (A3 contract). The
 * verdict (geofence_ok / low_confidence) drives the UI CTA lock/unlock — the server
 * is the authority. Never logs PII.
 */
@Injectable({ providedIn: 'root' })
export class ProofService {
  private readonly http = inject(HttpClient);

  async submitPhoto(
    deliveryId: number,
    kind: ProofKind,
    file: File,
    lat: number | null,
    lng: number | null,
    refusalReason?: string,
  ): Promise<ProofResult> {
    const contentType = file.type || 'image/jpeg';
    const presign = await firstValueFrom(
      this.http.post<PresignResponse>(`/v1/deliveries/${deliveryId}/proof/presign`, {
        content_type: contentType,
      }),
    );
    // Direct PUT to storage with the signed headers.
    await firstValueFrom(
      this.http.put(presign.upload_url, file, { headers: presign.headers }),
    );
    return firstValueFrom(
      this.http.post<ProofResult>(`/v1/deliveries/${deliveryId}/proof`, {
        proof_kind: kind,
        storage_key: presign.storage_key,
        lat,
        lng,
        refusal_reason: refusalReason ?? null,
      }),
    );
  }

  async submitReference(
    deliveryId: number,
    reference: string,
    lat: number | null = null,
    lng: number | null = null,
  ): Promise<ProofResult> {
    return firstValueFrom(
      this.http.post<ProofResult>(`/v1/deliveries/${deliveryId}/proof/reference`, {
        reference_number: reference,
        lat,
        lng,
      }),
    );
  }

  async validateReference(deliveryId: number, reference: string): Promise<boolean> {
    const res = await firstValueFrom(
      this.http.post<{ valid: boolean }>(`/v1/deliveries/${deliveryId}/proof/validate-reference`, {
        reference_number: reference,
      }),
    );
    return res.valid;
  }

  async confirmPayment(
    deliveryId: number,
    outcome: 'cash' | 'pix' | 'not_received',
    amountCents: number | null,
  ): Promise<{ dispute_opened: boolean }> {
    return firstValueFrom(
      this.http.post<{ dispute_opened: boolean }>(
        `/v1/deliveries/${deliveryId}/payment-confirmation`,
        { outcome, amount_cents: amountCents },
      ),
    );
  }
}
