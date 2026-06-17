/**
 * Visual-regression BASELINE for jx-doc-upload (UI-SPEC §10). Plain data (no
 * Storybook dependency — matches the Phase 3 state.stories.ts convention). The
 * Playwright harness renders these in light + dark + mobile and captures
 * `jx-doc-upload-{state}-{theme}-{viewport}.png`.
 */

import type { DocUploadState } from './doc-upload.component';

export interface DocUploadStory {
  state: string;
  inputs: {
    label: string;
    state: DocUploadState;
    progress?: number;
    previewUrl?: string | null;
    error?: string | null;
    captureMode?: 'environment' | 'user';
  };
}

const SAMPLE_PREVIEW =
  'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"/>';

export const docUploadStories: DocUploadStory[] = [
  { state: 'idle', inputs: { label: 'CNH', state: 'idle' } },
  {
    state: 'compressing',
    inputs: { label: 'CNH', state: 'compressing', previewUrl: SAMPLE_PREVIEW },
  },
  {
    state: 'enviando-60',
    inputs: {
      label: 'CNH',
      state: 'uploading',
      progress: 60,
      previewUrl: SAMPLE_PREVIEW,
    },
  },
  {
    state: 'sucesso',
    inputs: { label: 'CNH', state: 'success', previewUrl: SAMPLE_PREVIEW },
  },
  {
    state: 'erro-tipo',
    inputs: {
      label: 'CNH',
      state: 'error',
      error: 'Esse arquivo não é uma imagem. Tire uma foto ou escolha uma da galeria.',
    },
  },
  {
    state: 'erro-rede',
    inputs: {
      label: 'CNH',
      state: 'error',
      error: 'Sem conexão. Sua foto sobe sozinha quando a internet voltar.',
    },
  },
];

export const themes = ['light', 'dark'] as const;
