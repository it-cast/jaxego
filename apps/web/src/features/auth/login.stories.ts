/**
 * Visual-regression BASELINE for the login screen (UI-SPEC §9).
 * Baseline-only (no comparison yet). The T-06 Playwright harness drives the
 * /entrar route into each state across light + dark and captures
 * `login-{state}-{theme}-{viewport}.png`.
 */
export type Theme = 'light' | 'dark';

export interface LoginStory {
  state: 'idle' | 'loading' | 'erro' | 'totp';
  description: string;
}

export const loginStories: LoginStory[] = [
  { state: 'idle', description: 'form completo, foco no e-mail, botão habilitado' },
  { state: 'loading', description: 'botão desabilitado + skeleton, aria-busy' },
  {
    state: 'erro',
    description: 'jx-error-state role=alert, mensagem anti-enumeração',
  },
  { state: 'totp', description: 'campo Código de verificação revelado (mono)' },
];

export const themes: Theme[] = ['light', 'dark'];
