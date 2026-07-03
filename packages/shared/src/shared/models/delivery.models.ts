/** Delivery API DTOs (Phase 7 — F-03). Mirror the backend schemas. */

import type { DeliveryState } from '../components/state-badge/state-badge.component';

export type DeliveryPaymentMethod = 'direct' | 'card' | 'pix';
export type DeliveryProofMethod = 'none' | 'photo' | 'photo_reference' | 'otp';

export interface CreateDeliveryRequest {
  pickup_address: string;
  pickup_neighborhood?: string | null;
  dropoff_neighborhood_id: number;
  dropoff_address: string;
  dropoff_number?: string | null;
  dropoff_complement?: string | null;
  dropoff_reference?: string | null;
  distance_m?: number | null;
  recipient_name: string;
  recipient_phone_e164: string;
  recipient_email?: string | null;
  recipient_cpf?: string | null;
  items_description?: string | null;
  items_quantity: number;
  declared_value_cents?: number | null;
  // Pacote (MG-1) — peso em gramas, dimensões em cm. Opcionais.
  weight_g?: number | null;
  length_cm?: number | null;
  width_cm?: number | null;
  height_cm?: number | null;
  reference_number?: string | null;
  notes?: string | null;
  team_ids: number[];
  proof_method: DeliveryProofMethod;
  payment_method?: DeliveryPaymentMethod;
  receipt_method?: string | null;
  card_blob?: string | null;
  payer_document?: string | null;
  payer_email?: string | null;
  /** ISO-8601 UTC — quando o entregador deve ser chamado. Null = imediato. */
  scheduled_at?: string | null;
}

export interface CreateDeliveryResponse {
  delivery_id: number;
  public_token: string;
  state: DeliveryState;
  price_cents: number | null;
  fee_cents: number;
  no_couriers_warning: boolean;
  /** ISO-8601 UTC do horário agendado; presente quando state === 'AGENDADA'. */
  scheduled_at?: string | null;
}

export interface DeliveryListItem {
  id: number;
  public_token: string;
  state: DeliveryState;
  payment_method: DeliveryPaymentMethod;
  dropoff_neighborhood_id: number;
  price_cents: number | null;
  fee_cents: number;
  reference_number: string | null;
  recipient_name: string | null;
  /** Already masked by the backend (TH-04) — never the raw phone. */
  recipient_phone_masked: string | null;
  courier_id: number | null;
  courier_name: string | null;
  created_at: string | null;
  scheduled_at?: string | null;
  /** Coordenadas do destino (detalhe) — usadas para o mapa. */
  dropoff_lat?: number | null;
  dropoff_lng?: number | null;
  /** Pacote (MG-1) — peso (g) + dimensões (cm). */
  weight_g?: number | null;
  length_cm?: number | null;
  width_cm?: number | null;
  height_cm?: number | null;
  /** Telefone completo (E.164) — disponível apenas no GET /{id}, nunca na lista. */
  recipient_phone?: string | null;
  /** Campos completos — disponíveis apenas no GET /{id} (DeliveryOut), não na lista. */
  dropoff_address?: string | null;
  dropoff_number?: string | null;
  dropoff_complement?: string | null;
  dropoff_reference?: string | null;
  dropoff_neighborhood_name?: string | null;
  pickup_address?: string | null;
  pickup_neighborhood?: string | null;
  items_description?: string | null;
  items_quantity?: number;
  notes?: string | null;
  team_names?: string[];
  has_image?: boolean;
  proof_method?: string;
}

export interface DeliveryListResponse {
  items: DeliveryListItem[];
  total: number;
  limit: number;
  offset: number;
}

/** Upgrade payload surfaced by the 402 plan-limit error (RN-028 / D-07). */
export interface PlanLimitError {
  code: 'plan_limit_reached';
  message: string;
}
