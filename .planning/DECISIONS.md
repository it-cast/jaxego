# DECISIONS — Jaxegô

> Gerado por `gsd-project-ingestor` em 2026-06-10 a partir de `projeto/decisoes-existentes/adrs.md`.
> ADRs 001–013 são pré-existentes (status Accepted). ADRs 101–104 são travadas para v1.1 — **não re-discutir**.
> Entries `derived` são decisões implícitas detectadas pelo ingestor. Novas decisões durante execução entram ao final.

---

## ADRs pré-existentes (Accepted)

| ID | Decisão | Não-negociável | Pendência | Fonte |
|---|---|---|---|---|
| ADR-001 | Multi-área: app única, shared DB, `area_id` em tudo; middleware de escopo; testes de isolamento 2+ áreas. Globais: `users`, `audit_log`, `ai_usage_log`. Rejeitadas: banco/área, schema/área, white-label | **SIM** | — | `adrs.md:7-11` |
| ADR-002 | Backend Python 3.13 + FastAPI 0.115 + SQLAlchemy 2.x + MySQL 8 + Redis + arq + uv. Rejeitadas: NestJS, Go, PHP | **SIM** | — | `adrs.md:13-16` |
| ADR-003 | Frontend Angular 19 + Ionic 8 + Capacitor; APK Android M1, iOS/lojas M2. Rejeitadas: RN/Expo, Flutter, PWA-only | **SIM** | — | `adrs.md:18-21` |
| ADR-004 | Storage Backblaze B2 + Cloudflare CDN; buckets privados, URL pré-assinada, SHA-256. Rejeitadas: S3+CF, R2, disco local | sim | — | `adrs.md:23-26` |
| ADR-005 | Auth JWT HS256 access 15min + refresh opaco em DB + argon2id + TOTP (obrigatório admin plataforma); lockout 5/15min. Rejeitadas: sessão cookie, Auth0/Cognito, bcrypt, MFA-SMS | **SIM** | — | `adrs.md:28-31` |
| ADR-006 | Cobertura por bairro default, catálogo curado pelo admin local, tudo vira polígono espacial; elegibilidade coleta E entrega. Rejeitadas: raio-only, bairro sem polígono, cobertura só de coleta | sim | — | `adrs.md:33-36` |
| ADR-007 | Despacho cascata favoritos→ranking; timeout configurável (default 20s/60s); lock no aceite; localização nunca exposta à loja. Rejeitadas: broadcast, escolha humana sempre, leilão reverso | **SIM** | — | `adrs.md:38-41` |
| ADR-008 | Comprovação multi-modal: foto+GPS obrigatórios (raio 80m default); referência como camada leve; OTP pós-M1 server-side. Rejeitadas: foto sem GPS, OTP sem foto, app do destinatário, NFC/QR | **SIM** | — | `adrs.md:43-46` |
| ADR-009 v2 | PSP **Safe2Pay** (supersede Pagar.me): assinatura, cobrança com split, fatura com boleto, saque. Escrow interno 24h mantido. Camada de pagamento atrás de interface própria. Rejeitadas: Pagar.me, Mercado Pago, Stripe, conta própria | sim | **[DECIDIR] OQ-3**: validar split/prazo de repasse/taxas no contrato — ajustar escrow se PSP já retiver | `adrs.md:48-53` |
| ADR-010 | Integração Menu Certo: API key por área + Idempotency-Key (cache 24h) + webhooks HMAC-SHA256 anti-replay + retry 8×. Rejeitadas: gRPC/GraphQL, WebSocket, polling, OAuth2 (v2) | sim | — | `adrs.md:55-58` |
| ADR-011 | Validação do entregador em 2 níveis (simples/completa), aprovação item a item pelo admin de área. Rejeitadas: 4 níveis, zero validação, IA-only no M1 | sim | — | `adrs.md:60-64` |
| ADR-012 | Pagamento direto ao entregador como modalidade de 1ª classe; taxa em fatura mensal; disputa mediada; sem MEI pode trabalhar no direto. Risco aceito: evasão de fatura (mitigada RN-025/027). Rejeitadas: intermediação 100%, direto sem registro, taxa cobrada do entregador | **SIM** | — | `adrs.md:66-71` |
| ADR-013 | Score sem consequência financeira no M1; exibido com componentes explicáveis; consequências na v1.1 com 90 dias de dados. Rejeitadas: consequência dia 1, score oculto | sim | — | `adrs.md:73-76` |

## ADRs v1.1 (travadas — escopo da release seguinte, não re-discutir)

