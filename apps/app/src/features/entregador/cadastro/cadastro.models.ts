/** Contracts for the courier onboarding wizard (mirrors apps/api couriers schemas). */

export type KycLevel = 'simples' | 'completa';
export type VehicleType = 'moto' | 'bicicleta' | 'carro' | 'a_pe';

export type BankAccountType = 'CC' | 'PP';

export interface CourierSignupRequest {
  area_id: number;
  cpf: string;
  full_name: string;
  phone_e164: string;
  email: string;
  password: string;
  vehicle_type: VehicleType;
  vehicle_plate?: string | null;
  team_id: number;
  consent: boolean;
  birth_date?: string | null;
  zip_code?: string | null;
  street?: string | null;
  street_number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  bank_code?: string | null;
  bank_agency?: string | null;
  bank_account?: string | null;
  bank_account_digit?: string | null;
  bank_account_type?: BankAccountType | null;
}

export interface CourierSignupResponse {
  courier_id: number;
  status: 'pending_kyc' | 'active' | 'suspended' | 'banned';
  kyc_level: KycLevel;
  next_step: 'selfie' | 'documents' | 'done';
}

export interface DocumentPresignRequest {
  kind: 'selfie' | 'cnh' | 'crlv' | 'mei' | 'antecedentes';
  sha256_client: string;
  content_type: 'image/jpeg' | 'image/png' | 'image/webp';
}

export interface DocumentPresignResponse {
  document_id: number;
  presigned_url: string;
  method: 'PUT';
  expires_in: number;
  headers: Record<string, string>;
}

export interface SignupResult {
  ok: boolean;
  data?: CourierSignupResponse;
  code?: string;
  message?: string;
}

export const COURIER_ERROR = {
  EXISTS: 'courier_exists',
  INVALID_CPF: 'cpf_invalido',
  AREA_NOT_FOUND: 'area_not_found',
} as const;
