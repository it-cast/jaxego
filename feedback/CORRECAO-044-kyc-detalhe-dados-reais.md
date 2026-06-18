# Correção 044 — Página KYC do admin reescrita: dados reais em vez de hardcoded

> **Classe:** COD/PROC · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/api/app/couriers/schemas.py` (adicionados `CourierDocumentAdminItem`, `CourierAdminDetailOut`)
- `apps/api/app/couriers/router.py` (adicionado `GET /v1/admin/couriers/{courier_id}`)
- `apps/web/src/features/admin/kyc/kyc.service.ts` (adicionados `CourierDetail`, `CourierDocumentAdmin`, `getCourier()`)
- `apps/web/src/features/admin/kyc/kyc-detalhe.page.ts` (reescrito)

## Problema

A página de revisão KYC do admin (`/admin/kyc/:id`) era toda hardcoded — nome fixo "João da Silva", CPF fictício "123.***.***-09", selfie já aprovada, CNH/CRLV/MEI mostrados mesmo sem existir no banco. Nenhuma chamada à API.

## Correção

**Backend:**
- Novo endpoint `GET /v1/admin/couriers/{courier_id}` — retorna dados do courier + lista de documentos reais (só os que existem no banco), area-scoped (TH-09)
- Schemas `CourierAdminDetailOut` e `CourierDocumentAdminItem` adicionados

**Frontend:**
- Página reescrita com `ngOnInit` que lê o `:id` da rota e chama `getCourier()`
- Mostra só os documentos reais do banco com status correto
- Carrega thumbnail via `viewUrl()` (presigned GET) para cada documento
- Approve/reject com update otimista + rollback em caso de falha
- Atualiza `courier.status` após decisão (backend retorna `courier_status`)
