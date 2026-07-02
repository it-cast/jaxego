# CORRECAO-179 — Tabela zonas + CRUD admin_area

## O que foi feito
Nova entidade `Zona` como subdivisão de `Area`. O polígono sai de `Area` e vai
para `Zona`, permitindo que o admin_area cadastre múltiplas zonas com boundaries
individuais.

## Mudanças backend
- `app/areas/models.py`: novo modelo `Zona` (area_id FK, name, boundary JSON, timestamps); removido `boundary` de `Area`
- `app/areas/schemas.py`: removido `boundary` de `AreaCreate/AreaUpdate/AreaRead`; adicionado `ZonaCreate/ZonaUpdate/ZonaRead`
- `app/areas/service.py`: removido boundary de `create_area`/`update_area`; adicionado `list_zonas`, `create_zona`, `update_zona`, `delete_zona`
- `app/areas/admin_router.py`: endpoints `GET/POST /admin/area/zonas` e `PATCH/DELETE /admin/area/zonas/{id}`
- `alembic/versions/0031_zona_table.py`: cria tabela `zonas`, dropa coluna `boundary` de `areas`

## Mudanças frontend
- `apps/web/src/features/admin/zonas/zonas.service.ts`: novo service HTTP
- `apps/web/src/features/admin/zonas/zonas.page.ts`: página CRUD (list + create + edit + delete com confirmação)
- `apps/web/src/app/app.routes.ts`: rota `/admin/zonas`
- `apps/web/src/layouts/admin-shell.component.ts`: link "Zonas" com ícone `faLayerGroup` no sidebar

## Hierarquia
```
Area (tenant boundary)
  └── Zona (sub-divisão com polígono próprio)
         └── (futuro) preço mínimo por equipe por zona
```

## Bairros preservados
A tabela `neighborhoods` não foi alterada — estrutura mantida intacta.
