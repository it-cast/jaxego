# Correção 103 — Perfil refatorado com subpáginas: Editar dados, Documentação, Avaliações

> **Classe:** COD · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend

- `apps/api/app/scores/router.py` — endpoint `GET /v1/couriers/{id}/ratings` para listar avaliações recebidas
- `apps/api/app/couriers/router.py` — endpoint `PATCH /v1/couriers/{id}/profile` para atualizar nome e senha

### Frontend (App)

- `apps/app/src/features/entregador/perfil.page.ts` — refatorado para menu estilo settings com avatar + 3 links + logout
- `apps/app/src/features/entregador/perfil/editar-dados.page.ts` (criado) — edição de nome e senha, exibição readonly de email/telefone/cpf
- `apps/app/src/features/entregador/perfil/documentacao.page.ts` (criado) — listagem de documentos com status, reenvio de reprovados
- `apps/app/src/features/entregador/perfil/avaliacoes.page.ts` (criado) — panorama com média + lista de avaliações com filtro por estrelas
- `apps/app/src/features/entregador/entregador.service.ts` — métodos `updateProfile()` e `listRatings()`
- `apps/app/src/app/app.routes.ts` — rotas `/perfil/editar-dados`, `/perfil/documentacao`, `/perfil/avaliacoes`

## Implementação

### Perfil (menu)
- Avatar + nome + veículo
- 3 itens clicáveis com chevron: Editar dados, Documentação, Avaliações
- Botão "Sair da conta"

### Editar dados
- Nome editável + nova senha (min 10 chars)
- Email, telefone, CPF exibidos como readonly (mascarados)
- Header com back para /perfil

### Documentação
- Lista de documentos com pills de status (aprovado/reprovado/pendente)
- Botão de reenvio para reprovados com modal bottom-sheet
- Header com back para /perfil

### Avaliações
- Panorama: média grande + total de avaliações
- Filtro por estrelas (select)
- Lista de avaliações com estrelas + comentário + data
- Header com back para /perfil
