import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface CoverageRow {
  neighborhood_id: number;
  kind: 'include' | 'exclude';
}

export interface PricingRow {
  neighborhood_id?: number | null;
  up_to_km?: number | null;
  price: number;
  return_pct?: number | null;
}

export interface CoveragePayload {
  includes: number[];
  excludes: number[];
}

export interface PricingPayload {
  mode: 'neighborhood' | 'km';
  rows: PricingRow[];
}

/**
 * CoberturaPrecosService — the courier's own coverage + pricing (RN-003/RN-015).
 *
 * Self-only endpoints (the backend resolves ownership + area scope). A price
 * below the area floor returns 422 ("price_below_floor") whose message CITES the
 * floor — the page surfaces it citing the value. The floor itself is read from the
 * area config (never hardcoded in the front).
 */
@Injectable({ providedIn: 'root' })
export class CoberturaPrecosService {
  private readonly http = inject(HttpClient);

  async getCoverage(courierId: number): Promise<CoverageRow[]> {
    return firstValueFrom(
      this.http.get<CoverageRow[]>(`/v1/couriers/${courierId}/coverage`)
    );
  }

  async putCoverage(courierId: number, body: CoveragePayload): Promise<void> {
    await firstValueFrom(
      this.http.put<void>(`/v1/couriers/${courierId}/coverage`, body)
    );
  }

  async putPricing(courierId: number, body: PricingPayload): Promise<void> {
    await firstValueFrom(
      this.http.put<void>(`/v1/couriers/${courierId}/pricing`, body)
    );
  }
}
