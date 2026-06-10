import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

export interface Neighborhood {
  id: number;
  area_id: number;
  name: string;
  is_informal: boolean;
  polygon_status: 'defined' | 'by_name';
}

export interface NeighborhoodCreate {
  name: string;
  is_informal?: boolean;
  polygon_geojson?: unknown;
}

/**
 * AdminNeighborhoodsService — CRUD over /v1/neighborhoods (REQ-003).
 *
 * The backend is the authority: it validates the GeoJSON polygon (anti-DoS) and
 * blocks removal with active deliveries (409). The UI surfaces those errors with
 * actionable copy; client-side polygon checks are UX only.
 */
@Injectable({ providedIn: 'root' })
export class AdminNeighborhoodsService {
  private readonly http = inject(HttpClient);

  async list(): Promise<Neighborhood[]> {
    return firstValueFrom(this.http.get<Neighborhood[]>('/v1/neighborhoods'));
  }

  async create(body: NeighborhoodCreate): Promise<Neighborhood> {
    return firstValueFrom(this.http.post<Neighborhood>('/v1/neighborhoods', body));
  }

  async updatePolygon(id: number, polygonGeojson: unknown): Promise<Neighborhood> {
    return firstValueFrom(
      this.http.patch<Neighborhood>(`/v1/neighborhoods/${id}/polygon`, {
        polygon_geojson: polygonGeojson,
      })
    );
  }

  async remove(id: number): Promise<void> {
    await firstValueFrom(this.http.delete<void>(`/v1/neighborhoods/${id}`));
  }
}
