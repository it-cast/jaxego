# Correção 071 — Página de áreas reescrita no padrão da página de planos

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/web/src/features/admin-plataforma/areas.page.ts` (reescrito)
- `apps/web/src/features/admin-plataforma/areas.page.html` (criado)
- `apps/web/src/features/admin-plataforma/areas.page.scss` (criado)

## Problema

A página de áreas usava um layout de cards inline com edição in-place, diferente do padrão adotado na página de planos (DataTable + filtro + form separado). Falta de consistência visual entre as telas do admin de plataforma.

## Correção

Reescrita completa seguindo o mesmo padrão da página de planos:
- Header com título + botão "+ Adicionar"
- Busca client-side por nome ou slug
- `jx-data-table` com colunas: ID, Slug, Nome, Validação, Ações
- Ícone de edição e arquivamento por row (fa-pen-to-square / fa-box-archive)
- Arquivamento com confirmação inline ("Arquivar?" + confirmar/cancelar)
- Form separado (card) para criar/editar com campos: slug (imutável na edição), nome, nível de validação (simples/completa)
- Feedback messages com `role="status"`
- Badge de validação (Simples = brand, Completa = warning)
- Template e SCSS extraídos para arquivos separados (antes era tudo inline no .ts)
