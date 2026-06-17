/**
 * Auth contracts consumed from Phase 2 (`apps/api/app/auth`).
 * Source of truth: TokenPair schema + RFC-7807-like error envelope.
 */

/** POST /v1/auth/login response (200). */
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string; // "bearer"
  expires_in: number; // access token lifetime, seconds
}

/** Standard error envelope: { error: { code, message, request_id } }. */
export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    request_id: string | null;
  };
}

/**
 * Login request body. NOTE: the backend field is `totp` (not `totp_code`) —
 * see app/auth/schemas.py LoginBody. The UI-SPEC §5.5 text said `totp_code`;
 * we follow the real API contract.
 */
export interface LoginRequest {
  email: string;
  password: string;
  totp?: string;
}

/** Machine error codes the auth flow reacts to (app/auth/service.py + dependencies.py). */
export const ERROR_CODE = {
  TOTP_REQUIRED: 'totp_required',
  TOTP_ENROLLMENT_REQUIRED: 'totp_enrollment_required',
  INVALID_CREDENTIALS: 'invalid_credentials',
  ACCOUNT_LOCKED: 'account_locked',
} as const;

export type LoginErrorKind =
  | 'credentials'
  | 'totp_required'
  | 'locked'
  | 'network'
  | 'server'
  | 'unknown';

/** Surface the authenticated user belongs to (post-login routing, R0.4). */
export type Surface = 'entregador' | 'loja' | 'admin' | 'plataforma' | 'none';

/** GET /v1/auth/me response (app/auth/schemas.py MeResponse). */
export interface Me {
  user_id: number;
  surface: Surface;
  area_id: number | null;
  courier_id: number | null;
  merchant_id: number | null;
  status: string | null;
}
