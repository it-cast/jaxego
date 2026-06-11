/**
 * Visual-regression BASELINE for jx-tracking-timeline (UI-SPEC §12). Plain data.
 * Captures representative states × {light, dark}. Name: tracking-timeline-{state}-{theme}.
 */

import type {
  TimelineEntry,
  TrackingState,
} from './tracking-timeline.component';

const ENTRIES: TimelineEntry[] = [
  { state: 'CRIADA', at: '2026-06-10T10:00:00Z' },
  { state: 'ACEITA', at: '2026-06-10T10:05:00Z' },
  { state: 'COLETADA', at: '2026-06-10T10:20:00Z' },
];

export interface TimelineStory {
  state: string;
  inputs: { state: TrackingState; entries: TimelineEntry[] };
}

export const trackingTimelineStories: TimelineStory[] = (
  ['CRIADA', 'ACEITA', 'COLETADA', 'ENTREGUE', 'FINALIZADA', 'RECUSADA_NO_DESTINO'] as TrackingState[]
).map((s) => ({
  state: s.toLowerCase(),
  inputs: { state: s, entries: ENTRIES },
}));
