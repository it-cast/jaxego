import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import type { PoolAcceptResponse, PoolAcceptResult, PoolItemOut } from './pool.models';

/**
 * PoolService — the courier's unanswered-pool client. `list()` browses
 * SEM_RESPOSTA deliveries this courier is eligible for (same coverage/team
 * filter the cascade itself applies); `accept()` self-assigns one, racing any
 * other courier who taps the same card (single winner, no penalty on loss —
 * mirrors `OfferService.accept`).
 */
@Injectable({ providedIn: 'root' })
export class PoolService {
  private readonly http = inject(HttpClient);

  async list(): Promise<PoolItemOut[]> {
    try {
      return await firstValueFrom(this.http.get<PoolItemOut[]>('/v1/offers/pool'));
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 401) {
        throw err;
      }
      return [];
    }
  }

  async accept(deliveryId: number): Promise<PoolAcceptResult> {
    try {
      await firstValueFrom(
        this.http.post<PoolAcceptResponse>(`/v1/offers/pool/${deliveryId}/accept`, {}),
      );
      return 'won';
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 409) {
        return 'lost';
      }
      return 'error';
    }
  }
}
