/**
 * Merchant signup contracts — source of truth: apps/api/app/merchants (Phase 4).
 * Mirrors the Integration contracts in PLAN.md (request/response shapes).
 */

export type AccountType = 'cnpj' | 'cpf';
export type MerchantStatus =
  | 'pending_payment'
  | 'pending_validation'
  | 'active'
  | 'suspended';

/** POST /v1/merchants/signup request body. */
export interface SignupRequest {
  area_id: number;
  account_type: AccountType;
  document: string;
  trade_name: string;
  category: string;
  phone_e164: string;
  email: string;
  password: string;
  consent: boolean;
  address?: string;
  address_number?: string;
  address_neighborhood?: string;
  address_zip?: string;
  address_state?: string;
  plan_code?: string;
}

/** POST /v1/merchants/signup response (201). */
export interface SignupResponse {
  merchant_id: number;
  status: MerchantStatus;
  next_step: 'confirm' | 'done';
}

/** A plan from GET /v1/plans (values from SEED — DRV-009). */
export interface PlanDto {
  id: number;
  codename: string;
  nome: string;
  preco_cents: number;
  entregas_mes: number;
  taxa_entrega_cents: number;
  is_free: boolean;
  is_unlimited: boolean;
}

/** POST /v1/payments/assinar request body. */
export interface SubscribeRequest {
  plan_id: number;
  cycle: 'mensal' | 'anual';
  method: 'card' | 'pix';
  card_blob?: string;
  pix_recorrente?: boolean;
}

/** POST /v1/payments/assinar response (SubscriptionOut). */
export interface SubscribeResponse {
  subscription_id: number;
  billing_status: string;
  payment_method: string | null;
  plan_id: number;
  amount_cents: number;
  next_due_at: string | null;
  qr_code: string | null;
  qr_code_base64: string | null;
}

export interface SubscribeResult {
  ok: boolean;
  code?: string;
  message?: string;
  data?: SubscribeResponse;
}

/** Public active area from GET /v1/areas/public. */
export interface AreaOption {
  id: number;
  name: string;
  kyc_level?: string;
}

/** Machine error codes the signup flow reacts to (app/merchants/service.py). */
export const MERCHANT_ERROR = {
  DUPLICATE: 'duplicate_account', // E2 — anti-enumeration (generic message)
  CNPJ_INATIVO: 'cnpj_inativo', // E1
  AREA_NOT_COVERED: 'area_not_covered', // empty state
  DOC_INVALID: 'documento_invalido',
  RATE_LIMITED: 'rate_limited',
} as const;

/** Result of a signup attempt, mapped to UI-relevant kinds. */
export interface SignupResult {
  ok: boolean;
  code?: string;
  message?: string;
  data?: SignupResponse;
}

/** ViaCEP lookup result (subset we use). */
export interface ViaCepResult {
  logradouro?: string;
  bairro?: string;
  localidade?: string;
  uf?: string;
  erro?: boolean;
}
