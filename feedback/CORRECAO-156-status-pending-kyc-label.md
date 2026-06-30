# CORRECAO-156 — Label amigável para status pending_kyc

## Problema
Na listagem de entregadores em `/plataforma/pessoas`, o status `pending_kyc`
aparecia como texto cru em vez de um label legível.

## O que mudou

### Frontend (apps/web)
- **pessoas.page.ts**: Adicionado `pending_kyc: 'Aguardando documentos'` no
  mapa do método `statusLabel()`. Também corrigido de "Aguardando KYC" para
  "Aguardando documentos" após feedback do usuário (KYC não é termo familiar
  para o operador do painel).

## Arquivos alterados
- apps/web/src/features/admin-plataforma/pessoas.page.ts
