import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { currentPosition, haversineMeters } from './geolocation.util';

/**
 * CourierLocationService — posts courier position while online (dispatch ranking).
 *
 * Triggers:
 *   - Immediately when going online (zero-stale position for the first dispatch)
 *   - Every 5 minutes while online (keeps position fresh)
 *   - Movement filter 100m: skips the POST if courier didn't move (saves data/battery)
 *
 * Uses one-shot getCurrentPosition (NOT watchPosition) — GPS wakes on demand only.
 * Endpoint: PATCH /v1/couriers/{id}/location (backend ignores if courier is offline).
 */
@Injectable({ providedIn: 'root' })
export class CourierLocationService {
  private readonly http = inject(HttpClient);

  private timer: ReturnType<typeof setInterval> | null = null;
  private courierId: number | null = null;
  private lastSent: { lat: number; lng: number } | null = null;
  private readonly INTERVAL_MS = 300_000; // 5 min
  private readonly MOVEMENT_THRESHOLD_M = 100;

  /** Start tracking. Call immediately after courier goes online. */
  start(courierId: number): void {
    this.courierId = courierId;
    this.lastSent = null;
    this.stopTimer();
    void this.tick(); // immediate post on going online
    this.timer = setInterval(() => void this.tick(), this.INTERVAL_MS);
  }

  /** Stop tracking. Call when courier goes offline. */
  stop(): void {
    this.stopTimer();
    this.courierId = null;
    this.lastSent = null;
  }

  private stopTimer(): void {
    if (this.timer !== null) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  async tick(): Promise<void> {
    if (this.courierId === null) return;
    const pos = await currentPosition();
    if (pos === null) return;
    if (
      this.lastSent &&
      haversineMeters(this.lastSent.lat, this.lastSent.lng, pos.lat, pos.lng) <
        this.MOVEMENT_THRESHOLD_M
    ) {
      return;
    }
    try {
      await firstValueFrom(
        this.http.patch(`/v1/couriers/${this.courierId}/location`, {
          lat: pos.lat,
          lng: pos.lng,
        }),
      );
      this.lastSent = pos;
    } catch {
      // Network blip — next tick will retry.
    }
  }
}
