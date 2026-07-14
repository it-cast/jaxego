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
export interface CourierScore {
  avg_stars: number;
  total_ratings: number;
}

export interface RatingItem {
  id: number;
  stars: number;
  comment: string | null;
  merchant_name: string | null;
  created_at: string | null;
}

export interface AvailabilityResult {
  is_online: boolean;
  busy: boolean;
  online_until: string | null;
}

export interface CourierDocumentItem {
  id: number;
  kind: string;
  status: string;
  reject_reason: string | null;
  reject_detail: string | null;
}

export interface CourierProfile {
  online_until: string | null;
  id: number;
  full_name: string;
  cpf_masked: string;
  phone_masked: string;
  email_masked: string;
  vehicle_type: string;
  vehicle_plate: string | null;
  kyc_level: string;
  status: string;
  is_online: boolean;
  mei_pending: boolean;
  team_id: number | null;
  team_name: string | null;
  documents: CourierDocumentItem[];
}

export interface CourierDelivery {
  id: number;
  public_token: string;
  state: string;
  payment_method: string;
  proof_method: string;
  has_image: boolean;
  merchant_trade_name: string | null;
  courier_collection_method: string | null;
  receipt_method: string | null;
  notes: string | null;
  pickup_address: string;
  pickup_neighborhood: string | null;
  pickup_lat: number | null;
  pickup_lng: number | null;
  dropoff_neighborhood_id: number;
  distance_m: number | null;
  dropoff_address: string | null;
  dropoff_number: string | null;
  dropoff_complement: string | null;
  dropoff_reference: string | null;
  dropoff_neighborhood_name: string | null;
  dropoff_lat: number | null;
  dropoff_lng: number | null;
  recipient_name: string | null;
  recipient_phone_masked: string | null;
  recipient_phone: string | null;
  price_cents: number | null;
  fee_cents: number;
  reference_number: string | null;
  items_description: string | null;
  items_quantity: number;
  weight_g: number | null;
  length_cm: number | null;
  width_cm: number | null;
  height_cm: number | null;
  created_at: string | null;
}

export interface CourierDeliveryListItem {
  id: number;
  public_token: string;
  state: string;
  payment_method: string;
  pickup_address: string | null;
  dropoff_address: string | null;
  dropoff_number: string | null;
  dropoff_neighborhood_id: number;
  distance_m: number | null;
  price_cents: number | null;
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

  async setAvailability(courierId: number, online: boolean, onlineUntil?: string): Promise<AvailabilityResult> {
    return firstValueFrom(
      this.http.patch<AvailabilityResult>(
        `/v1/couriers/${courierId}/availability`,
        { online, online_until: onlineUntil ?? null }
      )
    );
  }

  /** The courier's own profile (identity + documents, PII masked) — F1.6. */
  async profile(courierId: number): Promise<CourierProfile | null> {
    try {
      return await firstValueFrom(
        this.http.get<CourierProfile>(`/v1/couriers/${courierId}/profile`)
      );
    } catch {
      return null;
    }
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

  /** All of the courier's in-progress deliveries (ACEITA/COLETADA), newest first. */
  async activeDeliveries(courierId: number): Promise<CourierDelivery[]> {
    return firstValueFrom(
      this.http.get<CourierDelivery[]>(
        `/v1/couriers/${courierId}/deliveries/active-list`
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

  async finalizeNoProof(courierId: number, deliveryId: number, lat: number, lng: number): Promise<void> {
    await firstValueFrom(
      this.http.post(`/v1/couriers/${courierId}/deliveries/${deliveryId}/finalize-no-proof`, { lat, lng }),
    );
  }

  /** Log 'chegou ao destino' — audit only, no state change (CORRECAO-252). */
  async markArrived(courierId: number, deliveryId: number, lat: number, lng: number): Promise<void> {
    await firstValueFrom(
      this.http.post(`/v1/couriers/${courierId}/deliveries/${deliveryId}/arrived`, { lat, lng }),
    );
  }

  async deliveryImageUrl(courierId: number, deliveryId: number): Promise<string | null> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ url: string }>(`/v1/couriers/${courierId}/deliveries/${deliveryId}/image`)
      );
      return res.url;
    } catch { return null; }
  }

  async markCollected(courierId: number, deliveryId: number, lat: number, lng: number): Promise<void> {
    await firstValueFrom(
      this.http.post(`/v1/couriers/${courierId}/deliveries/${deliveryId}/collect`, { lat, lng }),
    );
  }

  async updateProfile(courierId: number, data: { full_name?: string; password?: string; current_password?: string }): Promise<boolean> {
    try {
      await firstValueFrom(this.http.patch(`/v1/couriers/${courierId}/profile`, data));
      return true;
    } catch { return false; }
  }

  async listRatings(courierId: number, limit = 10, offset = 0): Promise<{ items: RatingItem[]; total: number }> {
    try {
      return await firstValueFrom(
        this.http.get<{ items: RatingItem[]; total: number }>(
          `/v1/couriers/${courierId}/ratings`, { params: { limit, offset } }
        )
      );
    } catch { return { items: [], total: 0 }; }
  }

  async listDeliveries(courierId: number): Promise<CourierDeliveryList> {
    return firstValueFrom(
      this.http.get<CourierDeliveryList>(`/v1/couriers/${courierId}/deliveries`)
    );
  }

  async coverageCount(courierId: number): Promise<number> {
    try {
      const rows = await firstValueFrom(
        this.http.get<{ neighborhood_id: number }[]>(`/v1/couriers/${courierId}/coverage`)
      );
      return rows.length;
    } catch { return 0; }
  }
}
