/**
 * Visual-regression BASELINE para jx-secret-reveal (UI-SPEC §Componentes/Novo).
 * Dados puros (sem Storybook). Capturar `secret-reveal-{state}-{theme}.png`
 * light+dark. O segredo é exibido 1× (D-01); o aviso é permanente.
 */

export interface SecretRevealStory {
  state: string;
  description: string;
  secret: string;
  label: string;
}

export const secretRevealStories: SecretRevealStory[] = [
  {
    state: 'api-key',
    description: 'Segredo de API key recém-criada, antes de copiar.',
    secret: 'jxg_a1b2c3d4_KQ8sR2vT5wXz9mP0nL7jH4gF6dS3aQ1e',
    label: 'Segredo da chave',
  },
  {
    state: 'webhook-secret',
    description: 'Secret de webhook rotacionado.',
    secret: 'whsec_9f8e7d6c5b4a3210ZyXwVuTsRqPoNmLkJiHgFe',
    label: 'Segredo do webhook',
  },
  {
    state: 'copiado',
    description: 'Após clicar em Copiar — feedback textual "Copiado".',
    secret: 'jxg_a1b2c3d4_KQ8sR2vT5wXz9mP0nL7jH4gF6dS3aQ1e',
    label: 'Segredo da chave',
  },
];
