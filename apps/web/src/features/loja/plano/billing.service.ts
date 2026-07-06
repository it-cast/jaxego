import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/**
 * BillingService — Phase 10 subscription/charge API client. Money is integer cents
 * (formatted to R$ pt-BR at the edge). NEVER logs card data — the card is encrypted
 * by PaymentCryptoService in the component; here we only send the opaque blob.
 */
export interface SubscriptionView {
  subscription_id: number;
  billing_status: 'trial' | 'active' | 'blocked' | 'cancelado';
  payment_method: 'card' | 'pix' | null;
  plan_id: number;
  amount_cents: number;
  next_due_at: string | null;
  qr_code: string | null;
  qr_code_base64: string | null;
  pix_autorizacao_status: string | null;
}

export interface ChargeHistoryItem {
  id: number;
  kind: string;
  amount_cents: number;
  method: string;
  status: string;
  transaction_id: string | null;
  created_at: string | null;
  due_at: string | null;
}

export interface SubscribeRequest {
  plan_id: number;
  cycle: 'mensal' | 'anual';
  method: 'card' | 'pix';
  card_blob?: string;
  pix_recorrente?: boolean;
}

export interface PlanChangeResult {
  kind: 'upgrade' | 'downgrade' | 'noop';
  charged_cents: number;
  effective: 'now' | 'cycle_end';
}

@Injectable({ providedIn: 'root' })
export class BillingService {
  private readonly http = inject(HttpClient);

  async subscription(): Promise<SubscriptionView> {
    return firstValueFrom(
      this.http.get<SubscriptionView>('/v1/payments/assinatura'),
    );
  }

  async subscribe(req: SubscribeRequest): Promise<SubscriptionView> {
    return firstValueFrom(
      this.http.post<SubscriptionView>('/v1/payments/assinar', req),
    );
  }

  async changePlan(targetPlanId: number): Promise<PlanChangeResult> {
    return firstValueFrom(
      this.http.post<PlanChangeResult>('/v1/payments/assinatura/mudar-plano', {
        target_plan_id: targetPlanId,
      }),
    );
  }

  async charges(): Promise<ChargeHistoryItem[]> {
    return firstValueFrom(
      this.http.get<ChargeHistoryItem[]>('/v1/payments/cobrancas'),
    );
  }
}

/** Format integer cents as R$ pt-BR (e.g. 9990 → "R$ 99,90"). */
export function formatCents(cents: number): string {
  return (cents / 100).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}
