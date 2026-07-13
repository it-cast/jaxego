# CORRECAO-234 — Aprovação de documentos (KYC) é exclusiva do admin da equipe

## Data
2026-07-10

## Contexto
A revisão de documentos do entregador passou a ser responsabilidade do admin da
EQUIPE (/v1/team-admin), não mais do admin da cidade. Porém o gatilho de criação
da subconta Safe2Pay (RN-010) só existia no caminho antigo do admin da cidade —
entregador aprovado pela equipe ficava sem subconta.

## Mudanças

### Backend
- `teams/team_admin_router.py` approve_document: ao ativar o entregador
  (todos os docs aprovados), agora grava audit `courier.activated`
  (actor_type=team) e chama `register_subaccount_on_kyc_active` →
  cria a subconta S2P (/v2/marketplace/add) e salva s2p_recipient_id/s2p_token.
- `couriers/router.py`: removido `PATCH /v1/admin/couriers/{id}/documents/{doc_id}`
  (review do admin da cidade).
- `couriers/service.py`: removida a função `review_document` (substituída por
  comentário apontando o novo dono do fluxo).

### Web
- Removidos arquivos mortos do admin da cidade: `features/admin/kyc/kyc-detalhe.page.*`,
  `queue-table.component.*` e stories (a página nem estava roteada).
- `features/admin/kyc/kyc.service.ts`: removido o método `review()` — o admin da
  cidade só visualiza; aprovação vive em `features/equipe/equipe-kyc.service.ts`.
- `review-row.component` mantido (reusado pela tela da equipe); o SCSS da
  kyc-detalhe foi movido para `features/equipe/` (a página da equipe o reusava).

## Onde a subconta S2P é criada agora
Único caminho: admin da equipe aprova o último documento pendente →
courier.status=active → POST /v2/marketplace/add (Identity = CNPJ MEI ou CPF).
Gatilho secundário inalterado: validação de MEI (register_subaccount_on_mei_active).
