/**
 * Single point of config for the map raster tile source (TD-019).
 *
 * Default: OpenStreetMap público (piloto, baixo volume). Para produção/alto
 * volume, troque AQUI por um provider comercial ou self-host — sem tocar o
 * componente `jx-live-map`:
 *
 *   MapTiler:  tiles: [`https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=${KEY}`]
 *   Mapbox:    tiles: [`https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{z}/{x}/{y}?access_token=${TOKEN}`]
 *   Self-host: tiles: ['https://tiles.jaxego.com.br/{z}/{x}/{y}.png']
 *
 * O token/URL deve vir de configuração de ambiente no build de produção, nunca
 * hardcoded com segredo. Por ora o piloto usa OSM (sem token).
 */
export interface MapTileSource {
  tiles: string[];
  tileSize: number;
  attribution: string;
}

export const MAP_TILE_SOURCE: MapTileSource = {
  tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
  tileSize: 256,
  attribution: '© OpenStreetMap',
};
