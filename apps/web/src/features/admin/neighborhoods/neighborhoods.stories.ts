/**
 * Visual-regression BASELINE for the neighborhoods catalog (UI-SPEC §10). Plain
 * data (no Storybook). Captured `neighborhoods-{state}-{theme}.png` light+dark.
 */

import type { Neighborhood } from './neighborhoods.service';

export const SAMPLE_NEIGHBORHOODS: Neighborhood[] = [
  { id: 1, area_id: 1, name: 'Centro', is_informal: false, polygon_status: 'defined' },
  { id: 2, area_id: 1, name: 'Aldeia', is_informal: false, polygon_status: 'by_name' },
  {
    id: 3,
    area_id: 1,
    name: 'Vila do Pescador',
    is_informal: true,
    polygon_status: 'by_name',
  },
];

export interface NeighborhoodsStory {
  state: string;
  description: string;
}

export const neighborhoodsStories: NeighborhoodsStory[] = [
  { state: 'com-bairros', description: 'Catálogo com bairros (definido/por nome/informal).' },
  { state: 'vazio', description: 'Catálogo vazio → jx-empty-state com CTA.' },
  {
    state: 'remocao-bloqueada',
    description: 'Remoção com entregas ativas → role=alert citando o bairro.',
  },
  { state: 'geojson-invalido', description: 'GeoJSON malformado → erro inline.' },
];
