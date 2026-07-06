/**
 * Visual-regression BASELINE for jx-upgrade-modal (UI-SPEC §8). Plain data.
 * Captures: open (comparison), focus on "Agora não", mobile · light+dark.
 */

import type { Plan } from '../plan-card/plan-card.component';

export const UPGRADE_PLANS: Plan[] = [
  {
    id: 1,
    codename: 'free',
    nome: 'Free',
    preco_cents: 0,
    entregas_mes: 2,
    taxa_entrega_cents: 150,
    is_free: true,
    is_unlimited: false,
  },
  {
    id: 2,
    codename: 'inicio',
    nome: 'Início',
    preco_cents: 4990,
    entregas_mes: 40,
    taxa_entrega_cents: 120,
    is_free: false,
    is_unlimited: false,
  },
  {
    id: 3,
    codename: 'profissional',
    nome: 'Profissional',
    preco_cents: 9990,
    entregas_mes: 150,
    taxa_entrega_cents: 100,
    is_free: false,
    is_unlimited: false,
  },
];

export interface UpgradeModalStory {
  state: string;
  inputs: { plans: Plan[]; currentPlanName: string; limit: number };
}

export const upgradeModalStories: UpgradeModalStory[] = [
  { state: 'aberto', inputs: { plans: UPGRADE_PLANS, currentPlanName: 'Free', limit: 2 } },
];
