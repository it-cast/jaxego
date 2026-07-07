---
classe: feature
data: 2026-07-07
arquivos_afetados:
  - apps/api/app/workers/tasks.py
  - apps/api/app/workers/settings.py
  - apps/api/app/payments/router.py
---

## Feature: cron de polling para autorizações PIX Automático pendentes

### Problema
O status da assinatura PIX só era atualizado quando o usuário estava na página
de cadastro (polling do frontend via `GET /assinatura`). Se saísse da página
antes da confirmação, a cobrança ficava para sempre como "EM ABERTO".

### Solução
Task `poll_pix_pending_authorizations` no arq worker, rodando a cada 2 minutos.

**Lógica:**
1. Busca todas as `merchant_subscriptions` com `billing_status='pending'`,
   `payment_method='pix'` e `pix_autorizacao_id IS NOT NULL`
2. Para cada uma, chama `payment.get_pix_authorization_status(authorization_id)`
3. Se Safe2Pay retornar `APROVADA` ou `ATIVA`:
   - Seta `billing_status = 'active'`
   - Seta `pix_autorizacao_status = s2p_status`
   - Marca o `platform_charges` mais recente com `status in ('open','pending')` como `'paid'`
4. Commit único por execução (se houve ativações)

**Por que não usar `activate_approved_pix`?**
Essa função cria um novo charge "open" para o primeiro ciclo — mas no fluxo de
cadastro o charge já existe (criado em `activate_pix`). Usá-la criaria dois charges.

### Fix adicional (router.py)
`GET /assinatura` também passou a marcar o charge existente como `paid` quando
detecta a autorização aprovada (fix feito em CORRECAO-208). O cron é o fallback
para quem saiu da página antes da confirmação.

### Registro
Cron adicionado em `settings.py`:
```python
cron(poll_pix_pending_authorizations, minute=set(range(0, 60, 2)))
```
Worker reiniciado — `cron:poll_pix_pending_authorizations` aparece nos logs de startup.
