# CORRECAO-124 — Refresh do status do entregador ao entrar na tela inicial

## O que mudou

### Frontend (apps/app)
- **inicio.page.ts**: Adicionado `await this.auth.loadMe()` no início do `ngOnInit`. Isso re-busca `/v1/auth/me` a cada vez que a tela inicial é aberta, atualizando o `status` no signal. Se os documentos do entregador forem aprovados enquanto ele está no app, o computed `kycPending` reflete a mudança imediatamente sem precisar relogar.

## Arquivos alterados
- apps/app/src/features/entregador/inicio.page.ts
