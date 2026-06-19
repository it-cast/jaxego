# Correção 051 — Filtros de documento e status na página KYC do admin

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/web/src/features/admin/kyc/kyc-detalhe.page.ts`
- `apps/web/src/features/admin/kyc/kyc-detalhe.page.scss`

## Problema

A página de revisão KYC do admin (`/admin/kyc/:courierId`) exibia todos os documentos de todas as versões sem distinção. Quando um entregador reenviava documentos, apareciam os rejeitados antigos e os novos em análise misturados, dificultando a revisão.

## Correção

- Filtro por **tipo de documento** (select: Todos / CPF+Selfie / CNH / CRLV / etc.) — opções dinâmicas a partir dos documentos existentes
- Filtro por **status** (select: Todos / Em análise / Aprovado / Reprovado / Aguardando envio) — default **"Em análise"** para o admin ver direto o que precisa revisar
- `filteredItems` (computed) aplica ambos os filtros sobre a lista completa
- Mensagem "Nenhum documento com esse filtro" quando a combinação não tem resultados
- Filtros aparecem apenas quando há documentos
