/**
 * Visual-regression BASELINE for jx-score-badge (UI-SPEC §Score). Plain data.
 * Captures all 5 levels × {md, lg} × {light, dark}.
 */

import type { ScoreLevel } from './score-badge.component';

const LEVELS: ScoreLevel[] = ['probation', 'bronze', 'prata', 'ouro', 'diamante'];

const SAMPLE_VALUE: Record<ScoreLevel, number> = {
  probation: 28,
  bronze: 42,
  prata: 61.5,
  ouro: 78.6,
  diamante: 93,
};

export interface ScoreBadgeStory {
  state: string;
  inputs: { level: ScoreLevel; value: number | null; size: 'md' | 'lg' };
}

export const scoreBadgeStories: ScoreBadgeStory[] = [
  ...LEVELS.map((l): ScoreBadgeStory => ({
    state: `md-${l}`,
    inputs: { level: l, value: SAMPLE_VALUE[l], size: 'md' },
  })),
  ...LEVELS.map((l): ScoreBadgeStory => ({
    state: `lg-${l}`,
    inputs: { level: l, value: SAMPLE_VALUE[l], size: 'lg' },
  })),
  {
    state: 'md-sem-valor',
    inputs: { level: 'prata', value: null, size: 'md' },
  },
];
