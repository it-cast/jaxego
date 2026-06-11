/**
 * Visual-regression BASELINE for jx-tracking-banner (UI-SPEC §12). Plain data.
 * Captures states with/without ETA × {light, dark}. Name: tracking-banner-{state}-{theme}.
 */

import type { TrackingState } from '../tracking-timeline/tracking-timeline.component';

export interface TrackingBannerStory {
  state: string;
  inputs: { state: TrackingState; etaSeconds: number | null };
}

export const trackingBannerStories: TrackingBannerStory[] = [
  { state: 'criada', inputs: { state: 'CRIADA', etaSeconds: null } },
  { state: 'aceita-eta', inputs: { state: 'ACEITA', etaSeconds: 900 } },
  { state: 'coletada-eta', inputs: { state: 'COLETADA', etaSeconds: 600 } },
  { state: 'entregue', inputs: { state: 'ENTREGUE', etaSeconds: null } },
];
