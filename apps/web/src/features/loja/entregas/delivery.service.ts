import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiErrorEnvelope } from '@jaxego/core/auth/auth.models';
import {
  CreateDeliveryRequest,
  CreateDeliveryResponse,
  DeliveryListItem,
  DeliveryListResponse,
} from '@jaxego/shared/models/delivery.models';

export type CreateDeliveryResult =
  | { ok: true; data: CreateDeliveryResponse }
  | { ok: false; code?: string; message?: string; planLimit?: boolean; planName?: string; planLimitCount?: number; planUsed?: number };

/**
 * DeliveryService — F-03 API client (Phase 7). NEVER logs recipient PII (only the
 * error request_id for correlation). The plan-limit 402 (`plan_limit_reached`) is
 * surfaced as `planLimit: true` so the form opens the upgrade modal (E4) instead
 * of showing a generic error.
 */
@Injectable({ providedIn: 'root' })
export class DeliveryService {
  private readonly http = inject(HttpClient);

  async create(req: CreateDeliveryRequest): Promise<CreateDeliveryResult> {
    try {
      const data = await firstValueFrom(
        this.http.post<CreateDeliveryResponse>('/v1/deliveries', req),
      );
      return { ok: true, data };
    } catch (err) {
      return this.mapError(err);
    }
  }

  async list(opts?: {
    state?: string;
    paymentMethod?: string;
    limit?: number;
    offset?: number;
  }): Promise<DeliveryListResponse> {
    let params = new HttpParams();
    if (opts?.state) params = params.set('state', opts.state);
    if (opts?.paymentMethod) params = params.set('payment_method', opts.paymentMethod);
    if (opts?.limit != null) params = params.set('limit', String(opts.limit));
    if (opts?.offset != null) params = params.set('offset', String(opts.offset));
    return firstValueFrom(
      this.http.get<DeliveryListResponse>('/v1/deliveries', { params }),
    );
  }

  /** Read a single delivery the store owns (404 if not owned — TH-03). */
  async get(deliveryId: number): Promise<DeliveryListItem | null> {
    try {
      return await firstValueFrom(
        this.http.get<DeliveryListItem>(`/v1/deliveries/${deliveryId}`),
      );
    } catch {
      return null;
    }
  }

  async getRating(deliveryId: number): Promise<{ stars: number; comment: string | null } | null> {
    try {
      return await firstValueFrom(
        this.http.get<{ stars: number; comment: string | null }>(`/v1/deliveries/${deliveryId}/rating`),
      );
    } catch {
      return null;
    }
  }

  async rate(deliveryId: number, stars: number, comment: string | null): Promise<boolean> {
    try {
      await firstValueFrom(
        this.http.post(`/v1/deliveries/${deliveryId}/rating`, { stars, comment }),
      );
      return true;
    } catch {
      return false;
    }
  }

  async cancel(deliveryId: number, reason?: string): Promise<boolean> {
    try {
      await firstValueFrom(
        this.http.post(`/v1/deliveries/${deliveryId}/cancel`, { reason: reason ?? null }),
      );
      return true;
    } catch {
      return false;
    }
  }

  private mapError(err: unknown): CreateDeliveryResult {
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        return {
          ok: false,
          code: 'network',
          message: 'Sem conexão com o servidor. Verifique sua internet e tente de novo.',
        };
      }
      // FastAPI 422 Pydantic validation: { detail: [{msg, loc, ...}] }
      if (err.status === 422) {
        const detail = (err.error as { detail?: { msg?: string }[] } | undefined)?.detail;
        const msg = Array.isArray(detail) && detail[0]?.msg
          ? detail[0].msg.replace(/^Value error,\s*/i, '')
          : 'Dados inválidos. Verifique os campos e tente de novo.';
        return { ok: false, code: 'validation_error', message: msg };
      }
      const envelope = err.error as ApiErrorEnvelope | undefined;
      const code = envelope?.error?.code;
      const message = envelope?.error?.message;
      const requestId = envelope?.error?.request_id;
      if (requestId) {
        // Correlation only — never expose request_id, never log PII.
        console.warn('[delivery] create failed', { code, request_id: requestId });
      }
      if (err.status === 402 || code === 'plan_limit_reached') {
        const errBody = envelope?.error as Record<string, unknown> | undefined;
        return {
          ok: false,
          code,
          message,
          planLimit: true,
          planName: errBody?.['plan_name'] as string | undefined,
          planLimitCount: errBody?.['limit'] as number | undefined,
          planUsed: errBody?.['used'] as number | undefined,
        };
      }
      // F-03 E3 (Phase 10): a card/pix refusal/outage is a 502 with this code; surface it
      // so the form offers retry / switch-to-direct (the delivery was NOT created).
      if (code === 'payment_gateway_error') {
        return { ok: false, code, message };
      }
      if (err.status >= 500) {
        return {
          ok: false,
          code: 'server',
          message: 'Tivemos um problema aqui. Já estamos vendo — tente em instantes.',
        };
      }
      return { ok: false, code, message };
    }
    return {
      ok: false,
      code: 'unknown',
      message: 'Não foi possível criar a entrega agora. Tente de novo.',
    };
  }

  async estimate(dropoffNeighborhoodId: number, teamId?: number | null): Promise<{ estimate_min_cents: number | null; estimate_max_cents: number | null; courier_count: number }> {
    try {
      const params: Record<string, any> = { dropoff_neighborhood_id: dropoffNeighborhoodId };
      if (teamId) params['team_id'] = teamId;
      return await firstValueFrom(
        this.http.get<{ estimate_min_cents: number | null; estimate_max_cents: number | null; courier_count: number }>(
          '/v1/deliveries/estimate', { params }
        ),
      );
    } catch {
      return { estimate_min_cents: null, estimate_max_cents: null, courier_count: 0 };
    }
  }
}
