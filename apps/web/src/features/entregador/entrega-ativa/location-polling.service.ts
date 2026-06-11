import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/** Great-circle distance in metres (movement filter — A5). */
export function haversineMeters(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const R = 6_371_000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dPhi = toRad(lat2 - lat1);
  const dLambda = toRad(lng2 - lng1);
  const a =
    Math.sin(dPhi / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLambda / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

/**
 * LocationPollingService — resilient courier position polling (DEC-002 / A5).
 *
 * Posts `POST /v1/deliveries/{id}/locations` every `intervalMs` (default 60s) WHILE
 * the delivery is in the moving window. Resilience (offline-first / push skill):
 * - PAUSES when the page/app is hidden (Page Visibility) — M1 tracks only with the
 *   screen open (degradação consciente → TD-020); resumes on visibility.
 * - PAUSES when offline; resumes on `online`.
 * - 50m MOVEMENT FILTER: a sample <50m from the last SENT position is skipped (saves
 *   battery + keeps delivery_locations from filling with near-duplicates — Pitfall 5).
 *
 * The service owns no UI; a page starts/stops it for the active delivery only.
 */
@Injectable({ providedIn: 'root' })
export class LocationPollingService {
  private readonly http = inject(HttpClient);

  private timer: ReturnType<typeof setInterval> | null = null;
  private deliveryId: number | null = null;
  private intervalMs = 60_000;
  private lastSent: { lat: number; lng: number } | null = null;
  private readonly MOVEMENT_THRESHOLD_M = 50;

  private readonly onVisibility = () => this.syncRunning();
  private readonly onOnline = () => this.syncRunning();
  private readonly onOffline = () => this.stopTimer();

  /** Begin polling for the given delivery (idempotent). */
  start(deliveryId: number, intervalMs = 60_000): void {
    this.deliveryId = deliveryId;
    this.intervalMs = Math.min(Math.max(intervalMs, 60_000), 120_000);
    this.lastSent = null;
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', this.onVisibility);
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.onOnline);
      window.addEventListener('offline', this.onOffline);
    }
    this.syncRunning();
  }

  /** Stop polling and detach listeners. */
  stop(): void {
    this.stopTimer();
    this.deliveryId = null;
    this.lastSent = null;
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', this.onVisibility);
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.onOnline);
      window.removeEventListener('offline', this.onOffline);
    }
  }

  /** Whether the timer is currently active (testable). */
  get running(): boolean {
    return this.timer !== null;
  }

  /** True only when visible AND online (the conditions to poll). */
  private shouldRun(): boolean {
    const visible = typeof document === 'undefined' || document.visibilityState !== 'hidden';
    const online = typeof navigator === 'undefined' || navigator.onLine;
    return this.deliveryId !== null && visible && online;
  }

  private syncRunning(): void {
    if (this.shouldRun()) {
      this.startTimer();
    } else {
      this.stopTimer();
    }
  }

  private startTimer(): void {
    if (this.timer !== null) return;
    void this.tick(); // immediate first sample
    this.timer = setInterval(() => void this.tick(), this.intervalMs);
  }

  private stopTimer(): void {
    if (this.timer !== null) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  /** One poll cycle: read GPS, apply the 50m filter, POST. Best-effort. */
  async tick(): Promise<void> {
    if (this.deliveryId === null) return;
    const pos = await this.currentPosition();
    if (pos === null) return;
    if (
      this.lastSent &&
      haversineMeters(this.lastSent.lat, this.lastSent.lng, pos.lat, pos.lng) <
        this.MOVEMENT_THRESHOLD_M
    ) {
      return; // moved <50m — skip (battery + noise filter)
    }
    try {
      await firstValueFrom(
        this.http.post(`/v1/deliveries/${this.deliveryId}/locations`, {
          lat: pos.lat,
          lng: pos.lng,
        }),
      );
      this.lastSent = pos;
    } catch {
      // A 409 (out of window) or a network blip must not crash the loop — degrade.
    }
  }

  private currentPosition(): Promise<{ lat: number; lng: number } | null> {
    return new Promise((resolve) => {
      if (typeof navigator === 'undefined' || !navigator.geolocation) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
        () => resolve(null),
        { enableHighAccuracy: true, timeout: 8000 },
      );
    });
  }
}
