# Correção 047 — Reenvio de documento reprovado na tela de Perfil do entregador

> **Classe:** COD/UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/api/app/couriers/schemas.py` (adicionado `id`, `reject_reason`, `reject_detail` ao `CourierDocumentItem`)
- `apps/api/app/couriers/router.py` (profile endpoint agora retorna campos de rejeição)
- `apps/app/src/features/entregador/entregador.service.ts` (interface atualizada)
- `apps/app/src/features/entregador/perfil.page.ts` (reescrito com modal de reenvio)

## Problema

Quando o admin reprovava documentos do entregador, não havia forma no app de ver o motivo da reprovação nem reenviar o documento. O entregador ficava preso com `pending_kyc` sem ação possível.

## Correção

**Backend:**
- `CourierDocumentItem` agora inclui `id`, `reject_reason` e `reject_detail`
- Endpoint `GET /v1/couriers/{id}/profile` retorna os motivos de reprovação

**Frontend (Perfil):**
- Documentos reprovados exibem status em vermelho ("Reprovado") + ícone de reenvio (fa-rotate-right, botão circular brand)
- Ao clicar no ícone, abre bottom-sheet modal com:
  - Nome do documento, status, motivo traduzido e detalhe do admin
  - Campo de anexo (jx-doc-card em modo edit, com preview e hideBadge)
  - Botões "Cancelar" e "Enviar para análise"
- Ao enviar: presign → upload → complete → status atualizado localmente para "Em análise"
- Se falhar, mostra erro sem fechar o modal
