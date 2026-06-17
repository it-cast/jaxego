import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/** The typed area config (mirrors the backend AreaConfig — Plan 01). */
export interface AreaConfig {
  kyc_level: 'simples' | 'completa';
  piso_entrega: string; // Decimal as string ("8.00")
  piso_km: string;
  geofence_m: number;
  timeout_oferta_s: number;
  timeout_favoritos_s: number;
  politica_retorno_pct: number;
}

export interface AreaRead {
  id: number;
  codename: string;
  name: string;
  config: AreaConfig | Record<string, unknown>;
}

/**
 * AdminAreaConfigService — reads/patches the area config (REQ-002).
 *
 * The PATCH is the only write; the backend validates ranges (422) and records a
 * before/after audit row for sensitive keys. A 422 is surfaced field-by-field by
 * the page; a 5xx surfaces the error state.
 */
@Injectable({ providedIn: 'root' })
export class AdminAreaConfigService {
  private readonly http = inject(HttpClient);

  // A área é resolvida pelo token (escopo do admin), não por id no path.
  async get(): Promise<AreaRead> {
    return firstValueFrom(this.http.get<AreaRead>('/v1/admin/area'));
  }

  async patchConfig(config: AreaConfig): Promise<AreaRead> {
    return firstValueFrom(
      this.http.patch<AreaRead>('/v1/admin/area/config', { config })
    );
  }
}
