/**
 * Visual-regression BASELINE definitions for the Phase 8 dispatch components
 * (UI-SPEC §10). Plain data (no Storybook dependency — same convention as
 * src/shared/state/state.stories.ts). The harness renders each in light + dark
 * and captures `{component}-{state}-{theme}-{viewport}.png`.
 *
 * Covers: jx-score-chip (5 levels), jx-accepted-courier-card (with/without photo),
 * jx-offer-timer (calm/attention/urgent/reduced-motion), jx-offer-sheet states,
 * the entregador-home dispatch states, and the loja favoritos lists.
 */

export type Theme = 'light' | 'dark';

export interface DispatchStory {
  component:
    | 'jx-score-chip'
    | 'jx-accepted-courier-card'
    | 'jx-offer-timer'
    | 'jx-offer-sheet'
    | 'jx-favorite-row'
    | 'jx-blocked-row'
    | 'entregador-home'
    | 'loja-favoritos';
  state: string;
  inputs: Record<string, unknown>;
}

export const dispatchStories: DispatchStory[] = [
  // jx-score-chip — all 5 levels (UI-SPEC §7.1).
  { component: 'jx-score-chip', state: 'probation', inputs: { level: 'probation', value: 12 } },
  { component: 'jx-score-chip', state: 'bronze', inputs: { level: 'bronze', value: 45 } },
  { component: 'jx-score-chip', state: 'prata', inputs: { level: 'prata', value: 68 } },
  { component: 'jx-score-chip', state: 'ouro', inputs: { level: 'ouro', value: 87.4 } },
  { component: 'jx-score-chip', state: 'diamante', inputs: { level: 'diamante', value: 96 } },

  // jx-accepted-courier-card.
  {
    component: 'jx-accepted-courier-card',
    state: 'com-foto',
    inputs: {
      name: 'Ana Favorita',
      plate: 'ABC1D23',
      scoreLevel: 'ouro',
      scoreValue: 87,
      photoUrl: '/assets/stub-photo.webp',
    },
  },
  {
    component: 'jx-accepted-courier-card',
    state: 'sem-foto',
    inputs: { name: 'Beto Comum', plate: 'XYZ9K88', scoreLevel: 'prata', scoreValue: 64 },
  },

  // jx-offer-timer — urgency phases + reduced-motion (UI-SPEC §4.2).
  { component: 'jx-offer-timer', state: 'calmo', inputs: { ttlTotalS: 20, ttlRemainingS: 16 } },
  { component: 'jx-offer-timer', state: 'atencao', inputs: { ttlTotalS: 20, ttlRemainingS: 8 } },
  { component: 'jx-offer-timer', state: 'urgente', inputs: { ttlTotalS: 20, ttlRemainingS: 3 } },
  {
    component: 'jx-offer-timer',
    state: 'reduced-motion',
    inputs: { ttlTotalS: 20, ttlRemainingS: 16, reducedMotion: true },
  },

  // jx-offer-sheet — active + terminal states (UI-SPEC §3.5).
  { component: 'jx-offer-sheet', state: 'oferta-ativa', inputs: { result: null } },
  { component: 'jx-offer-sheet', state: 'processando', inputs: { processing: true } },
  { component: 'jx-offer-sheet', state: 'ganhou', inputs: { result: 'won' } },
  { component: 'jx-offer-sheet', state: 'perdeu-corrida', inputs: { result: 'lost' } },
  { component: 'jx-offer-sheet', state: 'expirou', inputs: { result: 'expired' } },
  { component: 'jx-offer-sheet', state: 'falha-rede', inputs: { result: 'error' } },

  // entregador-home — dispatch states (UI-SPEC §2.3).
  { component: 'entregador-home', state: 'offline', inputs: { online: false } },
  { component: 'entregador-home', state: 'aguardando', inputs: { online: true } },
  { component: 'entregador-home', state: 'em-uma-entrega', inputs: { busy: true } },

  // loja-favoritos — lists (UI-SPEC §5).
  { component: 'jx-favorite-row', state: 'primeiro', inputs: { canMoveUp: false } },
  { component: 'jx-favorite-row', state: 'meio', inputs: { canMoveUp: true, canMoveDown: true } },
  { component: 'jx-favorite-row', state: 'ultimo', inputs: { canMoveDown: false } },
  { component: 'jx-blocked-row', state: 'com-motivo', inputs: { reason: 'atraso recorrente' } },
];
