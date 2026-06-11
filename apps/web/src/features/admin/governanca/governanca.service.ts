import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type { ScoreLevel } from '../../../shared/components/score-badge/score-badge.component';
import type { ScoreComponent } from '../../../shared/components/score-breakdown/score-breakdown.component';
import type {
  AppealDecision,
  SuspensionAppeal,
} from '../../../shared/components/suspension-panel/suspension-panel.component';

/**
 * Contratos de governança do admin de ÁREA (telas 09/19/20) — espelham
 * `apps/api/app/suspensions/schemas.py` e `app/scores/schemas.py`.
 *
 * Todos os endpoints exigem `require_role("admin_area")` + `area_scope`; a área entra
 * no WHERE (TH-03 → 404 fora de escopo). A decisão de disputa é ADMINISTRATIVA, SEM
 * efeito financeiro (DEC-004 → Phase 15). Suspensão sempre auditada (D-04).
 */

/** Disputa de pagamento da área (primitivo Phase 9). */
export interface DisputeRow {
  id: number;
  delivery_id: number;
  courier_id: number;
  status: string;
  reason: string | null;
  opened_at: string;
}

/** Score com breakdown explicável de um entregador (ADR-013). */
export interface CourierScore {
  courier_id: number;
  snapshot_date: string;
  total_score: number;
  level: ScoreLevel;
  components: ScoreComponent[];
}

export type SubjectType = 'courier' | 'merchant';
export type DisputeOutcome = 'procedente' | 'improcedente';

@Injectable({ providedIn: 'root' })
export class GovernancaService {
  private readonly http = inject(HttpClient);

  // --- Suspensões / recursos (REQ-045) -------------------------------------
  /** Lista os recursos de suspensão da área (abertos ou todos). */
  async listAppeals(openOnly = false, limit = 50, offset = 0): Promise<SuspensionAppeal[]> {
    return firstValueFrom(
      this.http.get<SuspensionAppeal[]>('/v1/admin/suspensions', {
        params: { open_only: openOnly, limit, offset },
      }),
    );
  }

  /** Abre uma suspensão (motivo obrigatório → auditada). Abre a janela de recurso. */
  async openSuspension(
    subjectType: SubjectType,
    subjectId: number,
    reason: string,
  ): Promise<SuspensionAppeal> {
    return firstValueFrom(
      this.http.post<SuspensionAppeal>('/v1/admin/suspensions', {
        subject_type: subjectType,
        subject_id: subjectId,
        reason,
      }),
    );
  }

  /** Registra a decisão do recurso; `overturned` reverte a suspensão (auditada). */
  async decideAppeal(
    appealId: number,
    decision: AppealDecision,
  ): Promise<SuspensionAppeal> {
    return firstValueFrom(
      this.http.patch<SuspensionAppeal>(
        `/v1/admin/suspensions/${appealId}/decision`,
        { decision },
      ),
    );
  }

  // --- Disputas (REQ-044 — decisão administrativa, SEM efeito financeiro) ---
  /** Lista as disputas de pagamento da área (primitivo Phase 9). */
  async listDisputes(limit = 50, offset = 0): Promise<DisputeRow[]> {
    return firstValueFrom(
      this.http.get<DisputeRow[]>('/v1/admin/disputes', {
        params: { limit, offset },
      }),
    );
  }

  /**
   * Registra a decisão administrativa da disputa (auditada). SEM efeito financeiro
   * — a resolução financeira (bloqueio/restituição) é da Phase 15 (DEC-004).
   */
  async decideDispute(
    disputeId: number,
    outcome: DisputeOutcome,
    note?: string,
  ): Promise<DisputeRow> {
    return firstValueFrom(
      this.http.patch<DisputeRow>(`/v1/admin/disputes/${disputeId}/decision`, {
        outcome,
        note: note ?? null,
      }),
    );
  }

  // --- Score (REQ-020 / ADR-013) -------------------------------------------
  /** Breakdown de score de um entregador da área (telas 19/20/24). */
  async courierScore(courierId: number): Promise<CourierScore> {
    return firstValueFrom(
      this.http.get<CourierScore>(`/v1/admin/scores/${courierId}`),
    );
  }
}