| ID | Decisão | Fonte |
|---|---|---|
| ADR-101 | GPS tracking por HTTP polling 60–120s, filtro 50m, `delivery_locations` retenção 24h, Page Visibility pausa. Rejeitado: WebSocket. **⚠ PROMOVIDA PARA O M1 por DEC-002 (decisão do dono em 2026-06-10) — não é mais v1.1.** Especificação técnica permanece válida | `adrs.md:80` |
| ADR-102 | Gatilho de revisão de validação completa: 3ª área ativa OU 90 dias de operação (dívida de compliance — ver TD-002) | `adrs.md:81` |
| ADR-103 | Taxas versionadas temporalmente (`effective_from/until`); entrega usa taxa vigente na criação. **Nota do ingestor:** considerar antecipar o schema para o M1 (ver SUG-002) | `adrs.md:82` |
| ADR-104 | Timer de aceite configurável por área (10–60s, default 20s); Redis TTL fonte de verdade; cronômetro do app é visual. **Aplicada já no M1** (Phase 8) | `adrs.md:83` |

## Decisões derivadas pelo ingestor (`derived` — implícitas nos docs, sem ADR formal)

| ID | Decisão | Fonte | Tag |
|---|---|---|---|
| DRV-001 | Estados da entrega exatamente 7 no M1; novo estado exige ADR | RN-019 | derived |
| DRV-002 | Soft delete em tabelas de domínio; FK RESTRICT em transacionais; utf8mb4; UTC no banco | `regras.md:41` | derived |
| DRV-003 | API: versionamento `/v1/`, erros RFC 7807, paginação por cursor, idempotência por header em escrita relevante | `regras.md:40` | derived |
| DRV-004 | Frontend: signals, reactive forms, OnPush, standalone, lazy por rota | `regras.md:42` | derived |
| DRV-005 | pt-BR em toda UI; código e schema em inglês; vocabulário canônico do glossário em copy | `stack.md:60`, glossário | derived |
| DRV-006 | Receita Federal via minhareceita.org self-hosted primário + BrasilAPI fallback `[ASSUMIDO]` | `integracoes.md:59` | derived + assumido |
| DRV-007 | SMS: Zenvia primário + Twilio fallback; degrade para e-mail+push se ambos falharem | `integracoes.md:63-67` | derived |
| DRV-008 | Identidade visual canônica = `tokens.json` v2-jaxego (Persimmon #E84E1B + cream #FAF6EE + Inter Tight/Fraunces italic/JetBrains Mono); nada de cor hardcoded | `tokens.json`, `brand.md`, `stack.md:26` | derived |
| DRV-009 | Valores de planos/taxas implementados como dados parametrizados (seeds editáveis), nunca constantes em código — porque são `[ASSUMIDO]` | `visao-geral.md:45-54,66-67` | derived (decisão do ingestor) |
| DRV-010 | ~~Tracking público no M1 sem mapa em tempo real; timeline + estado apenas~~ **REVERTIDA por DEC-002 (2026-06-10): mapa em tempo real ENTRA no M1.** Tela 26 agora alinhada ao escopo | wireframe 26 × ADR-101 | derived (revertida) |

---

## Decisões durante execução

| ID | Decisão | Contexto | Impacto | Data |
|---|---|---|---|---|
| DEC-001 | **Dark mode entra no M1.** Toda superfície (entregador/loja/admin) suporta tema claro e escuro desde o piloto. `ux-advanced/dark-mode-theming` passa a ser skill obrigatória em toda phase com `has_ui: true`; `tokens.json` ganha variantes dark (geradas como CSS vars por tema, nada hardcoded — mantém DRV-008) | Dono optou por dark mode no M1 na revisão do DISCOVERY-REPORT (2026-06-10) | Phase 3 cria os tokens dark + theming no design system; phases de UID herdam. Sem TD pendente de dark mode | 2026-06-10 |
| DEC-002 | **Mapa de tracking em tempo real entra no M1** (reabre ADR-101, antes v1.1). GPS tracking por HTTP polling 60–120s, filtro de movimento 50m, tabela `delivery_locations` (retenção 24h pós-entrega), Page Visibility API pausa o polling; tiles OpenStreetMap/MapLibre. WebSocket permanece rejeitado. Supera DRV-010 | Dono pediu mapa ao vivo no piloto na revisão do DISCOVERY-REPORT (2026-06-10); tela 26 já previa "posição aproximada — atualiza a cada minuto" | Adiciona escopo à Phase 9 (tracking + polling de localização do entregador + mapa); TD-005 resolvida/cancelada; ADR-101 promovida | 2026-06-10 |
