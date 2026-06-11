/**
 * Visual-regression BASELINE for jx-subscription-status (UI-SPEC §14).
 * States: trial, active, blocked, cancelado — captured in {light, dark}.
 */
import type { BillingStatus } from './jx-subscription-status.component';

export interface SubscriptionStatusStory {
  state: string;
  inputs: { status: BillingStatus; amountCents: number; nextDueAt: string | null; trialDays: number | null };
}

export const subscriptionStatusStories: SubscriptionStatusStory[] = [
  { state: 'trial', inputs: { status: 'trial', amountCents: 0, nextDueAt: null, trialDays: 7 } },
  { state: 'active', inputs: { status: 'active', amountCents: 9990, nextDueAt: '2026-07-11', trialDays: null } },
  { state: 'blocked', inputs: { status: 'blocked', amountCents: 9990, nextDueAt: '2026-06-01', trialDays: null } },
  { state: 'cancelado', inputs: { status: 'cancelado', amountCents: 0, nextDueAt: null, trialDays: null } },
];
