/**
 * Visual-regression BASELINE for the delivery list (tela 14, UI-SPEC §8).
 * States: com-entregas, filtro-sem-resultado (empty), sem-nenhuma (empty+CTA),
 * loading, erro · light+dark. Plain data (no Storybook runtime).
 */

import type { DeliveryListItem } from './delivery.models';

const ROWS: DeliveryListItem[] = [
  {
    id: 1,
    public_token: 'AB12CD34EF56',
    state: 'CRIADA',
    payment_method: 'direct',
    dropoff_neighborhood_id: 1,
    estimate_min_cents: 1000,
    estimate_max_cents: 1000,
    fee_cents: 150,
    reference_number: 'PED-1',
    recipient_name: 'Maria Cliente',
    recipient_phone_masked: '+5522 9••••-7777',
    courier_id: null,
    created_at: '2026-06-10T14:30:00Z',
  },
  {
    id: 2,
    public_token: 'GH78IJ90KL12',
    state: 'CANCELADA',
    payment_method: 'direct',
    dropoff_neighborhood_id: 2,
    estimate_min_cents: null,
    estimate_max_cents: null,
    fee_cents: 0,
    reference_number: null,
    recipient_name: 'João Souza',
    recipient_phone_masked: '+5522 9••••-1234',
    courier_id: null,
    created_at: '2026-06-09T11:05:00Z',
  },
];

export interface EntregasListStory {
  state: string;
  rows: DeliveryListItem[];
  tableState: 'ready' | 'empty' | 'loading' | 'error';
  hasFilters?: boolean;
}

export const entregasListStories: EntregasListStory[] = [
  { state: 'com-entregas', rows: ROWS, tableState: 'ready' },
  { state: 'sem-nenhuma', rows: [], tableState: 'empty', hasFilters: false },
  { state: 'filtro-sem-resultado', rows: [], tableState: 'empty', hasFilters: true },
  { state: 'loading', rows: [], tableState: 'loading' },
  { state: 'erro', rows: [], tableState: 'error' },
];
