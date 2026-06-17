/**
 * Visual-regression BASELINE for jx-live-map (UI-SPEC §12). Plain data.
 *
 * The map itself is lazy (MapLibre loads on intersection), so the captured baseline is
 * the SKELETON placeholder + reserved height in {light, dark} — the LCP-safe state the
 * page paints before the tiles arrive. Name: live-map-{state}-{theme}.
 */

export interface LiveMapStory {
  state: string;
  inputs: { lat: number | null; lng: number | null; ariaLabel: string };
}

export const liveMapStories: LiveMapStory[] = [
  {
    state: 'skeleton',
    inputs: { lat: -21.54, lng: -42.18, ariaLabel: 'Posição aproximada do entregador no mapa' },
  },
];
