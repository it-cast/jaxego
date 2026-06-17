/**
 * Visual-regression BASELINE for jx-doc-card (UI-SPEC §10). Plain data (no
 * Storybook). Captured as `jx-doc-card-{state}-{theme}.png` in light + dark.
 */

import type { DocStatus } from './doc-card.component';

export interface DocCardStory {
  state: string;
  inputs: {
    title: string;
    mode: 'edit' | 'read';
    status: DocStatus;
    purpose?: string;
    meta?: string;
    rejectReason?: string;
    previewUrl?: string | null;
  };
}

export const docCardStories: DocCardStory[] = [
  {
    state: 'edicao',
    inputs: {
      title: 'Selfie com documento',
      mode: 'edit',
      status: 'pending_upload',
      purpose: 'Confirma que é você de verdade.',
    },
  },
  {
    state: 'em-analise',
    inputs: {
      title: 'CNH com EAR',
      mode: 'read',
      status: 'pending',
      meta: 'enviado 23/04',
    },
  },
  {
    state: 'aprovado',
    inputs: { title: 'Selfie com documento', mode: 'read', status: 'approved' },
  },
  {
    state: 'reprovado-com-motivo',
    inputs: {
      title: 'CNH com EAR',
      mode: 'read',
      status: 'rejected',
      rejectReason: 'Sem observação EAR na CNH.',
    },
  },
  {
    state: 'mei-pendente',
    inputs: {
      title: 'MEI',
      mode: 'read',
      status: 'mei_pending',
      meta: 'CNAE 5320-2/02 · Receita: INATIVO',
    },
  },
];

export const themes = ['light', 'dark'] as const;
