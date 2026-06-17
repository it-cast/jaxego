/**
 * Visual-regression BASELINE for the courier wizard (tela 03, UI-SPEC §10).
 * Plain data. Captured `cadastro-entregador-{state}-{theme}-mobile.png`.
 */

export interface CadastroStory {
  state: string;
  note: string;
}

export const cadastroStories: CadastroStory[] = [
  { state: 'passo-1-dados', note: 'área + CPF + telefone + e-mail + senha + consent' },
  { state: 'passo-2-selfie', note: 'jx-doc-card selfie (capture user) + microcopy privacidade' },
  { state: 'passo-3-veiculo', note: 'tipo + placa (condicional motorizado)' },
  { state: 'passo-4-documentos', note: 'CNH/CRLV/MEI (só nível completa) + warn-banner' },
  { state: 'cpf-ja-cadastrado', note: 'E2 anti-enumeração — mensagem única' },
  { state: 'pending_kyc', note: 'em-análise pós-submit (sem confete)' },
  { state: 'mei_pending', note: 'banner permanente de regularização (RN-024)' },
];

export const themes = ['light', 'dark'] as const;
