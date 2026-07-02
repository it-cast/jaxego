# CORRECAO-191 — Botão de edição e alinhamento à direita nos bairros

## Solicitação
Alinhar as ações da lista de bairros no canto direito e adicionar botão de edição.

## Mudanças

### Backend
- `apps/api/app/neighborhoods/schemas.py`: Adicionado `NeighborhoodUpdate` (PATCH parcial)
- `apps/api/app/neighborhoods/service.py`: Adicionado `update_neighborhood()`
- `apps/api/app/neighborhoods/router.py`: Adicionado `PATCH /v1/neighborhoods/{id}`

### Frontend
- `neighborhoods.service.ts`: Adicionado método `update()`
- `neighborhoods.page.ts`: Adicionado `faPencil`, `editingId`, `editName`, `startEdit()`, `cancelEdit()`, `saveEdit()`
- `neighborhoods.page.html`: Edição inline — nome vira input no modo edição, ações mostram salvar/cancelar; botão lápis aparece ao lado do lixo no modo normal
- `neighborhoods.page.scss`: `justify-content: flex-end` em `.jx-nbhd__actions`; novo `.jx-nbhd__inline-input`
