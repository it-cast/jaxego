/** Visual-regression BASELINE for jx-plan-compare (UI-SPEC §14): upgrade, downgrade. */
import type { Plan } from '@jaxego/shared/components';

export interface PlanCompareStory {
  state: string;
  inputs: { planList: Plan[]; current: string; currentPrice: number; prorata: number };
}

const plans: Plan[] = [
  { id: 1, codename: 'free', nome: 'Free', preco_mensal_cents: 0, preco_anual_cents: 0, entregas_mes: 30, taxa_entrega_cents: 200, is_free: true, is_unlimited: false },
  { id: 3, codename: 'pro', nome: 'Profissional', preco_mensal_cents: 9990, preco_anual_cents: 99900, entregas_mes: 300, taxa_entrega_cents: 150, is_free: false, is_unlimited: false },
];

export const planCompareStories: PlanCompareStory[] = [
  { state: 'upgrade-prorata', inputs: { planList: plans, current: 'free', currentPrice: 0, prorata: 2500 } },
  { state: 'downgrade-agendado', inputs: { planList: plans, current: 'pro', currentPrice: 9990, prorata: 0 } },
];
