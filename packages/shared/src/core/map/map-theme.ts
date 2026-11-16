import { MAP_TILE_SOURCE } from './map-tiles';

/**
 * Map theming (redesign v3). Every color a map draws comes from the semantic
 * CSS tokens (`--map-*`) read at runtime — no hex inside map components, and
 * the map follows the light/dark theme like the rest of the UI.
 */

export interface MapPalette {
  zone: string;
  zoneRef: string;
  route: string;
  pin: string;
  pinCourier: string;
  surface: string;
  categorical: string[];
}

function cssVar(name: string, el: Element = document.documentElement): string {
  return getComputedStyle(el).getPropertyValue(name).trim();
}

export function readMapPalette(el?: Element): MapPalette {
  const v = (n: string) => cssVar(n, el);
  return {
    zone: v('--map-zone'),
    zoneRef: v('--map-zone-ref'),
    route: v('--map-route'),
    pin: v('--map-pin'),
    pinCourier: v('--map-pin-courier'),
    surface: v('--surface-elevated'),
    categorical: [1, 2, 3, 4, 5, 6, 7, 8].map((i) => v(`--map-zone-${i}`)),
  };
}

/** Categorical zone color by index (cycles through the 8 token hues). */
export function zoneColor(index: number, el?: Element): string {
  const list = readMapPalette(el).categorical;
  return list[((index % list.length) + list.length) % list.length];
}

/** Watches `data-theme` + the OS scheme; returns an unsubscribe fn. */
export function onThemeChange(cb: () => void): () => void {
  const root = document.documentElement;
  const mo = new MutationObserver(() => cb());
  mo.observe(root, { attributes: true, attributeFilter: ['data-theme'] });
  const mq = window.matchMedia?.('(prefers-color-scheme: dark)');
  mq?.addEventListener?.('change', cb);
  return () => {
    mo.disconnect();
    mq?.removeEventListener?.('change', cb);
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type L = any;

/** Tile layer with the branded CSS class (filter applied per theme in _map.scss). */
export function brandTileLayer(L: L) {
  return L.tileLayer(MAP_TILE_SOURCE.url, {
    maxZoom: MAP_TILE_SOURCE.maxZoom,
    attribution: MAP_TILE_SOURCE.attribution,
    className: 'jx-map-tiles',
  });
}

export type PinKind = 'destination' | 'courier' | 'store';

/**
 * Brand pin as an inline-SVG divIcon (replaces the default blue Leaflet marker
 * that was loaded from unpkg). Colors come from CSS (`.jx-pin--*` in _map.scss).
 */
export function brandPinIcon(L: L, kind: PinKind = 'destination') {
  const glyph =
    kind === 'courier'
      ? // moto/bolt glyph
        '<path d="M13 3 6 14h5l-1 7 7-11h-5l1-7z" fill="currentColor"/>'
      : kind === 'store'
        ? '<path d="M5 9h14l-1-4H6L5 9zm0 1v9h5v-5h4v5h5v-9H5z" fill="currentColor"/>'
        : '<circle cx="12" cy="12" r="4.2" fill="currentColor"/>';
  const html = `
    <span class="jx-pin jx-pin--${kind}" aria-hidden="true">
      <span class="jx-pin__pulse"></span>
      <svg class="jx-pin__shape" viewBox="0 0 40 52" width="40" height="52">
        <path class="jx-pin__body" d="M20 51c-1.2 0-2.2-.6-2.9-1.6C11.4 41.3 2 30.6 2 19.6 2 9.6 10 2 20 2s18 7.6 18 17.6c0 11-9.4 21.7-15.1 29.8-.7 1-1.7 1.6-2.9 1.6z"/>
        <svg x="8" y="7.5" width="24" height="24" viewBox="0 0 24 24" class="jx-pin__glyph">${glyph}</svg>
      </svg>
    </span>`;
  return L.divIcon({
    className: 'jx-pin-host',
    html,
    iconSize: [40, 52],
    iconAnchor: [20, 50],
    popupAnchor: [0, -46],
  });
}

/** Polygon style for an editable/active zone. */
export function activeZoneStyle(color: string) {
  return { color, weight: 3, opacity: 1, fillColor: color, fillOpacity: 0.18, lineJoin: 'round' };
}

/** Polygon style for a reference (non-editable) zone. */
export function referenceZoneStyle(color: string) {
  return { color, weight: 2, opacity: 0.85, fillColor: color, fillOpacity: 0.07, dashArray: '6 6' };
}
