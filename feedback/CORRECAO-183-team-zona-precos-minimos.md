# CORRECAO-183 — Team zona: preços mínimos por zona

## Arquivos criados
- `apps/api/alembic/versions/0032_team_zona.py`: migration criando tabela `team_zonas` com FK para `teams` e `zonas`, UniqueConstraint em `(team_id, zona_id)`, campo `preco_minimo_cents`
- `apps/api/app/teams/models.py`: modelo `TeamZona` adicionado
- `apps/api/app/teams/team_admin_router.py`: endpoints `GET /team-admin/zonas` e `PUT /team-admin/zonas/{zona_id}` para listar e configurar preços mínimos por zona
- `apps/web/src/features/equipe/equipe-zonas.service.ts`: service HTTP para os endpoints acima
- `apps/web/src/features/equipe/zonas.page.ts`: página de gestão de zonas com edição inline de preço mínimo

## Arquivos modificados
- `apps/web/src/app/app.routes.ts`: rota `/equipe/zonas` adicionada
- `apps/web/src/layouts/equipe-shell.component.ts`: link "Zonas" com ícone `faLayerGroup` adicionado ao nav

## Comportamento
- Time responsável acessa `/equipe/zonas` e vê todas as zonas da área
- Cada zona exibe o preço mínimo configurado (badge verde) ou "Não configurado" (badge cinza)
- Botão de lápis abre edição inline com campo numérico; confirmar salva via PUT (upsert)
- Filtro de busca por nome e paginação (mesma estrutura das páginas de equipe)
