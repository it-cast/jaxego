/**
 * Visual-regression BASELINE para a tela 22 (UI-SPEC §Layout & estados).
 * Dados puros (sem Storybook). Capturar `api-keys-{state}-{theme}.png` light+dark.
 */

import type { ApiKey, WebhookDelivery } from './api-keys.service';

export const SAMPLE_KEYS: ApiKey[] = [
  {
    id: 1,
    key_id: 'jxg_centro',
    name: 'Integração Menu Certo',
    scopes: 'deliveries:write',
    revoked: false,
    created_at: '2026-06-01T12:00:00Z',
    last_used_at: '2026-06-10T18:30:00Z',
  },
  {
    id: 2,
    key_id: 'jxg_legado',
    name: 'Painel antigo',
    scopes: 'deliveries:write deliveries:read',
    revoked: true,
    created_at: '2026-05-02T09:00:00Z',
    last_used_at: null,
  },
];

export const SAMPLE_DELIVERIES: WebhookDelivery[] = [
  {
    id: 10,
    event_id: '01J...A',
    event_type: 'delivery.created',
    status: 'delivered',
    attempts: 1,
    last_status_code: 200,
    next_retry_at: null,
    created_at: '2026-06-10T18:31:00Z',
  },
  {
    id: 11,
    event_id: '01J...B',
    event_type: 'delivery.delivered',
    status: 'pending',
    attempts: 3,
    last_status_code: 503,
    next_retry_at: '2026-06-10T19:00:00Z',
    created_at: '2026-06-10T18:45:00Z',
  },
  {
    id: 12,
    event_id: '01J...C',
    event_type: 'delivery.canceled',
    status: 'failed',
    attempts: 8,
    last_status_code: 500,
    next_retry_at: null,
    created_at: '2026-06-09T10:00:00Z',
  },
];

export interface ApiKeysStory {
  state: string;
  description: string;
}

export const apiKeysStories: ApiKeysStory[] = [
  { state: 'lista-com-keys', description: 'Chaves ativas + revogada, badges de status.' },
  { state: 'lista-vazia', description: 'Empty state com CTA "Criar primeira chave".' },
  { state: 'criar-modal', description: 'Modal de criação (nome + escopos).' },
  {
    state: 'segredo-1x',
    description: 'Sucesso da criação: jx-secret-reveal exibe o segredo uma vez.',
  },
  {
    state: 'revogar-confirm',
    description: 'Confirmação sensível com nome+key_id e aviso < 1 min.',
  },
  {
    state: 'webhook-historico',
    description: 'Painel de webhook + histórico (entregue/pendente/falhou).',
  },
];
