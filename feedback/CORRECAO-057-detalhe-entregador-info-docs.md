# Correção 057 — Página de detalhe do entregador no admin com informações e documentos

> **Classe:** UX/COD · **Data:** 2026-06-19

---

## Arquivos afetados

- `apps/web/src/features/admin/governanca/entregador-detalhe.page.ts`
- `apps/web/src/features/admin/governanca/entregador-detalhe.page.html`
- `apps/web/src/features/admin/governanca/entregador-detalhe.page.scss`

## Problema

A página `/admin/entregadores/:courierId` mostrava apenas o ID do entregador, score e painel de suspensão. Não exibia dados pessoais (nome, CPF, veículo, status, data de cadastro) nem os documentos KYC.

## Correção

- Carrega dados do courier via `AdminKycService.getCourier()` (`GET /v1/admin/couriers/{id}`)
- Seção "Informações": grid com status, validação exigida, veículo/placa, data de cadastro
- Seção "Documentos": lista com kind + status (colorido: verde aprovado, vermelho reprovado, amarelo em análise) + link "Revisar →" para `/admin/kyc/:id`
- Header mostra nome completo + CPF mascarado em vez de só `#id`
- Link "← Entregadores" para voltar à lista
