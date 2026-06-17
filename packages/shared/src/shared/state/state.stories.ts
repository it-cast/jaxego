/**
 * Visual-regression BASELINE definitions for the canonical state components
 * (UI-SPEC §9). No comparison yet — this phase only declares the baseline
 * matrix (product/visual-regression-testing: baseline-only). The T-06 Playwright
 * harness renders these in light + dark and captures
 * `{component}-{state}-{theme}-{viewport}.png`.
 *
 * Storybook is intentionally NOT installed in Phase 3 (out of scope / CONTEXT
 * deferred). These are plain data so the harness — or a future Storybook setup —
 * can drive them without a heavy dependency.
 */

export type Theme = 'light' | 'dark';

export interface StateStory {
  component:
    | 'jx-empty-state'
    | 'jx-error-state'
    | 'jx-loading-skeleton'
    | 'jx-warn-banner';
  state: string;
  inputs: Record<string, unknown>;
}

export const stateStories: StateStory[] = [
  // jx-empty-state
  {
    component: 'jx-empty-state',
    state: 'default',
    inputs: { title: 'Nada por aqui ainda.', icon: '∅' },
  },
  {
    component: 'jx-empty-state',
    state: 'com-cta',
    inputs: {
      title: 'Nenhuma entrega ainda.',
      message: 'Crie a primeira no botão acima.',
      ctaLabel: 'Criar agora',
      icon: '∅',
    },
  },
  {
    component: 'jx-empty-state',
    state: 'sem-cta',
    inputs: {
      title: 'Sem resultados.',
      message: 'Ajuste os filtros e tente de novo.',
    },
  },
  // jx-error-state
  {
    component: 'jx-error-state',
    state: 'padrao',
    inputs: {
      message: 'Tivemos um problema aqui. Já estamos vendo — tente em instantes.',
    },
  },
  {
    component: 'jx-error-state',
    state: 'com-retry',
    inputs: {
      message:
        'Não conseguimos carregar as entregas. Tente de novo em alguns segundos.',
      retryLabel: 'Tentar de novo',
    },
  },
  // jx-loading-skeleton
  { component: 'jx-loading-skeleton', state: 'line', inputs: { variant: 'line' } },
  {
    component: 'jx-loading-skeleton',
    state: 'block',
    inputs: { variant: 'block' },
  },
  {
    component: 'jx-loading-skeleton',
    state: 'circle',
    inputs: { variant: 'circle' },
  },
  // jx-warn-banner
  {
    component: 'jx-warn-banner',
    state: 'padrao',
    inputs: {
      message:
        'Sua loja está em validação simples. Algumas funções liberam após a completa.',
    },
  },
  {
    component: 'jx-warn-banner',
    state: 'dispensavel',
    inputs: {
      message: 'Conexão instável. Mostrando dados salvos.',
      dismissible: true,
    },
  },
];

export const themes: Theme[] = ['light', 'dark'];
