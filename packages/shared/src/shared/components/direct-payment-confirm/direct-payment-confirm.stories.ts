/**
 * Visual-regression BASELINE for jx-direct-payment-confirm (UI-SPEC §12). Plain data.
 * Name: direct-payment-confirm-default-{theme}.
 */

export interface DirectPaymentConfirmStory {
  state: string;
  inputs: { amountLabel: string };
}

export const directPaymentConfirmStories: DirectPaymentConfirmStory[] = [
  { state: 'default', inputs: { amountLabel: 'R$ 25,00' } },
];
