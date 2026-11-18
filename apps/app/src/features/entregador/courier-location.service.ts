import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { currentFix, haversineMeters } from './geolocation.util';

interface LocationResponse {
  interval_seconds?: number;
  recorded?: boolean;
}

/**
 * CourierLocationService — manda a posição do entregador enquanto ele está online.
 * Serve ao despacho por proximidade e ao rastro (courier_locations, guardado 7 dias,
 * visto pelo admin da área e pela loja da entrega).
 *
 * Quando:
 *   - Na hora em que fica online (posição fresca para o primeiro despacho)
 *   - No intervalo que o SERVIDOR devolve: 1 min com entrega ativa, 5 min sem
 *   - Na hora, logo depois de aceitar uma entrega (`refresh()`), para o rastro começar já
 * Filtro de movimento: não manda se andou menos de 20 m (com entrega) / 100 m (sem),
 * mas manda de qualquer jeito a cada 5 min para o servidor poder trocar o intervalo.
 *
 * Leitura avulsa (getCurrentPosition, NÃO watchPosition): o GPS só acorda na hora.
 * Endpoint: PATCH /v1/couriers/{id}/location (ignorado se o entregador estiver offline).
 */
@Injectable({ providedIn: 'root' })
export class CourierLocationService {
  private readonly http = inject(HttpClient);

  private timer: ReturnType<typeof setTimeout> | null = null;
  private courierId: number | null = null;
  private lastSent: { lat: number; lng: number; at: number } | null = null;
  private intervalMs = 300_000;
  private emAndamento = false;
  private readonly DEFAULT_INTERVAL_MS = 300_000; // 5 min
  private readonly MAX_SILENCE_MS = 300_000; // manda pelo menos a cada 5 min
  private readonly MIN_INTERVAL_MS = 5_000;

  /** Start tracking. Call immediately after courier goes online. */
  start(courierId: number): void {
    this.courierId = courierId;
    this.lastSent = null;
    this.intervalMs = this.DEFAULT_INTERVAL_MS;
    this.stopTimer();
    void this.tick(true); // envio imediato ao ficar online
  }

  /** Stop tracking. Call when courier goes offline. */
  stop(): void {
    this.stopTimer();
    this.courierId = null;
    this.lastSent = null;
  }

  /** Manda agora, sem filtro de movimento (ex.: logo depois de aceitar uma entrega). */
  refresh(): void {
    if (this.courierId === null) return;
    this.stopTimer();
    void this.tick(true);
  }

  private stopTimer(): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  private agendar(): void {
    this.stopTimer();
    if (this.courierId === null) return;
    this.timer = setTimeout(() => void this.tick(false), this.intervalMs);
  }

  /** Limiar de movimento: menor com entrega ativa (intervalo curto) para desenhar o trajeto. */
  private limiarMetros(): number {
    if (this.intervalMs < 30_000) return 0; // teste local (RASTRO_INTERVALO_TESTE_S): manda sempre
    return this.intervalMs < this.DEFAULT_INTERVAL_MS ? 20 : 100;
  }

  async tick(forcar = false): Promise<void> {
    if (this.courierId === null || this.emAndamento) return;
    this.emAndamento = true;
    try {
      const pos = await currentFix();
      if (pos === null || this.courierId === null) return;
      const agora = Date.now();
      if (
        !forcar &&
        this.lastSent &&
        agora - this.lastSent.at < this.MAX_SILENCE_MS &&
        haversineMeters(this.lastSent.lat, this.lastSent.lng, pos.lat, pos.lng) < this.limiarMetros()
      ) {
        return;
      }
      try {
        const res = await firstValueFrom(
          this.http.patch<LocationResponse | null>(`/v1/couriers/${this.courierId}/location`, {
            lat: pos.lat,
            lng: pos.lng,
            ...(pos.accuracy !== null ? { accuracy: pos.accuracy } : {}),
          }),
        );
        this.lastSent = { lat: pos.lat, lng: pos.lng, at: agora };
        const s = Number(res?.interval_seconds);
        if (Number.isFinite(s) && s > 0) this.intervalMs = Math.max(this.MIN_INTERVAL_MS, s * 1000);
      } catch {
        // Falha de rede: o próximo ciclo tenta de novo.
      }
    } finally {
      this.emAndamento = false;
      this.agendar();
    }
  }
}
