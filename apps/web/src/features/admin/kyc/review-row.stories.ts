/**
 * Visual-regression BASELINE for jx-kyc-review-row (UI-SPEC §10). Plain data
 * (no Storybook). Captured `jx-kyc-review-row-{state}-{theme}.png` light+dark.
 */

import type { ReviewStatus } from './review-row.component';

export interface ReviewRowStory {
  state: string;
  inputs: {
    title: string;
    status: ReviewStatus;
    meta?: string;
    thumbUrl?: string | null;
    thumbState?: 'loading' | 'ready' | 'error';
  };
}

export const reviewRowStories: ReviewRowStory[] = [
  {
    state: 'aprovar',
    inputs: {
      title: 'Selfie com documento',
      status: 'pending',
      meta: '123.***.***-09 · enviada há 5h',
    },
  },
  {
    // The "reject reason open" state is driven by an interaction (clicking
    // Reprovar); the baseline captures the pending row from which it opens.
    state: 'reprovar-motivo-aberto',
    inputs: {
      title: 'CNH com EAR',
      status: 'pending',
      meta: '123.***.***-09 · enviada há 2h',
    },
  },
  {
    state: 'auto-aprovado',
    inputs: {
      title: 'MEI',
      status: 'approved_auto',
      meta: 'CNAE 5320-2/02 · Receita: ATIVO',
    },
  },
  {
    state: 'thumb-carregando',
    inputs: {
      title: 'CRLV',
      status: 'pending',
      thumbState: 'loading',
      meta: '123.***.***-09',
    },
  },
];

export const themes = ['light', 'dark'] as const;
