/**
 * Lazy, single-instance Leaflet loader shared by every map in the product
 * (redesign v3 — antes cada componente carregava o Leaflet do unpkg por conta).
 *
 * - Leaflet vem do npm (bundle lazy, sem CDN em runtime).
 * - leaflet-draw (só o editor de zonas usa) ainda não tem pacote no monorepo:
 *   é carregado sob demanda e se pendura no `window.L` exposto aqui.
 */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type LeafletNs = any;

let leafletPromise: Promise<LeafletNs> | null = null;
let drawPromise: Promise<LeafletNs> | null = null;

const DRAW_VERSION = '1.0.4';

export function loadLeaflet(): Promise<LeafletNs> {
  if (!leafletPromise) {
    leafletPromise = (async () => {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore — leaflet sem @types para manter "types": [] do tsconfig
      const mod: LeafletNs = await import('leaflet');
      const L = mod.default ?? mod;
      // plugins (leaflet-draw) esperam o namespace global
      (window as unknown as { L: LeafletNs }).L = L;
      return L;
    })();
  }
  return leafletPromise;
}

/** Leaflet + leaflet-draw (editor de polígonos). */
export function loadLeafletDraw(): Promise<LeafletNs> {
  if (!drawPromise) {
    drawPromise = (async () => {
      const L = await loadLeaflet();
      if (!L.Control?.Draw) {
        await Promise.all([
          injectCss(`https://unpkg.com/leaflet-draw@${DRAW_VERSION}/dist/leaflet.draw.css`),
          injectScript(`https://unpkg.com/leaflet-draw@${DRAW_VERSION}/dist/leaflet.draw.js`),
        ]);
      }
      return L;
    })();
  }
  return drawPromise;
}

function injectScript(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = url;
    s.onload = () => resolve();
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

function injectCss(url: string): Promise<void> {
  return new Promise((resolve) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    link.onload = () => resolve();
    link.onerror = () => resolve(); // estilo é cosmético — não trava o mapa
    document.head.appendChild(link);
  });
}
