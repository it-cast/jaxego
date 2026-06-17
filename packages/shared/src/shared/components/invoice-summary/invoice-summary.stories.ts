/**
 * Visual-regression BASELINE for jx-invoice-summary (UI-SPEC §15). Plain data.
 * Captures open / overdue / paid × {light, dark}.
 */

import type { InvoiceSummary } from './invoice-summary.component';

export interface InvoiceSummaryStory {
  state: string;
  inputs: { invoice: InvoiceSummary; paying: boolean };
}

export const invoiceSummaryStories: InvoiceSummaryStory[] = [
  {
    state: 'open',
    inputs: {
      invoice: {
        id: 1,
        competence: '2026-05',
        amount_cents: 24500,
        status: 'open',
        due_at: '2026-06-10T00:00:00Z',
      },
      paying: false,
    },
  },
  {
    state: 'overdue',
    inputs: {
      invoice: {
        id: 2,
        competence: '2026-04',
        amount_cents: 18900,
        status: 'overdue',
        due_at: '2026-05-10T00:00:00Z',
      },
      paying: false,
    },
  },
  {
    state: 'paid',
    inputs: {
      invoice: {
        id: 3,
        competence: '2026-03',
        amount_cents: 31200,
        status: 'paid',
        due_at: '2026-04-10T00:00:00Z',
        paid_at: '2026-04-02T12:00:00Z',
      },
      paying: false,
    },
  },
  {
    state: 'open-paying',
    inputs: {
      invoice: {
        id: 4,
        competence: '2026-05',
        amount_cents: 24500,
        status: 'open',
        due_at: '2026-06-10T00:00:00Z',
      },
      paying: true,
    },
  },
];
