import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiErrorEnvelope } from '@jaxego/core/auth/auth.models';
import {
  CourierSignupRequest,
  CourierSignupResponse,
  DocumentPresignRequest,
  DocumentPresignResponse,
  SignupResult,
} from './cadastro.models';

/**
 * CourierCadastroService — F-02 API client. NEVER stores the password; never
 * logs PII (only the error request_id). The signup error message comes straight
 * from the backend (already anti-enumeration for E2 — the frontend never infers
 * which field collided). The document byte is PUT straight to B2 with the
 * presigned URL (it does not pass through this app's backend).
 */
@Injectable({ providedIn: 'root' })
export class CourierCadastroService {
  private readonly http = inject(HttpClient);

  async signup(req: CourierSignupRequest): Promise<SignupResult> {
    try {
      const data = await firstValueFrom(
        this.http.post<CourierSignupResponse>('/v1/couriers/signup', req)
      );
      return { ok: true, data };
    } catch (err) {
      return this.mapError(err);
    }
  }

  /** Ask the backend for a presigned PUT for a document. */
  async presignDocument(
    courierId: number,
    req: DocumentPresignRequest
  ): Promise<DocumentPresignResponse | null> {
    try {
      return await firstValueFrom(
        this.http.post<DocumentPresignResponse>(
          `/v1/couriers/${courierId}/documents`,
          req
        )
      );
    } catch {
      return null;
    }
  }

  /** Upload the file straight to B2 with the presigned PUT (background). */
  async uploadToStorage(presign: DocumentPresignResponse, file: Blob): Promise<boolean> {
    try {
      await firstValueFrom(
        this.http.put(presign.presigned_url, file, { headers: presign.headers })
      );
      return true;
    } catch {
      return false; // resilience: caller retains the file + retries on reconnect
    }
  }

  /** Report the upload done → backend reprocesses + enters the review queue. */
  async completeDocument(courierId: number, documentId: number): Promise<boolean> {
    try {
      await firstValueFrom(
        this.http.post(
          `/v1/couriers/${courierId}/documents/${documentId}/complete`,
          {}
        )
      );
      return true;
    } catch {
      return false;
    }
  }

  /** Submit a MEI CNPJ; the backend sets mei_pending if inactive/incompatible. */
  async submitMei(courierId: number, cnpj: string): Promise<boolean | null> {
    try {
      const res = await firstValueFrom(
        this.http.post<{ mei_pending: boolean }>(
          `/v1/couriers/${courierId}/mei`,
          { cnpj }
        )
      );
      return res.mei_pending;
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
          message: 'Sem conexão com o servidor. Verifique sua internet e tente de novo.',
        };
      }
      const envelope = err.error as ApiErrorEnvelope | undefined;
      const code = envelope?.error?.code;
      const message = envelope?.error?.message;
      const requestId = envelope?.error?.request_id;
      if (requestId) {
        console.warn('[courier] signup failed', { code, request_id: requestId });
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

  async listTeams(areaId: number): Promise<{ id: number; name: string }[]> {
    try {
      const res = await firstValueFrom(
        this.http.get<{ items: { id: number; name: string }[] }>(`/v1/couriers/teams`, { params: { area_id: areaId } })
      );
      return res.items;
    } catch { return []; }
  }
}
