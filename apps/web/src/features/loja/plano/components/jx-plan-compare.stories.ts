/** Visual-regression BASELINE for jx-plan-compare (UI-SPEC §14): upgrade, downgrade. */
import type { Plan } from '../../../../shared/components';

export interface PlanCompareStory {
  state: string;
  inputs: { planList: Plan[]; current: string; currentPrice: number; prorata: number };
}

const plans: Plan[] = [
  { codename: 'free', nome: 'Free', preco_cents: 0, entregas_mes: 30, taxa_entrega_cents: 200, is_free: true, is_unlimited: false },
  { codename: 'pro', nome: 'Profissional', preco_cents: 9990, entregas_mes: 300, taxa_entrega_cents: 150, is_free: false, is_unlimited: false },
];

export const planCompareStories: PlanCompareStory[] = [
  { state: 'upgrade-prorata', inputs: { planList: plans, current: 'free', currentPrice: 0, prorata: 2500 } },
  { state: 'downgrade-agendado', inputs: { planList: plans, current: 'pro', currentPrice: 9990, prorata: 0 } },
];
