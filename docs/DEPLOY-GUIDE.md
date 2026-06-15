# Guia de Deploy — Jaxegô v1.0 (piloto Pádua, teste de produção)

**Objetivo:** subir o **núcleo de pagamento direto** para testar com usuários reais. Cartão/PIX online
e o back-office financeiro (saque/cobrança via PSP) ficam **desligados** até o contrato Safe2Pay
(DEC-004). Pré-requisitos abaixo são obrigatórios — sem eles a aplicação não sobe.

---

## 0. Pré-flight (uma vez)
- [ ] Host Linux com Docker + Docker Compose (ou Python 3.13 + uv, Node 20, MySQL 8, Redis 7).
- [ ] DNS/HTTPS apontando para a API e o front (reverse proxy: Caddy/Nginx).
- [ ] `.env` de produção criado a partir de `apps/api/.env.example` (NUNCA commitar). Ver §2.

## 1. Banco — validar migrations no SEU MySQL (BLOCKER #1)
> Nunca rodamos os testes `@mysql` ao vivo; faça isto ANTES de qualquer coisa.
```bash
cd apps/api
export DATABASE_URL="mysql+aiomysql://USER:SENHA@SEU_HOST:3306/jaxego?charset=utf8mb4"
uv sync --frozen
uv run alembic upgrade head            # aplica 0001..0013
uv run alembic downgrade -1 && uv run alembic upgrade head   # smoke de reversibilidade
uv run pytest -m mysql -q              # roda a suíte de integração MySQL (0004..0013)
```
Se algo falhar aqui, pare e me chame — é o risco desconhecido nº 1.

## 2. Variáveis de ambiente (BLOCKER #2 — secrets)
Mínimo para o piloto direto (do `apps/api/.env.example`):
```ini
ENVIRONMENT=production
JWT_SECRET=<gerar 32+ bytes aleatórios>
DATABASE_URL=mysql+aiomysql://USER:SENHA@HOST:3306/jaxego?charset=utf8mb4
REDIS_URL=redis://HOST:6379/0
SENTRY_DSN=<seu DSN>          # observabilidade
# Integrações do fluxo direto:
B2_KEY_ID=... B2_APP_KEY=... B2_ENDPOINT_URL=... B2_KYC_BUCKET=...   # docs KYC + comprovação
SES_SEND_URL=... SES_API_TOKEN=...     # e-mail (notificações)
SMS_ZENVIA_URL=... SMS_ZENVIA_TOKEN=... # SMS "a caminho"
GEOCODING_BASE_URL=...                 # endereços (Nominatim — ver TD-014)
OSRM_BASE_URL=...                      # ETA (fallback p/ mediana se ausente)
VAPID_PRIVATE_KEY=... VAPID_PUBLIC_KEY=... VAPID_CLAIM_SUB=mailto:... # push web
# Safe2Pay: DEIXAR como sandbox/vazio no piloto direto (ver §6).
SAFE2PAY_SANDBOX=true
REVENUE_SHARE_DEFAULT_PCT=10           # TD-13-01 — confirme com você antes de cobrar
```
Gere JWT_SECRET: `python -c "import secrets;print(secrets.token_urlsafe(48))"`.

## 3. Seed inicial (BLOCKER #3 — admin)
> O seed JÁ existe e é idempotente (cria Pádua + 4 planos + pesos de score + revenue share + admins).
```bash
cd apps/api
uv run python -m tools.seed
```
Cria:
- **admin de plataforma:** `admin@jaxego.com.br` (senha bootstrap `trocar-esta-senha-10` — **troque já**; no 1º login pede cadastro de TOTP).
- **admin de área (Pádua):** `padua.admin@jaxego.com.br` (mesma senha bootstrap).

## 4. Subir os serviços
Via compose (api + worker arq + mysql + redis):
```bash
cd infra
docker compose up -d --build
docker compose ps            # api, worker, mysql, redis saudáveis
curl -f https://SEU_HOST/health   # → 200
```
O **worker** (arq) roda os jobs: cascata de despacho, ciclo de entrega, notificações, jobs LGPD,
fatura mensal (cálculo), conciliação. Precisa estar de pé.

## 5. Frontend
```bash
cd apps/web
npm ci && npm run build        # dist/web/browser
# servir dist/web/browser pelo reverse proxy; SPA fallback p/ index.html
```

## 6. ⚠️ Decisão: comportamento de cartão/PIX no launch
Hoje `app/payments/factory.py` usa o **Safe2Pay real** em qualquer `environment` ≠ dev/test. Sem
contrato/chave, uma tentativa de cartão/PIX **falharia em runtime** (degrada para "indisponível";
direto segue). Para um piloto direto limpo, escolha:
- **(A) [recomendado] adicionar flag `payments_provider=stub`** (espelha `llm_provider`) — eu implemento;
  card/PIX fica desligado de forma explícita/controlada até o contrato. Decisão a tomar: stub **rejeita**
  (card/PIX "indisponível", honesto p/ piloto real) vs stub **aprova** (útil só p/ ambiente de teste).
- **(B)** manter como está e garantir que a **UI da loja só ofereça "direto"** (tela 12 já habilita só
  direto por padrão) — card/PIX nunca é acionado pelo usuário.
> Quando o contrato Safe2Pay fechar: preencher `SAFE2PAY_*`, resolver TD-10-01..04 + TD-15-01, flipar para
> o adapter real e validar split/escrow/estorno no sandbox antes de produção.

## 7. Smoke test do fluxo direto (validar o piloto)
1. Login admin plataforma → cadastra TOTP. Login admin de área (Pádua).
2. Admin de área: revisar 1 KYC de entregador (criar entregador de teste via `/entregador/cadastro`).
3. Loja: `/loja/cadastro` (plano Free) → `/loja/entregas/nova` (modalidade **direta**).
4. Entregador: receber oferta → aceitar → coletar → **comprovar** (foto + GPS).
5. Recebedor: abrir o link público `/r/<token>` → ver timeline + mapa → confirmar recebimento.
6. Conferir notificações (push/email) e a fatura interna sendo calculada (sem cobrança via PSP).

## 8. O que fica para depois (pós-contrato / pós-piloto)
- 🟡 Cartão/PIX online + split + escrow real, saque/repasse, cobrança da fatura, conciliação real (Phase 10/15).
- 🟡 APK assinado para os entregadores (CI gera debug; assinado = keystore + UAT — TD-14-04).
- 🟡 Lighthouse/p95 reais anexados de um run de CI (TD-14-03).
- 🟡 Self-host de tiles/Nominatim quando o volume exigir (TD-019/014).

---
*Referências: `.planning/phases/14-.../RELEASE-CHECKLIST.md` · `infra/docker-compose.yml` · `apps/api/.env.example`*
