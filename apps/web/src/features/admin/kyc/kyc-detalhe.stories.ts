/**
 * Visual-regression BASELINE for the admin KYC detail (tela 19, UI-SPEC §10).
 * Plain data. Captured `admin-kyc-detalhe-{state}-{theme}.png` light+dark.
 */

export interface KycDetalheStory {
  state: string;
  note: string;
}

export const kycDetalheStories: KycDetalheStory[] = [
  { state: 'revisao-2-de-4', note: '4 itens: selfie aprovado, CNH/CRLV em análise, MEI auto' },
  { state: 'reprovar-sem-motivo', note: 'reject form aberto sem motivo → bloqueio + alerta' },
  { state: 'documento-expirado', note: 'thumb com erro + retry que regenera a view-url' },
];

export const themes = ['light', 'dark'] as const;
