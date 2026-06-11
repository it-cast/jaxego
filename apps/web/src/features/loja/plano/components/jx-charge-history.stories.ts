/** Visual-regression BASELINE for jx-charge-history (UI-SPEC §14): com-dados, vazio. */
import type { ChargeHistoryItem } from '../billing.service';

export interface ChargeHistoryStory {
  state: string;
  inputs: { charges: ChargeHistoryItem[] };
}

const sample: ChargeHistoryItem[] = [
  { id: 1, kind: 'subscription', amount_cents: 9990, method: 'card', status: 'paid', transaction_id: 'tx_1', created_at: '2026-06-01T12:00:00Z' },
  { id: 2, kind: 'delivery', amount_cents: 1200, method: 'pix', status: 'open', transaction_id: null, created_at: '2026-06-05T09:00:00Z' },
];

export const chargeHistoryStories: ChargeHistoryStory[] = [
  { state: 'com-dados', inputs: { charges: sample } },
  { state: 'vazio', inputs: { charges: [] } },
];
