/** Visual-regression BASELINE for jx-checkout-method-toggle (UI-SPEC §14). */
import type { CheckoutMethod } from './jx-checkout-method-toggle.component';

export interface CheckoutMethodToggleStory {
  state: string;
  inputs: { method: CheckoutMethod; disabled: boolean };
}

export const checkoutMethodToggleStories: CheckoutMethodToggleStory[] = [
  { state: 'cartao-selecionado', inputs: { method: 'card', disabled: false } },
  { state: 'pix-selecionado', inputs: { method: 'pix', disabled: false } },
  { state: 'processando', inputs: { method: 'card', disabled: true } },
];
