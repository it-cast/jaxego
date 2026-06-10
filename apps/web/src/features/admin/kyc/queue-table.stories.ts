/**
 * Visual-regression BASELINE for jx-kyc-queue-table (UI-SPEC §10). Plain data
 * (no Storybook). Captured `jx-kyc-queue-table-{state}-{theme}.png` light+dark.
 */

import type { KycQueueRow } from './queue-table.component';

const ROWS: KycQueueRow[] = [
  {
    courierId: 'cou_8f3a',
    courierName: 'João da Silva',
    level: 'completa',
    approvedCount: 2,
    totalCount: 4,
    waitingHours: 5,
  },
  {
    courierId: 'cou_2b71',
    courierName: 'Maria Souza',
    level: 'simples',
    approvedCount: 0,
    totalCount: 1,
    waitingHours: 53,
  },
];

export interface QueueStory {
  state: string;
  inputs: { rows: KycQueueRow[]; loading?: boolean; showArea?: boolean };
}

export const queueStories: QueueStory[] = [
  { state: 'com-fila', inputs: { rows: ROWS } },
  { state: 'fila-vazia', inputs: { rows: [] } },
  {
    state: 'item-escalado-48h',
    inputs: { rows: [ROWS[1]] },
  },
  { state: 'loading', inputs: { rows: [], loading: true } },
];

export const themes = ['light', 'dark'] as const;
