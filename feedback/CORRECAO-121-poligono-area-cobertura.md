# CORRECAO-121 — Mapa com polígono para demarcar área de cobertura

## O que mudou

### Backend (apps/api)
- **areas/models.py**: Adicionado campo `boundary` (JSON, nullable) na tabela `areas` para armazenar GeoJSON Polygon
- **alembic 0020**: Migration para adicionar coluna `boundary`
- **areas/schemas.py**: `AreaCreate`, `AreaUpdate` e `AreaRead` agora incluem `boundary`
- **areas/service.py**: `create_area` e `update_area` salvam o boundary

### Frontend (apps/web)
- **area-map.component.ts** (novo): Componente de mapa interativo com Leaflet + Leaflet.draw (carregados via CDN). Permite desenhar, editar e deletar polígonos. Emite GeoJSON Polygon via `boundaryChange`.
- **areas.page.ts**: Importa `AreaMapComponent`, gerencia `formBoundary` no create/edit/save
- **areas.page.html**: Mapa adicionado no formulário de criar/editar área com hint explicativo
- **areas.page.scss**: Adicionado estilo `.jx-areas__hint`
- **platform-admin.service.ts**: Interface `Area` agora inclui `boundary` e `GeoJSON`

## Arquivos alterados
- apps/api/app/areas/models.py
- apps/api/alembic/versions/0020_area_boundary.py (novo)
- apps/api/app/areas/schemas.py
- apps/api/app/areas/service.py
- apps/web/src/features/admin-plataforma/area-map.component.ts (novo)
- apps/web/src/features/admin-plataforma/areas.page.ts
- apps/web/src/features/admin-plataforma/areas.page.html
- apps/web/src/features/admin-plataforma/areas.page.scss
- apps/web/src/features/admin-plataforma/platform-admin.service.ts
