# CORRECAO-256 — Filtros de nome/categoria/status em /admin/lojas

## Data
2026-07-14

## Pedido
"Coloque um filtro de buscar loja no /admin/lojas, por nome, por categoria e
por status."

## O que já existia
Já tinha busca por nome (e documento mascarado) — um único `<input search>`
filtrando client-side. Faltavam categoria e status.

## O que mudou
`apps/web/src/features/admin/lojas/lojas-list.page.ts`:
- Dois `<select>` novos ao lado da busca por nome: categoria e status.
- **Categoria não é uma lista fixa** — `category` é texto livre no cadastro
  da loja (sem enum no backend, `Field(min_length=2, max_length=40)`). O
  dropdown é populado dinamicamente com as categorias distintas presentes na
  lista carregada (`categoryOptions` computed, ordenado alfabeticamente) —
  em vez de inventar uma taxonomia fixa que poderia não bater com o que as
  lojas realmente cadastraram.
- Status é fixo (`active`/`pending_payment`/`pending_validation`/`suspended`
  — mesmos 4 valores que já existiam em `statusLabel()`).
- Filtragem continua client-side (mesmo padrão da busca por nome já
  existente — a lista inteira já vem de uma vez do `GET /v1/admin/merchants`,
  sem paginação server-side).
- Os 3 filtros (nome + categoria + status) combinam com AND.

## Build
`ng build web` — verde.
