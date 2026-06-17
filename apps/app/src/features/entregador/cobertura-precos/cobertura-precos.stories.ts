/**
 * Visual-regression BASELINE for the cobertura+preços screen (UI-SPEC §10). Plain
 * data (no Storybook). Captured `cobertura-precos-{state}-{theme}.png`
 * light+dark, mobile viewport.
 */

import type { CoverageItem } from './coverage-list.component';

export const SAMPLE_ITEMS: CoverageItem[] = [
  { neighborhoodId: 1, name: 'Centro', covered: true, excluded: false, price: 'R$ 9,00' },
  { neighborhoodId: 2, name: 'Aldeia', covered: true, excluded: false, price: 'R$ 8,50' },
  {
    neighborhoodId: 3,
    name: 'Vila do Pescador',
    covered: false,
    excluded: true,
    price: '',
  },
];

export interface CoberturaStory {
  state: string;
  description: string;
}

export const coberturaStories: CoberturaStory[] = [
  { state: 'modo-bairro', description: 'Cobertura por bairro com preço por linha.' },
  { state: 'modo-km', description: 'Faixas por km + cobertura visível.' },
  {
    state: 'preco-abaixo-do-piso',
    description: 'Preço < piso → role=alert citando o piso (R$ X,XX).',
  },
  { state: 'retorno', description: '% de retorno preenchido.' },
  { state: 'sem-cobertura', description: 'Nenhum bairro atendido → empty-state.' },
];
