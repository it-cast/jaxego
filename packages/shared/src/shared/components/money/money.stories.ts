/**
 * Visual-regression BASELINE for jx-money (UI-SPEC §Tokens). Plain data.
 * Captures inline/display × {plain, credit, debit} × {light, dark}.
 */

import type { MoneySign, MoneyVariant } from './money.component';

export interface MoneyStory {
  state: string;
  inputs: { cents: number; variant: MoneyVariant; sign: MoneySign; label?: string };
}

export const moneyStories: MoneyStory[] = [
  { state: 'inline-plain', inputs: { cents: 9990, variant: 'inline', sign: 'none' } },
  { state: 'inline-zero', inputs: { cents: 0, variant: 'inline', sign: 'none' } },
  {
    state: 'inline-credit',
    inputs: { cents: 4500, variant: 'inline', sign: 'credit' },
  },
  {
    state: 'inline-debit',
    inputs: { cents: 2000, variant: 'inline', sign: 'debit' },
  },
  {
    state: 'display-balance',
    inputs: { cents: 12000, variant: 'display', sign: 'none', label: 'Saldo disponível' },
  },
  {
    state: 'display-large',
    inputs: { cents: 1234567, variant: 'display', sign: 'none' },
  },
];
