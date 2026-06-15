# RELEASE CHECKLIST — Jaxegô v1.0 (piloto Pádua)

**Data:** 2026-06-11 (autopilot) · **Gera:** Phase 14 (release-safety) · **Deploy bloqueado se houver BLOCKER aberto.**

> Convenção: 🔴 BLOCKER (impede go-live) · 🟡 WARNING (resolver idealmente) · ✅ pronto · 🧑 UAT humano.

## 🔴 BLOCKERS de go-live

| # | Item | Estado | Origem |
|---|---|---|---|
| B-01 | **Contrato Safe2Pay assinado** — habilita cutover de produção do cartão/PIX com split + escrow | 🔴 PENDENTE | TD-10-01..04 (DEC-003/004). Dono escolheu cartão/PIX live no deploy → **exige contrato antes do go-live**. Sem contrato: subir só com pagamento direto e flag de cartão/PIX OFF. |
| B-02 | Segredos de produção configurados (`ANTHROPIC_API_KEY` opcional/infra, `safe2pay_*`, SMTP/SES, B2, Zenvia/Twilio, JWT secret, MySQL/Redis) | 🔴 VERIFICAR | settings; nunca em git. Conferir no ambiente de deploy. |
| B-03 | Migrations aplicadas em produção: `alembic upgrade head` (até 0012) com smoke `pytest -m mysql` das reversíveis (0004/0005/0006/0008/0010/0011/0012) | 🔴 VERIFICAR | CI roda `alembic upgrade head` + mysql; rodar contra a base de produção/staging antes do deploy. |
| B-04 | Seed de **admin de plataforma** | ✅ EXISTE — só rodar `uv run python -m tools.seed` (idempotente: Pádua + 4 planos + pesos score + revenue share + `admin@jaxego.com.br` + admin de área). Trocar senha bootstrap no 1º login. | `apps/api/tools/seed.py` |

## 🟡 WARNINGS (resolver idealmente antes do piloto)

| # | Item | Estado | Origem |
|---|---|---|---|
| W-01 | Revenue share % definido pelo dono (hoje `[ASSUMIDO 10%]` parametrizado) | 🟡 | TD-13-01 (OQ-1) |
| W-02 | Path da API pública alinhado com o integrador Menu Certo (`/v1/public/deliveries`) | 🟡 | TD-12-01 |
| W-03 | Relatório Lighthouse + p95 reais anexados de um run de CI | 🟡 | TD-14-03 (PERF-REPORT) |
| W-04 | Cache de auth da API key distribuído (hoje in-process; revoke já < 1min) | 🟡 | TD-12-02 |
| W-05 | GitHub remote configurado + CI validado em execução remota | 🟡 | STATE "Atenção item 5" |

## ✅ Prontos (verificados em dev/test)

- ✅ Suíte backend verde (`pytest -m "not mysql"`, ~472) + `ruff` limpo (exceto flaky pré-existente `test_health`, documentado)
- ✅ Suíte frontend verde (177) + build + lint; **zero hex** (3 exceções técnicas documentadas: mask `#000`, theme-color manifest)
- ✅ Jobs LGPD: anonimização 12m + exclusão 30d testados com dados sintéticos
- ✅ Infra LLM (router + ai_usage_log) pronta atrás de Stub — **nenhuma feature de IA ligada no M1**
- ✅ Fallback de ETA robusto (timeout + circuit breaker → mediana), métrica `eta_source`
- ✅ CI com gates: lint/typecheck/test (mysql+redis) + web (test/lint/build/zero-hex/lighthouse) + apk debug
- ✅ Health check `/health` (Phase 1, verificado ao vivo 200)
- ✅ Observabilidade: Sentry, logs estruturados, request_id, campos PII proibidos

## 🧑 UAT humano (não automatizável)

| # | Item | Origem |
|---|---|---|
| U-01 | APK debug instala em device Android real; câmera (comprovação), GPS (geofence/tracking) e push exercidos | REQ-051; CI gera APK debug em tag/dispatch |
| U-02 | Release assinado (keystore) + publicação — pós-piloto / M2 (iOS e lojas fora do M1) | TD do APK assinado |
| U-03 | Smoke visual das telas-chave (claro+escuro) num device/navegador real | webapp-testing |

## Escopo de pagamentos no deploy (DEC-004)
- **Live no deploy:** assinatura + cartão/PIX com split + escrow 24h (Phase 10) — **gated por B-01 (contrato)**.
- **NÃO no deploy:** fatura mensal, resolução financeira de disputas, saques, conciliação → **Phase 15 (pós-deploy)**.
- Caso B-01 não resolva a tempo: deploy do piloto com **pagamento direto** (1ª classe, ADR-012) e cartão/PIX desligado por flag até o contrato.
