/**
 * Visual-regression BASELINE for jx-geofence-pill (UI-SPEC §12). Plain data.
 * Captures every verdict × {light, dark}. Name: geofence-pill-{state}-{theme}.
 */

import type { GeofenceState } from './geofence-pill.component';

const STATES: GeofenceState[] = ['checking', 'ok', 'out', 'missing', 'low_confidence'];

export interface GeofencePillStory {
  state: string;
  inputs: { state: GeofenceState };
}

export const geofencePillStories: GeofencePillStory[] = STATES.map((s) => ({
  state: s,
  inputs: { state: s },
}));
