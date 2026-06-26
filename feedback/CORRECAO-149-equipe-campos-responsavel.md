# CORRECAO-149 — Campos de responsável e CNPJ no cadastro de equipes

## O que mudou

### Backend (apps/api)
- **teams/models.py**: Adicionados campos `cnpj` (opcional), `razao_social` (opcional), `responsavel`, `responsavel_cpf`, `responsavel_user_id` (FK → users)
- **alembic 0027**: Migration para adicionar as colunas na tabela teams
- **teams/schemas.py**: `TeamCreate` inclui dados do responsável + email + senha. `TeamUpdate` permite editar nome, cnpj, razão social, responsável e cpf. `TeamRead` retorna todos os campos + email do responsável
- **teams/service.py**: `create_team` cria o User (email + senha + cpf) e vincula como `responsavel_user_id`. Trata duplicata de email. `get_responsavel_email` busca o email do user vinculado
- **teams/router.py**: Serialização via `_team_read` que inclui o email do responsável

### Frontend (apps/web)
- **equipes.page.ts**: Form expandido com campos em grid 2 colunas:
  - Nome da equipe
  - CNPJ (opcional) + Razão social (opcional)
  - Responsável + CPF do responsável
  - Email + Senha (só no criar, não no editar)
  - Coluna "Responsável" na tabela
  - `formData` substitui `formName`

## Arquivos alterados
- apps/api/app/teams/models.py
- apps/api/alembic/versions/0027_team_fields.py (novo)
- apps/api/app/teams/schemas.py
- apps/api/app/teams/service.py
- apps/api/app/teams/router.py
- apps/web/src/features/admin/equipes/equipes.page.ts
