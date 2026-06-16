import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/**
 * EntregadorService — courier-scoped reads/writes (MR-1). Mirrors:
 *  - PATCH /v1/couriers/{id}/availability      (REQ-018)
 *  - GET   /v1/couriers/{id}/score             (ADR-013, 404 if no snapshot)
 *  - GET   /v1/couriers/{id}/deliveries/active (F1.0 — null when idle)
 *  - GET   /v1/couriers/{id}/deliveries/{id}
 *  - GET   /v1/couriers/{id}/deliveries        (history)
 *
 * `courierId` comes from AuthService.me(). Money is INTEGER cents (DRV-009);
 * destination PII (full address/recipient) is only present AFTER pickup (RN-013).
 */
export interface ScoreComponent {
  component: string;
  raw: number;
  weight: number;
  contribution: number;
}

export interface CourierScore {
  courier_id: number;
  snapshot_date: string;
  total_score: number;
  level: string;
  components: ScoreComponent[];
}

export interface AvailabilityResult {
  is_online: boolean;
  busy: boolean;
}

export interface CourierDelivery {
  id: number;
  public_token: string;
  state: string;
  payment_method: string;
  proof_method: string;
  pickup_address: string;
  pickup_neighborhood: string | null;
  pickup_lat: number | null;
  pickup_lng: number | null;
  dropoff_neighborhood_id: number;
  distance_m: number | null;
  dropoff_address: string | null;
  dropoff_number: string | null;
  dropoff_complement: string | null;
  dropoff_lat: number | null;
  dropoff_lng: number | null;
  recipient_name: string | null;
  recipient_phone_masked: string | null;
  estimate_min_cents: number | null;
  estimate_max_cents: number | null;
  fee_cents: number;
  reference_number: string | null;
  items_description: string | null;
  items_quantity: number;
  created_at: string | null;
}

export interface CourierDeliveryListItem {
  id: number;
  public_token: string;
  state: string;
  payment_method: string;
  dropoff_neighborhood_id: number;
  distance_m: number | null;
  estimate_min_cents: number | null;
  estimate_max_cents: number | null;
  fee_cents: number;
  created_at: string | null;
}

export interface CourierDeliveryList {
  items: CourierDeliveryListItem[];
  total: number;
  limit: number;
  offset: number;
}

@Injectable({ providedIn: 'root' })
export class EntregadorService {
  private readonly http = inject(HttpClient);

  async setAvailability(courierId: number, online: boolean): Promise<AvailabilityResult> {
    return firstValueFrom(
      this.http.patch<AvailabilityResult>(
        `/v1/couriers/${courierId}/availability`,
        { online }
      )
    );
  }

  /** Latest score snapshot; null when none has been computed yet (404). */
  async score(courierId: number): Promise<CourierScore | null> {
    try {
      return await firstValueFrom(
        this.http.get<CourierScore>(`/v1/couriers/${courierId}/score`)
      );
    } catch {
      return null;
    }
  }

  /** The courier's in-progress delivery (ACEITA/COLETADA), or null when idle. */
  async activeDelivery(courierId: number): Promise<CourierDelivery | null> {
    return firstValueFrom(
      this.http.get<CourierDelivery | null>(
        `/v1/couriers/${courierId}/deliveries/active`
      )
    );
  }

  async getDelivery(courierId: number, deliveryId: number): Promise<CourierDelivery> {
    return firstValueFrom(
      this.http.get<CourierDelivery>(
        `/v1/couriers/${courierId}/deliveries/${deliveryId}`
      )
    );
  }

  async listDeliveries(courierId: number): Promise<CourierDeliveryList> {
    return firstValueFrom(
      this.http.get<CourierDeliveryList>(`/v1/couriers/${courierId}/deliveries`)
    );
  }
}
