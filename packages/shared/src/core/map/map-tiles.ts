/**
 * Single point of config for the map raster tile source (TD-019).
 *
 * Default: OpenStreetMap público (piloto, baixo volume). Para produção/alto
 * volume, troque AQUI por um provider comercial ou self-host — sem tocar os
 * componentes de mapa (`jx-live-map`, `jx-area-map`, `jx-zona-map`):
 *
 *   MapTiler:  url: `https://api.maptiler.com/maps/streets-v2/{z}/{x}/{y}.png?key=${KEY}`
 *   Self-host: url: 'https://tiles.jaxego.com.br/{z}/{x}/{y}.png'
 *
 * O visual (claro/escuro) NÃO depende do provider: o redesign v3 aplica um
 * filtro CSS por tema (`--map-tiles-filter`, ver styles/_map.scss), então um
 * único conjunto de tiles serve os dois temas.
 *
 * O token/URL deve vir de configuração de ambiente no build de produção, nunca
 * hardcoded com segredo. Por ora o piloto usa OSM (sem token).
 */
export interface MapTileSource {
  /** Leaflet-style template ({z}/{x}/{y}). */
  url: string;
  /** MapLibre-style list (kept for compatibility). */
  tiles: string[];
  tileSize: number;
  maxZoom: number;
  attribution: string;
}

const OSM_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

export const MAP_TILE_SOURCE: MapTileSource = {
  url: OSM_URL,
  tiles: [OSM_URL],
  tileSize: 256,
  maxZoom: 19,
  attribution: '© OpenStreetMap',
};

/** Default map center when no geometry is known yet (piloto: Santo Antônio de Pádua/RJ). */
export const MAP_DEFAULT_CENTER: [number, number] = [-21.54, -42.18];
