# Jaxegô — Stack

> Cada escolha com 1 linha de porquê. Versões travadas. Mudança de stack exige ADR.

## Backend

| Camada | Escolha | Porquê |
|---|---|---|
| Linguagem | Python 3.13 | Fluência do time + skills internas de qualidade (ruff/pytest/uv) já maduras. |
| Framework | FastAPI 0.115 | Async nativo, Pydantic v2, performance suficiente para I/O bound com p95 < 200 ms. |
| ORM | SQLAlchemy 2.x | Suporte completo a MySQL 8 (JSON, spatial), tipagem moderna. |
| Migrations | Alembic | Padrão SQLAlchemy, migra 1 schema único multi-área. |
| Banco | MySQL 8.0 | Expertise do time (skill mysql-expert), índices espaciais nativos para cobertura/geofence. |
| Cache/locks | Redis | Locks de despacho (aceite único), TTL de oferta como fonte de verdade, rate limit de API key. |
| Filas | arq (Redis) | Webhooks com retry exponencial, jobs de finalização/escrow/anonimização, sem peso de Celery. |
| Pacotes | uv | Resolve e instala em segundos; lockfile reproduzível. |
| Qualidade | ruff + basedpyright + pytest | Lint, tipos e testes no CI desde o commit 1. |

## Frontend / Mobile

| Camada | Escolha | Porquê |
|---|---|---|
| Framework | Angular 19 standalone + signals | Fluência do time, controle de fluxo novo (@if/@for), OnPush default. |
| UI mobile | Ionic 8 | Componentes mobile prontos com qualidade nativa; mesmo código web e app. |
| Empacotamento | Capacitor | APK Android no M1 (distribuição direta); lojas oficiais no M2. iOS pós-M1. |
| Estilo | SCSS + CSS vars geradas de tokens.json | Identidade num lugar só; nada de cor hardcoded. |
| Apps | 1 código, 3 superfícies | App do entregador (Ionic mobile-first), painel da loja (web responsivo), admin área/plataforma (web desktop-first). |

## Infra

| Camada | Escolha | Porquê |
|---|---|---|
| Hosting | VPS + Docker Compose | Custo proporcional ao M1; um compose sobe API, worker, Redis, MySQL. |
| Proxy | Nginx | TLS, gzip, rate limit de borda. |
| CI/CD | GitHub Actions | Lint → testes → build → deploy por tag; já usado pelo time. |
| Storage | Backblaze B2 (S3-compatible) | ~75% mais barato que S3; buckets privados para KYC/comprovações com URL assinada. |
| CDN | Cloudflare | Egress zero via Bandwidth Alliance; WAF e cache de assets. |
| Observabilidade | Sentry + Prometheus + logs estruturados stdout | Erros com contexto, métricas de despacho (tempo até aceite), sem stack pesada de APM. |

## Integrações (detalhe em docs-externos/integracoes.md)

| Serviço | Uso | Porquê |
|---|---|---|
| **Safe2Pay** | Assinaturas, cobrança por entrega (cartão/PIX), split para subconta do entregador, faturas (PIX/cartão/boleto) | PSP nacional com marketplace/split, PIX nativo e boleto para fatura mensal. Substitui Pagar.me (ADR-009 v2). |
| Receita Federal (API CNPJ) | Validação de loja e de MEI | Antifraude de cadastro (RN-011) e elegibilidade de saque (RN-010). |
| Zenvia ou Twilio | SMS transacional (momento "a caminho") | Quota por plano; um provedor primário + fallback. |
| AWS SES | E-mail transacional | Custo mínimo, alta entregabilidade. |
| Web Push (VAPID) | Push no app/PWA | Notificação grátis substitui SMS na maioria dos momentos. |
| OSRM ou Google Distance Matrix | Distância/ETA em rota | OSRM self-hosted gratuito no M1; Google como fallback pago [ASSUMIDO]. |
| Claude + OpenAI | Triagem de disputas, antifraude de foto (pós-M1), copys | Router próprio simples; tudo logado em ai_usage_log com custo. |
| Menu Certo | Primeiro cliente da API pública | API key por área + webhooks HMAC com retry. |

## Restrições e orçamentos

- `api_p95_ms`: 200 (endpoints quentes: criar entrega, aceitar oferta).
- `web_lcp_ms`: 2500 em 4G.
- Multi-área lógico: 1 banco, `area_id` em tudo (RN-001); sharding só se >50 áreas de alto volume (registrado como dívida).
- Timestamps UTC no banco; conversão na borda. Atenção a naive datetimes (lição auditada da v1.0).
- LGPD by design: PII mínima, buckets privados, anonimização agendada (RN-021).
- pt-BR em toda UI; código e schema em inglês.
