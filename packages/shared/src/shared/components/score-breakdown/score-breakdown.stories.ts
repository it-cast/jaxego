/**
 * Visual-regression BASELINE for jx-score-breakdown (UI-SPEC §Score, ADR-013).
 * Plain data. Captures the explainable table in {light, dark}.
 */

import type { ScoreComponent } from './score-breakdown.component';

export const SAMPLE_BREAKDOWN: ScoreComponent[] = [
  { component: 'acceptance', raw: 0.92, weight: 0.25, contribution: 23 },
  { component: 'punctuality', raw: 0.84, weight: 0.25, contribution: 21 },
  { component: 'proof_ok', raw: 0.95, weight: 0.2, contribution: 19 },
  { component: 'low_cancellation', raw: 0.88, weight: 0.15, contribution: 13.2 },
  { component: 'ratings', raw: 0.74, weight: 0.15, contribution: 11.1 },
];

export interface ScoreBreakdownStory {
  state: string;
  inputs: { components: ScoreComponent[]; total: number | null };
}

export const scoreBreakdownStories: ScoreBreakdownStory[] = [
  {
    state: 'com-total',
    inputs: { components: SAMPLE_BREAKDOWN, total: 87.3 },
  },
  {
    state: 'sem-total',
    inputs: { components: SAMPLE_BREAKDOWN, total: null },
  },
  {
    state: 'vazio',
    inputs: { components: [], total: null },
  },
];
