/** Visual-regression BASELINE for jx-card-form (UI-SPEC §14): idle, cifrando, recusado. */
import type { CardFormState } from './jx-card-form.component';

export interface CardFormStory {
  state: string;
  inputs: { ctaLabel: string; formState: CardFormState };
}

export const cardFormStories: CardFormStory[] = [
  { state: 'idle', inputs: { ctaLabel: 'Confirmar pagamento', formState: 'idle' } },
  { state: 'cifrando', inputs: { ctaLabel: 'Confirmar pagamento', formState: 'cifrando' } },
  { state: 'recusado', inputs: { ctaLabel: 'Confirmar pagamento', formState: 'recusado' } },
];
