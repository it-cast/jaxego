import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type { AcceptResponse, OfferOut, OfferResult } from './offer.models';
import { currentPosition } from '../geolocation.util';

/**
 * OfferService — the courier's offer client (Phase 8). `active()` polls the
 * authoritative offer (the Redis TTL is the timer source of truth — ADR-104);
 * `accept()`/`decline()` resolve the offer. The accept is idempotent: a retry with
 * the same offer either wins or falls into "lost" (E3) — never a double accept.
 * NEVER logs PII (the offer carries none — RN-013).
 */
@Injectable({ providedIn: 'root' })
export class OfferService {
  private readonly http = inject(HttpClient);

  /** Poll the active offer; null when there is none (204). */
  async active(): Promise<OfferOut | null> {
    try {
      const data = await firstValueFrom(
        this.http.get<OfferOut>('/v1/offers/active', { observe: 'response' }),
      );
      return data.status === 204 ? null : (data.body ?? null);
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 401) {
        throw err;
      }
      return null;
    }
  }

  /** Accept an offer. Maps the server outcome to a terminal result (UI-SPEC §3.5).
   * Requires device GPS (audit log, CORRECAO-252) — 'gps_missing' if unavailable. */
  async accept(deliveryId: number): Promise<OfferResult> {
    const pos = await currentPosition();
    if (pos === null) return 'gps_missing';
    try {
      await firstValueFrom(
        this.http.post<AcceptResponse>(`/v1/offers/${deliveryId}/accept`, pos),
      );
      return 'won';
    } catch (err) {
      if (err instanceof HttpErrorResponse) {
        // 409 → someone else won the race (E3, no penalty); 404 → offer gone.
        if (err.status === 409) return 'lost';
        if (err.status === 404) return 'expired';
      }
      return 'error';
    }
  }

  /** Decline an offer → the cascade advances to the next candidate. */
  async decline(deliveryId: number): Promise<boolean> {
    try {
      await firstValueFrom(this.http.post(`/v1/offers/${deliveryId}/decline`, {}));
      return true;
    } catch {
      return false;
    }
  }
}
