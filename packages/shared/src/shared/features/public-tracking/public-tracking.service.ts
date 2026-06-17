import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/** Minimised public tracking payload (mirrors the server serializer — RN-013/RN-022). */
export interface PublicTracking {
  state: string;
  timeline: { state: string; at: string | null }[];
  eta_seconds: number | null;
  dropoff: { neighborhood_id: number; address?: string; number?: string; complement?: string };
  courier: { vehicle_type: string } | null;
  courier_position: { lat: number; lng: number } | null;
}

export type PublicTrackingResult =
  | { ok: true; data: PublicTracking }
  | { ok: false; notFound: boolean };

/**
 * PublicTrackingService — fetches the token-only public tracker (tela 26). No auth.
 * A 404 surfaces as `notFound` so the page shows the "link inválido" state
 * (anti-enumeração — the copy never reveals whether the token existed).
 */
@Injectable({ providedIn: 'root' })
export class PublicTrackingService {
  private readonly http = inject(HttpClient);

  async get(token: string): Promise<PublicTrackingResult> {
    try {
      const data = await firstValueFrom(
        this.http.get<PublicTracking>(`/v1/public/tracking/${encodeURIComponent(token)}`),
      );
      return { ok: true, data };
    } catch {
      // Any failure (404 / network) → show the generic "not found / expired" state.
      return { ok: false, notFound: true };
    }
  }
}
