/**
 * Visual-regression BASELINE definitions for the Phase 4 wizard components
 * (UI-SPEC §10). Baseline-only (product/visual-regression-testing): plain data
 * the harness renders in light + dark, capturing
 * `{component}-{state}-{theme}-{viewport}.png`. Storybook is not installed
 * (Phase 3 decision); these stay framework-agnostic.
 */

export type Theme = 'light' | 'dark';

export interface ComponentStory {
  component:
    | 'jx-wizard-stepper'
    | 'jx-field'
    | 'jx-plan-card'
    | 'cadastro-loja'
    | 'selecao-plano'
    | 'dashboard-pos-ativacao';
  state: string;
  inputs: Record<string, unknown>;
}

const STEPS = [
  { label: 'Identificação' },
  { label: 'Confirmação' },
  { label: 'Endereço' },
  { label: 'Plano' },
];

export const wizardStories: ComponentStory[] = [
  // jx-wizard-stepper
  { component: 'jx-wizard-stepper', state: 'passo-1', inputs: { steps: STEPS, current: 0 } },
  { component: 'jx-wizard-stepper', state: 'passo-2', inputs: { steps: STEPS, current: 1 } },
  { component: 'jx-wizard-stepper', state: 'passo-3', inputs: { steps: STEPS, current: 2 } },
  { component: 'jx-wizard-stepper', state: 'concluido', inputs: { steps: STEPS, current: 3 } },
  // jx-field
  {
    component: 'jx-field',
    state: 'idle',
    inputs: { label: 'Nome da loja', placeholder: 'Padaria do Zé' },
  },
  {
    component: 'jx-field',
    state: 'erro',
    inputs: {
      label: 'CNPJ',
      error: 'CNPJ incompleto. Confira os 14 dígitos.',
      mono: true,
    },
  },
  {
    component: 'jx-field',
    state: 'mono-preenchido',
    inputs: { label: 'CNPJ', mono: true, value: '11.222.333/0001-81' },
  },
  // jx-plan-card
  {
    component: 'jx-plan-card',
    state: 'free-selecionado',
    inputs: {
      plan: {
        codename: 'free',
        nome: 'Free',
        preco_cents: 0,
        entregas_mes: 2,
        taxa_entrega_cents: 200,
        is_free: true,
        is_unlimited: false,
      },
      selected: true,
    },
  },
  {
    component: 'jx-plan-card',
    state: 'pago-outline',
    inputs: {
      plan: {
        codename: 'profissional',
        nome: 'Profissional',
        preco_cents: 12900,
        entregas_mes: 150,
        taxa_entrega_cents: 100,
        is_free: false,
        is_unlimited: false,
      },
      selected: false,
    },
  },
  // composed screens
  { component: 'cadastro-loja', state: 'passo-1', inputs: {} },
  { component: 'cadastro-loja', state: 'erro-cnpj-e1', inputs: {} },
  { component: 'cadastro-loja', state: 'colisao-e2', inputs: {} },
  { component: 'cadastro-loja', state: 'sem-area', inputs: {} },
  { component: 'selecao-plano', state: 'grid-4-planos', inputs: {} },
  { component: 'dashboard-pos-ativacao', state: 'onboarding-hint', inputs: {} },
  { component: 'dashboard-pos-ativacao', state: 'pending-payment-e3', inputs: {} },
  { component: 'dashboard-pos-ativacao', state: 'pending-validation-e4', inputs: {} },
];

export const themes: Theme[] = ['light', 'dark'];
