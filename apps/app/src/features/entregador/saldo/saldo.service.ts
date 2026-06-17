import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/**
 * Contratos da tela 16 (extrato/saldo + saque do entregador) — espelham
 * `apps/api/app/withdrawals/router.py`. Dinheiro em CENTAVOS inteiros (DRV-009);
 * o mínimo de saque vem do BACKEND (`minimum_cents`), nunca reimplementado aqui
 * (D-04/D-07). Reads escopados ao entregador (IDOR → saldo 0 — TH-01). O saque é
 * idempotente por `reference` no servidor; o cliente envia um `idempotency_key`
 * para evitar duplo-clique (TH-02).
 */

/** Saldo disponível + mínimo de saque (GET /v1/withdrawals/balance). */
export interface Balance {
  balance_cents: number;
  /** Mínimo de saque parametrizado no backend (seed — D-07). */
  minimum_cents: number;
}

/** Uma linha do extrato (GET /v1/withdrawals/extract) — corrida liberada (crédito). */
export interface ExtractEntry {
  id: number;
  /** "credit" (corrida liberada). */
  kind: string;
  delivery_id: number;
  amount_cents: number;
  at: string | null;
}

/** Uma linha do histórico de saques (GET /v1/withdrawals/history). */
export interface WithdrawalHistoryRow {
  id: number;
  amount_cents: number;
  /** pending | paid | failed. */
  status: string;
  transaction_id: string | null;
  settled_at: string | null;
  requested_at: string | null;
}

/** Resultado de um saque (POST /v1/withdrawals). */
export interface WithdrawalResult {
  id: number;
  amount_cents: number;
  status: string;
  transaction_id: string | null;
}

@Injectable({ providedIn: 'root' })
export class SaldoService {
  private readonly http = inject(HttpClient);

  /** Saldo disponível + mínimo (a regra de mínimo vem do backend). */
  async balance(): Promise<Balance> {
    return firstValueFrom(this.http.get<Balance>('/v1/withdrawals/balance'));
  }

  /** O extrato (corridas liberadas) do entregador. */
  async extract(): Promise<ExtractEntry[]> {
    return firstValueFrom(
      this.http.get<ExtractEntry[]>('/v1/withdrawals/extract'),
    );
  }

  /** O histórico de saques do entregador (status/valor). */
  async history(): Promise<WithdrawalHistoryRow[]> {
    return firstValueFrom(
      this.http.get<WithdrawalHistoryRow[]>('/v1/withdrawals/history'),
    );
  }

  /** Solicita um saque do saldo disponível. `idempotencyKey` evita duplo-clique. */
  async requestWithdrawal(
    amountCents: number,
    idempotencyKey?: string,
  ): Promise<WithdrawalResult> {
    return firstValueFrom(
      this.http.post<WithdrawalResult>('/v1/withdrawals', {
        amount_cents: amountCents,
        idempotency_key: idempotencyKey ?? null,
      }),
    );
  }
}
