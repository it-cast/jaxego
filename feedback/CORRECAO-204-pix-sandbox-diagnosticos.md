---
classe: fix
data: 2026-07-06
arquivos_afetados:
  - apps/api/app/payments/safe2pay_adapter.py
  - apps/api/app/payments/router.py
---

## Problema

`SAFE2PAY_SANDBOX=true` persistia no container mesmo após alterar o `.env` para `false`.
`docker compose restart` reinicia o container existente sem reler o `env_file` do docker-compose.
O container precisava ser recriado com `--force-recreate` para carregar os novos valores.

Adicionalmente, `_post_v3` não logava o body do erro 4xx da Safe2Pay, impossibilitando diagnóstico de falhas no endpoint PIX Automático.

## Causa Raiz

- `docker compose restart` → mantém env vars baked na criação original do container
- `docker compose up -d` (sem `--force-recreate`) → só recria se a configuração do compose mudou, não quando o conteúdo do `env_file` muda
- Solução: `docker compose -f infra/docker-compose.yml up -d --force-recreate api worker`

## Correções

### 1. Container recriado

```bash
docker compose -f infra/docker-compose.yml up -d --force-recreate api worker
```

Confirmado: container agora tem `SAFE2PAY_SANDBOX=false`.

### 2. Log de diagnóstico no router (`subscribe_attempt`)

Adicionado `logger.info("subscribe_attempt", method=..., pix_recorrente=..., plan_id=...)` antes do
branch card/pix. Permite confirmar que `pix_recorrente=true` chega ao backend quando o toggle está
ativado no frontend.

### 3. `_post_v3` agora loga body do erro

Antes: `logger.error("safe2pay_v3_http_error", status=...)` sem o corpo da resposta.
Depois: captura `resp.content` antes de fechar o contexto, extrai `Error`/`Message`/`detail`,
loga `s2p_error` + `s2p_code` + `url` — mesmo padrão do `_call_safe2pay`.

### 4. Log `safe2pay_pix_automatic_attempt` em `_create_pix_automatic`

Adicionado log no início do método para confirmar quando o caminho PIX Automático é atingido
(diferente de `safe2pay_pix_qr_attempt` que é do caminho PIX avulso).

## Observação para o usuário

Para testar **PIX Automático (recorrente)**: o toggle "Ativar débito automático (PIX Recorrente)"
precisa estar marcado **antes** de clicar o botão. Sem o toggle:
- Botão mostra "Gerar PIX" → chama `_create_pix_qr` (PaymentMethod 10, QR Code avulso)
- Log: `safe2pay_pix_qr_attempt`

Com o toggle marcado:
- Botão mostra "Autorizar PIX Recorrente" → chama `_create_pix_automatic`
- Log: `safe2pay_pix_automatic_attempt`
- Endpoint: `POST /v3/pix/automatic/authorizations` (sem sandbox — produção apenas)
