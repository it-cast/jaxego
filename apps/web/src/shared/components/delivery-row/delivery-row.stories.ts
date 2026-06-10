/**
 * Visual-regression BASELINE for jx-delivery-row (UI-SPEC §8). Plain data.
 * Captures: CRIADA (with cancel action), no courier (—), entregue, cancelada.
 */

import type { DeliveryListItem } from '../../../features/loja/entregas/delivery.models';

function row(over: Partial<DeliveryListItem>): DeliveryListItem {
  return {
    id: 1,
    public_token: 'AB12CD34EF56',
    state: 'CRIADA',
    payment_method: 'direct',
    dropoff_neighborhood_id: 1,
    estimate_min_cents: 1000,
    estimate_max_cents: 1000,
    fee_cents: 150,
    reference_number: 'PED-123',
    recipient_name: 'Maria Cliente',
    recipient_phone_masked: '+5522 9••••-7777',
    courier_id: null,
    created_at: '2026-06-10T14:30:00Z',
    ...over,
  };
}

export interface DeliveryRowStory {
  state: string;
  inputs: { delivery: DeliveryListItem };
}

export const deliveryRowStories: DeliveryRowStory[] = [
  { state: 'criada', inputs: { delivery: row({ state: 'CRIADA' }) } },
  { state: 'sem-frete', inputs: { delivery: row({ estimate_min_cents: null }) } },
  { state: 'entregue', inputs: { delivery: row({ state: 'ENTREGUE', courier_id: 9 }) } },
  { state: 'cancelada', inputs: { delivery: row({ state: 'CANCELADA' }) } },
];
