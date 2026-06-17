/**
 * Visual-regression BASELINE for jx-availability-toggle (UI-SPEC §10). Plain data
 * (no Storybook). Captured `availability-toggle-{state}-{theme}.png` light+dark,
 * mobile.
 */

export interface AvailabilityStory {
  state: string;
  inputs: { isOnline: boolean; disabled?: boolean };
  description: string;
}

export const availabilityStories: AvailabilityStory[] = [
  {
    state: 'online',
    inputs: { isOnline: true },
    description: 'Trilho success + "Online" + ponto.',
  },
  {
    state: 'offline',
    inputs: { isOnline: false },
    description: 'Trilho neutro + "Offline".',
  },
  {
    state: 'desabilitado',
    inputs: { isOnline: false, disabled: true },
    description: 'Não-active → switch inerte + warn-banner "termine sua validação".',
  },
];
