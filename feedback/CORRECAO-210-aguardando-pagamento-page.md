---
classe: feature
data: 2026-07-07
arquivos_afetados:
  - apps/web/src/features/loja/cadastro/aguardando-pagamento.page.ts (novo)
  - apps/web/src/app/app.routes.ts
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
  - packages/shared/src/shared/features/auth/login.page.ts
  - apps/api/app/workers/settings.py
---

## Feature: página dedicada de aguardando pagamento PIX

### Problema
Após PIX submit no cadastro, o QR code ficava embutido na mesma página do cadastro.
Se o usuário saísse e voltasse a fazer login, não havia redirecionamento para o
pagamento pendente — o usuário chegava ao dashboard com status inconsistente.

### Solução
Nova página `/loja/aguardando-pagamento`:
- Faz `GET /assinatura` no load para buscar QR code e copia-e-cola
- Polling a cada 5s verificando `billing_status`
- Quando `active` → redireciona para `/loja`
- Mostra botão "Copiar código PIX"

### Fluxo atualizado

**Cadastro com PIX:**
1. Submit PIX → `POST /assinar` OK → redireciona para `/loja/aguardando-pagamento`
2. (antes: `pixPending = true` + polling no próprio cadastro)

**Login com pagamento pendente:**
- `loadMe()` retorna `status = 'pending_payment'`
- Login page redireciona para `/loja/aguardando-pagamento` em vez de `/loja`

**Cron:**
- Reduzido de a cada 2 minutos para 1×/hora (fallback para quem nunca volta ao sistema)

### Arquivos alterados
- `aguardando-pagamento.page.ts`: página nova standalone com polling + QR + copy
- `app.routes.ts`: rota `loja/aguardando-pagamento` registrada (pública, fora do shell)
- `cadastro.page.ts`: após PIX OK, navega para a nova página em vez de `pixPending.set(true)`
- `login.page.ts`: se `me.surface === 'loja' && me.status === 'pending_payment'` → `/loja/aguardando-pagamento`
- `settings.py`: cron `minute={30}` (1×/hora) em vez de `set(range(0, 60, 2))`
