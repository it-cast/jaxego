/**
 * Visual-regression BASELINE for jx-notice (UI-SPEC §12). Plain data.
 * Captures each tone × {light, dark}. Name: notice-{tone}-{theme}.
 */

import type { NoticeTone } from './notice.component';

const TONES: NoticeTone[] = ['info', 'success', 'warning', 'error'];

export interface NoticeStory {
  state: string;
  inputs: { tone: NoticeTone; title: string | null; message: string };
}

export const noticeStories: NoticeStory[] = TONES.map((tone) => ({
  state: tone,
  inputs: {
    tone,
    title: tone === 'success' ? 'Pedido entregue' : null,
    message: 'Seu pedido está a caminho.',
  },
}));
