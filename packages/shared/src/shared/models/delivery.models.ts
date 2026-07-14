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
  cep?: string | null;
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
  /** Quando true, a corrida é cobrada via PIX antes de chamar entregadores. */
  platform_pix?: boolean;
  /** Valor máximo confirmado pelo usuário para o PIX (centavos). */
  pix_amount_cents?: number | null;
  /** Preço do entregador mais caro elegível (zona), sem taxas — base pra apuração de sobra/falta na finalização. */
  pix_courier_price_cents?: number | null;
  /** Saldo/crédito que a loja escolheu usar como desconto (opt-in). */
  credit_applied_cents?: number | null;
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
  /** PIX QR code EMV copia-e-cola (quando platform_pix=true). */
  pix_qr_code?: string | null;
  /** PIX QR code em base64 para exibição como imagem (quando platform_pix=true). */
  pix_qr_code_base64?: string | null;
  /** Quanto de saldo foi de fato aplicado (pode ser menor que o pedido). */
  credit_applied_cents?: number;
  /** Valor final cobrado no PIX após o desconto (null se totalmente coberto). */
  final_pix_amount_cents?: number | null;
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
  /** Dados completos do entregador — disponíveis apenas no GET /{id} (DeliveryOut). */
  courier_phone?: string | null;
  courier_vehicle_type?: string | null;
  courier_vehicle_plate?: string | null;
  courier_rating?: number | null;
  courier_rating_count?: number;
  courier_total_deliveries?: number;
  /** ISO-8601 — data em que o entregador entrou na plataforma. */
  courier_since?: string | null;
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
  pix_qr_code?: string | null;
  pix_qr_code_base64?: string | null;
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
