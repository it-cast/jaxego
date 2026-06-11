import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiErrorEnvelope } from '../../../core/auth/auth.models';
import {
  CreateDeliveryRequest,
  CreateDeliveryResponse,
  DeliveryListItem,
  DeliveryListResponse,
} from './delivery.models';

export type CreateDeliveryResult =
  | { ok: true; data: CreateDeliveryResponse }
  | { ok: false; code?: string; message?: string; planLimit?: boolean };

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
      const envelope = err.error as ApiErrorEnvelope | undefined;
      const code = envelope?.error?.code;
      const message = envelope?.error?.message;
      const requestId = envelope?.error?.request_id;
      if (requestId) {
        // Correlation only — never expose request_id, never log PII.
        console.warn('[delivery] create failed', { code, request_id: requestId });
      }
      if (err.status === 402 || code === 'plan_limit_reached') {
        return { ok: false, code, message, planLimit: true };
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
}
