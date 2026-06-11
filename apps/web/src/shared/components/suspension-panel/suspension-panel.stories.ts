/**
 * Visual-regression BASELINE for jx-suspension-panel (UI-SPEC §Tela 25/09).
 * Plain data. Captures open / at-risk / overdue / reverted / upheld in {light, dark}.
 */

import type { SuspensionAppeal } from './suspension-panel.component';

function appeal(overrides: Partial<SuspensionAppeal>): SuspensionAppeal {
  return {
    id: 1,
    subject_type: 'courier',
    subject_id: 10,
    reason: 'Reclamações recorrentes de atraso na coleta.',
    opened_at: '2026-06-10T12:00:00Z',
    sla_due_at: '2026-06-13T12:00:00Z',
    decision: null,
    decided_at: null,
    reverted_at: null,
    ...overrides,
  };
}

export interface SuspensionPanelStory {
  state: string;
  inputs: { appeal: SuspensionAppeal; busy: boolean };
}

export const suspensionPanelStories: SuspensionPanelStory[] = [
  {
    state: 'aberta',
    inputs: { appeal: appeal({}), busy: false },
  },
  {
    state: 'lojista-aberta',
    inputs: {
      appeal: appeal({ subject_type: 'merchant', reason: 'Pagamentos contestados.' }),
      busy: false,
    },
  },
  {
    state: 'revertida',
    inputs: {
      appeal: appeal({ reverted_at: '2026-06-13T12:00:00Z' }),
      busy: false,
    },
  },
  {
    state: 'mantida',
    inputs: {
      appeal: appeal({ decision: 'upheld', decided_at: '2026-06-12T09:00:00Z' }),
      busy: false,
    },
  },
];
