/**
 * Visual-regression BASELINE for the area-config page (UI-SPEC §10). Plain data
 * (no Storybook). Captured `area-config-{state}-{theme}.png` light+dark.
 */

import type { AreaConfig } from './area-config.service';

export const SAMPLE_CONFIG: AreaConfig = {
  kyc_level: 'completa',
  piso_entrega: '8.00',
  piso_km: '2.50',
  geofence_m: 80,
  timeout_oferta_s: 20,
  timeout_favoritos_s: 60,
  politica_retorno_pct: 50,
};

export interface AreaConfigStory {
  state: string;
  description: string;
}

export const areaConfigStories: AreaConfigStory[] = [
  { state: 'form-completo', description: 'Config carregada, válida, pronta para salvar.' },
  { state: 'validando', description: 'Campo fora da faixa com erro acionável no blur.' },
  {
    state: 'confirmacao-sensivel',
    description: 'Diálogo before→after antes do PATCH auditado.',
  },
  { state: 'erro-faixa', description: 'Geofence fora de 30–300 → mensagem cita a faixa.' },
];
