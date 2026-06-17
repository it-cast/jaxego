import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiErrorEnvelope } from '@jaxego/core/auth/auth.models';
import {
  PlanDto,
  SignupRequest,
  SignupResponse,
  SignupResult,
  ViaCepResult,
} from './merchant.models';

/**
 * MerchantService — F-01 API client. NEVER stores the password; never logs PII
 * (only the error request_id for correlation). The signup error message comes
 * straight from the backend (already anti-enumeration for E2 — the frontend does
 * not infer which field collided).
 */
@Injectable({ providedIn: 'root' })
export class MerchantService {
  private readonly http = inject(HttpClient);

  async signup(req: SignupRequest): Promise<SignupResult> {
    try {
      const data = await firstValueFrom(
        this.http.post<SignupResponse>('/v1/merchants/signup', req)
      );
      return { ok: true, data };
    } catch (err) {
      return this.mapError(err);
    }
  }

  async listPlans(): Promise<PlanDto[]> {
    try {
      return await firstValueFrom(this.http.get<PlanDto[]>('/v1/plans'));
    } catch {
      return [];
    }
  }

  async confirmPhone(merchantId: number, otp: string): Promise<boolean> {
    try {
      const res = await firstValueFrom(
        this.http.post<{ confirmed: boolean }>(
          `/v1/merchants/${merchantId}/confirm-phone`,
          { otp }
        )
      );
      return res.confirmed;
    } catch {
      return false;
    }
  }

  async captureInterest(email: string, cidade: string): Promise<boolean> {
    try {
      await firstValueFrom(
        this.http.post('/v1/interest', { email, cidade, consent: true })
      );
      return true;
    } catch {
      return false;
    }
  }

  /** ViaCEP autocomplete (resilience: a failure is non-blocking). */
  async lookupCep(cep: string): Promise<ViaCepResult | null> {
    const digits = cep.replace(/\D/g, '');
    if (digits.length !== 8) return null;
    try {
      const res = await firstValueFrom(
        this.http.get<ViaCepResult>(`https://viacep.com.br/ws/${digits}/json/`)
      );
      return res.erro ? null : res;
    } catch {
      return null;
    }
  }

  private mapError(err: unknown): SignupResult {
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        return {
          ok: false,
          code: 'network',
          message:
            'Sem conexão com o servidor. Verifique sua internet e tente de novo.',
        };
      }
      const envelope = err.error as ApiErrorEnvelope | undefined;
      const code = envelope?.error?.code;
      const message = envelope?.error?.message;
      const requestId = envelope?.error?.request_id;
      if (requestId) {
        // Correlation only — never expose request_id raw, never log PII.
        console.warn('[merchant] signup failed', { code, request_id: requestId });
      }
      if (err.status >= 500) {
        return {
          ok: false,
          code: 'server',
          message: 'Tivemos um problema aqui. Já estamos vendo — tente em instantes.',
        };
      }
      return { ok: false, code, message };
    }
    return {
      ok: false,
      code: 'unknown',
      message: 'Não foi possível concluir o cadastro agora. Tente de novo.',
    };
  }
}
