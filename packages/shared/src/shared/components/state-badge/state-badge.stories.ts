/**
 * Visual-regression BASELINE for jx-state-badge (UI-SPEC §8). Plain data.
 * Captures all 7 states × {list, dashboard} × {light, dark}.
 */

import type { DeliveryState, StateBadgeVariant } from './state-badge.component';

const STATES: DeliveryState[] = [
  'CRIADA',
  'ACEITA',
  'COLETADA',
  'ENTREGUE',
  'RECUSADA_NO_DESTINO',
  'CANCELADA',
  'FINALIZADA',
];

export interface StateBadgeStory {
  state: string;
  inputs: { state: DeliveryState; variant: StateBadgeVariant };
}

export const stateBadgeStories: StateBadgeStory[] = [
  ...STATES.map((s): StateBadgeStory => ({
    state: `list-${s.toLowerCase()}`,
    inputs: { state: s, variant: 'list' },
  })),
  ...STATES.map((s): StateBadgeStory => ({
    state: `dashboard-${s.toLowerCase()}`,
    inputs: { state: s, variant: 'dashboard' },
  })),
];
