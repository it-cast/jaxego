import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

/**
 * Contratos da tela 22 — espelham `apps/api/app/api_keys/schemas.py` e
 * `apps/api/app/webhooks/schemas.py` (D-10). O SEGREDO da chave só chega na
 * resposta de criação (`CreateApiKeyResponse.secret`); nunca em `ApiKeyOut`.
 */

/** Uma chave de API (sem segredo) — lista/detalhe (TH-09: nunca vaza o hash). */
export interface ApiKey {
  id: number;
  key_id: string;
  name: string;
  /** Escopos separados por espaço (ex.: "deliveries:write"). */
  scopes: string;
  revoked: boolean;
  created_at: string | null;
  last_used_at: string | null;
}

export interface ApiKeyList {
  items: ApiKey[];
  total: number;
}

/** Resposta de criação — o segredo completo `jxg_...` chega UMA vez (D-01). */
export interface ApiKeyCreated {
  id: number;
  key_id: string;
  name: string;
  scopes: string;
  secret: string;
}

/** Endpoint de webhook configurado (URL + secret próprio + eventos). */
export interface WebhookEndpoint {
  id: number;
  url: string;
  secret: string;
  events: string;
  enabled: boolean;
  created_at: string | null;
}

/** Uma linha do histórico de entregas de webhook (status/tentativa/retry). */
export interface WebhookDelivery {
  id: number;
  event_id: string;
  event_type: string;
  status: 'pending' | 'delivered' | 'failed';
  attempts: number;
  last_status_code: number | null;
  next_retry_at: string | null;
  created_at: string | null;
}

export interface WebhookDeliveryList {
  items: WebhookDelivery[];
  total: number;
}

/** Escopos aceitos pelo backend (ALLOWED_SCOPES). */
export const API_KEY_SCOPES = ['deliveries:write', 'deliveries:read'] as const;
export type ApiKeyScope = (typeof API_KEY_SCOPES)[number];

/** Eventos de webhook suportados (WEBHOOK_EVENTS — backend). */
export const WEBHOOK_EVENTS = [
  'delivery.created',
  'delivery.accepted',
  'delivery.collected',
  'delivery.delivered',
  'delivery.finalized',
  'delivery.canceled',
] as const;
export type WebhookEvent = (typeof WEBHOOK_EVENTS)[number];

export interface ConfigureWebhookBody {
  url: string;
  events: string[];
  enabled: boolean;
  rotate_secret: boolean;
}

/**
 * AdminApiKeysService — gerência de chaves de API e webhook da área (tela 22).
 *
 * Rotas: `/v1/admin/areas/{area_id}/api-keys` e `/.../webhook` (+ `/deliveries`).
 * O segredo da chave volta só na criação; a UI o exibe 1× via jx-secret-reveal.
 */
@Injectable({ providedIn: 'root' })
export class AdminApiKeysService {
  private readonly http = inject(HttpClient);

  private base(areaId: number): string {
    return `/v1/admin/areas/${areaId}`;
  }

  // --- API keys -------------------------------------------------------------
  async listKeys(areaId: number, limit = 20, offset = 0): Promise<ApiKeyList> {
    return firstValueFrom(
      this.http.get<ApiKeyList>(`${this.base(areaId)}/api-keys`, {
        params: { limit, offset },
      }),
    );
  }

  async createKey(
    areaId: number,
    name: string,
    scopes: string[],
  ): Promise<ApiKeyCreated> {
    return firstValueFrom(
      this.http.post<ApiKeyCreated>(`${this.base(areaId)}/api-keys`, {
        name,
        scopes,
      }),
    );
  }

  async revokeKey(areaId: number, keyPk: number): Promise<ApiKey> {
    return firstValueFrom(
      this.http.delete<ApiKey>(`${this.base(areaId)}/api-keys/${keyPk}`),
    );
  }

  // --- Webhook --------------------------------------------------------------
  async getWebhook(areaId: number): Promise<WebhookEndpoint | null> {
    return firstValueFrom(
      this.http.get<WebhookEndpoint | null>(`${this.base(areaId)}/webhook`),
    );
  }

  async configureWebhook(
    areaId: number,
    body: ConfigureWebhookBody,
  ): Promise<WebhookEndpoint> {
    return firstValueFrom(
      this.http.put<WebhookEndpoint>(`${this.base(areaId)}/webhook`, body),
    );
  }

  async listDeliveries(
    areaId: number,
    limit = 20,
    offset = 0,
  ): Promise<WebhookDeliveryList> {
    return firstValueFrom(
      this.http.get<WebhookDeliveryList>(
        `${this.base(areaId)}/webhook/deliveries`,
        { params: { limit, offset } },
      ),
    );
  }
}
