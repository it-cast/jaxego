import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type { ScoreLevel } from '../../shared/components/score-badge/score-badge.component';
import type { ScoreComponent } from '../../shared/components/score-breakdown/score-breakdown.component';
import type { SuspensionAppeal } from '../../shared/components/suspension-panel/suspension-panel.component';

/**
 * Contratos do admin de plataforma (telas 23/24/25) — espelham
 * `apps/api/app/platform_admin/schemas.py` e `app/suspensions/schemas.py`.
 *
 * Todas as leituras são cross-área e AUDITADAS no backend (TH-02 / D-06). O acesso
 * exige `require_platform_admin` (TOTP — ADR-005). Revenue share é só config
 * parametrizada — NÃO move dinheiro (D-07 / DEC-004 → Phase 15).
 */

/** Uma linha da visão geral por área (tela 23). */
export interface AreaOverviewRow {
  area_id: number;
  codename: string;
  name: string;
  couriers: number;
  merchants: number;
  deliveries: number;
}

/** Resultado de busca de entregador com nível de score (tela 24). */
export interface CourierSearchRow {
  courier_id: number;
  area_id: number;
  full_name: string;
  status: string;
  score_total: number | null;
  score_level: ScoreLevel | null;
}

/** Resultado de busca de loja (tela 24). */
export interface MerchantSearchRow {
  merchant_id: number;
  area_id: number;
  name: string;
  status: string;
}

/** Disputa de pagamento (primitivo Phase 9) — listagem global (tela 25). */
export interface DisputeRow {
  id: number;
  delivery_id: number;
  courier_id: number;
  status: string;
  reason: string | null;
  opened_at: string;
}

/** Configuração de repasse parametrizada por área (D-07). */
export interface RevenueShare {
  area_id: number;
  share_pct: number;
  effective_from: string;
}

/** Snapshot de score com breakdown explicável (ADR-013). */
export interface CourierScore {
  courier_id: number;
  snapshot_date: string;
  total_score: number;
  level: ScoreLevel;
  components: ScoreComponent[];
}

@Injectable({ providedIn: 'root' })
export class PlatformAdminService {
  private readonly http = inject(HttpClient);
  private readonly base = '/v1/platform';

  /** Visão geral por área (tela 23). Leitura cross-área auditada. */
  async overview(): Promise<AreaOverviewRow[]> {
    return firstValueFrom(
      this.http.get<AreaOverviewRow[]>(`${this.base}/overview`),
    );
  }

  /** Busca de entregadores cross-área com score (tela 24). */
  async searchCouriers(params: {
    q?: string;
    areaId?: number;
    limit?: number;
    offset?: number;
  } = {}): Promise<CourierSearchRow[]> {
    return firstValueFrom(
      this.http.get<CourierSearchRow[]>(`${this.base}/couriers`, {
        params: this.queryParams(params),
      }),
    );
  }

  /** Busca de lojas cross-área (tela 24). */
  async searchMerchants(params: {
    q?: string;
    areaId?: number;
    limit?: number;
    offset?: number;
  } = {}): Promise<MerchantSearchRow[]> {
    return firstValueFrom(
      this.http.get<MerchantSearchRow[]>(`${this.base}/merchants`, {
        params: this.queryParams(params),
      }),
    );
  }

  /** Disputas globais (cross-área) — tela 25. */
  async listDisputes(limit = 50, offset = 0): Promise<DisputeRow[]> {
    return firstValueFrom(
      this.http.get<DisputeRow[]>(`${this.base}/disputes`, {
        params: { limit, offset },
      }),
    );
  }

  /** Suspensões/recursos globais (cross-área) — tela 25. */
  async listSuspensions(
    openOnly = false,
    limit = 50,
    offset = 0,
  ): Promise<SuspensionAppeal[]> {
    return firstValueFrom(
      this.http.get<SuspensionAppeal[]>(`${this.base}/suspensions`, {
        params: { open_only: openOnly, limit, offset },
      }),
    );
  }

  /** Repasse parametrizado da área (config — NÃO move dinheiro). */
  async getRevenueShare(areaId: number): Promise<RevenueShare | null> {
    return firstValueFrom(
      this.http.get<RevenueShare | null>(
        `${this.base}/areas/${areaId}/revenue-share`,
      ),
    );
  }

  /** Define novo % de repasse efetivo (auditado). NÃO move dinheiro (D-07). */
  async setRevenueShare(areaId: number, sharePct: number): Promise<RevenueShare> {
    return firstValueFrom(
      this.http.put<RevenueShare>(`${this.base}/areas/${areaId}/revenue-share`, {
        share_pct: sharePct,
      }),
    );
  }

  /** Breakdown de score de um entregador (admin de área — reusado na tela 24). */
  async courierScore(courierId: number): Promise<CourierScore> {
    return firstValueFrom(
      this.http.get<CourierScore>(`/v1/admin/scores/${courierId}`),
    );
  }

  private queryParams(params: {
    q?: string;
    areaId?: number;
    limit?: number;
    offset?: number;
  }): Record<string, string | number> {
    const out: Record<string, string | number> = {
      limit: params.limit ?? 50,
      offset: params.offset ?? 0,
    };
    if (params.q) {
      out['q'] = params.q;
    }
    if (params.areaId != null) {
      out['area_id'] = params.areaId;
    }
    return out;
  }
}
