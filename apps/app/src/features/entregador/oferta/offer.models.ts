/**
 * Offer contracts (Phase 8 — F-05). Mirrors the backend `OfferOut` (RN-013): the
 * destination is ONLY neighborhood + distance — there is NO street/number field
 * here by construction. The timer comes from the server (ADR-104).
 */
export interface OfferOut {
  delivery_id: number;
  loja_nome: string;
  pickup_address: string;
  pickup_neighborhood: string | null;
  dropoff_address: string | null;
  dropoff_number: string | null;
  dropoff_neighborhood: string;
  distance_m: number | null;
  value_cents: number | null;
  payment_method: string;
  receipt_method: string | null;
  eta_s: number | null;
  eta_degraded: boolean;
  /** Redis TTL — the source of truth of the timer (ADR-104). */
  ttl_total_s: number;
  ttl_remaining_s: number;
}

export interface AcceptResponse {
  delivery_id: number;
  state: string;
}

/** Terminal results of an accept attempt (UI-SPEC §3.5). */
export type OfferResult = 'won' | 'lost' | 'expired' | 'error';
