/** Pool contracts (unanswered deliveries). Mirrors the backend `PoolItemOut`. */
export interface PoolItemOut {
  delivery_id: number;
  loja_nome: string;
  pickup_address: string;
  pickup_neighborhood: string | null;
  dropoff_address: string;
  dropoff_number: string | null;
  dropoff_neighborhood: string;
  distance_m: number | null;
  value_cents: number | null;
  payment_method: string;
  receipt_method: string | null;
  created_at: string;
}

export interface PoolAcceptResponse {
  delivery_id: number;
  state: string;
}

/** Terminal results of a self-assign attempt — same shape as an offer accept. */
export type PoolAcceptResult = 'won' | 'lost' | 'error' | 'gps_missing';
