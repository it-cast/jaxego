import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface CoverageRow {
  neighborhood_id: number;
  kind: 'include' | 'exclude';
}

export interface PricingRow {
  mode?: 'neighborhood' | 'km';
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

export interface NeighborhoodCatalogItem {
  id: number;
  area_id: number;
  name: string;
  is_informal: boolean;
  polygon_status: string;
}

export interface ZonaItem {
  zona_id: number;
  zona_nome: string;
  boundary: object | null;
  team_preco_cents: number | null;
  courier_preco_cents: number | null;
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

  async catalog(): Promise<NeighborhoodCatalogItem[]> {
    return firstValueFrom(
      this.http.get<NeighborhoodCatalogItem[]>('/v1/neighborhoods/catalog')
    );
  }

  async getCoverage(courierId: number): Promise<CoverageRow[]> {
    return firstValueFrom(
      this.http.get<CoverageRow[]>(`/v1/couriers/${courierId}/coverage`)
    );
  }

  async getPricing(courierId: number): Promise<PricingRow[]> {
    return firstValueFrom(
      this.http.get<PricingRow[]>(`/v1/couriers/${courierId}/pricing`)
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

  async listZonas(courierId: number): Promise<ZonaItem[]> {
    return firstValueFrom(
      this.http.get<ZonaItem[]>(`/v1/couriers/${courierId}/zonas`)
    );
  }

  async setZonaPreco(courierId: number, zonaId: number, precoCents: number): Promise<void> {
    await firstValueFrom(
      this.http.put(`/v1/couriers/${courierId}/zonas/${zonaId}`, { preco_cents: precoCents })
    );
  }
}
