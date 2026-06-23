# Correção 090 — Validação de referência separada da transição de estado

> **Classe:** BUG · **Data:** 2026-06-22

---

## Arquivos afetados

### Backend (API)

- `apps/api/app/proofs/router.py` — novo endpoint `POST /v1/deliveries/{id}/proof/validate-reference` que valida sem transicionar

### Frontend (App entregador)

- `apps/app/src/features/entregador/comprovacao/proof.service.ts` — método `validateReference()` que chama o novo endpoint
- `apps/app/src/features/entregador/comprovacao/comprovacao.page.ts` — usa `validateReference` em vez de `submitReference`

## Problema

Ao validar o número do pedido, o endpoint `POST /proof/reference` fazia a transição `COLETADA → ENTREGUE` (e o router finalizava para `FINALIZADA`). Depois, quando o entregador clicava "Finalizar entrega", o `submitPhoto` tentava transicionar de `COLETADA → ENTREGUE` numa entrega já `FINALIZADA`, causando erro "Transição de status inválida: FINALIZADA → ENTREGUE".

## Correção

- Novo endpoint `POST /proof/validate-reference` que apenas compara o número informado com o `reference_number` da entrega e retorna `{ valid: true/false }` — sem criar proof, sem transição de estado
- O app agora usa este endpoint para validar (mostrando feedback OK/erro)
- A transição de estado só acontece quando o entregador clica "Finalizar entrega" via `submitPhoto`
- O fluxo fica: foto → validar número → "Finalizar entrega" (que envia foto ao backend → COLETADA → ENTREGUE → FINALIZADA)
