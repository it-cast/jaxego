# CORRECAO-169 — Remoção do campo polígono dos bairros

## Páginas afetadas
- `http://localhost:4200/admin/bairros`

## Arquivos alterados

### Backend
- `apps/api/alembic/versions/0029_drop_neighborhood_polygon.py` — migration: DROP COLUMN polygon
- `apps/api/app/neighborhoods/schemas.py` — removidos `NeighborhoodPolygonUpdate`, `polygon_geojson` de `NeighborhoodCreate`, `polygon_status` de `NeighborhoodRead`
- `apps/api/app/neighborhoods/service.py` — removidos `_polygon_status`, `validate_polygon_geojson`, lógica ST_GeomFromGeoJSON, função `update_polygon`; `list_neighborhoods` simplificado para retornar `list[Neighborhood]`; `create_neighborhood` retorna `Neighborhood` (não mais tupla)
- `apps/api/app/neighborhoods/router.py` — removido endpoint `PATCH /{nbhd_id}/polygon`; `_read` simplificado (sem `polygon_status`)

### Frontend
- `apps/web/src/features/admin/neighborhoods/neighborhoods.service.ts` — removidos `polygon_geojson` de `NeighborhoodCreate`, `polygon_status` de `Neighborhood`, método `updatePolygon`
- `apps/web/src/features/admin/neighborhoods/neighborhoods.page.ts` — removidos `geojsonText`, `geojsonError`, `validateGeojson()`, coluna 'polygon' da tabela, import `HttpErrorResponse`
- `apps/web/src/features/admin/neighborhoods/neighborhoods.page.html` — removido textarea GeoJSON do form e `<td>` de polígono da tabela
- `apps/web/src/features/admin/neighborhoods/neighborhoods.page.scss` — removidos estilos `.jx-nbhd__textarea`, `.jx-nbhd__badge`

## Banco de dados
Migration `0029_drop_neighborhood_polygon` aplicada com sucesso — coluna `polygon` removida de `neighborhoods_catalog`.
