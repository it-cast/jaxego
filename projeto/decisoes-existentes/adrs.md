# Jaxegô — Decisões arquiteturais (ADRs)

> Consolidado. Cada ADR: decisão, contexto, alternativas REJEITADAS com razão. ADRs marcadas [ASSUMIDO] vieram do gerador e aguardam validação. ADRs v1.1 são decisões já travadas para a release seguinte ao M1 (evitam re-discussão).

---

## ADR-001 · Multi-área: aplicação única, shared DB, `area_id` em tudo — **Accepted**

**Decisão:** uma aplicação só, dividida por **áreas** (cidade ou região de cidade). Shared database + shared schema + `area_id` em toda tabela de domínio; middleware injeta o escopo do token/chave; testes de isolamento com 2+ áreas em todo módulo. Tabelas globais: `users`, `audit_log`, `ai_usage_log`.
**Contexto:** cada cidade/região tem regras próprias (nível de validação, pisos, bairros, política de retorno), mas é o mesmo produto, a mesma malha de código e o mesmo time.
**Rejeitadas:** banco por área (custo e migrations multiplicados; entregador em 2 áreas exigiria sincronização); schema por área (DDL no onboarding de cidade, tooling MySQL pior); "multi-tenant" como produto white-label (não é o modelo — é UMA marca, Jaxegô, operando várias áreas).

## ADR-002 · Backend Python 3.13 + FastAPI + SQLAlchemy + MySQL 8 — **Accepted**

**Decisão:** FastAPI 0.115, SQLAlchemy 2.x, MySQL 8.0, Redis, arq, uv, ruff, pytest, basedpyright.
**Rejeitadas:** Node/NestJS (menos fluência do time); Go (produtividade menor sem ganho para I/O bound); manter PHP (stack em abandono ativo no grupo).

## ADR-003 · Frontend Angular 19 + Ionic 8 + Capacitor — **Accepted**

**Decisão:** um código Angular standalone/signals; app do entregador Ionic mobile-first (web + APK Android via Capacitor no M1), painel da loja web responsivo, admins desktop-first. iOS e lojas oficiais no M2.
**Rejeitadas:** React Native/Expo (troca de stack atrasa M1); Flutter (Dart sem fluência, web imaturo); PWA-only para o entregador (push/câmera/GPS em iOS limitados — por isso APK já no M1 e lojas no M2).

## ADR-004 · Storage Backblaze B2 + Cloudflare CDN — **Accepted**

**Decisão:** B2 S3-compatible para KYC e comprovações (buckets privados, URL pré-assinada, compressão, hash SHA-256), Cloudflare na frente (egress zero).
**Rejeitadas:** S3+CloudFront (~3× custo); R2 (maturidade/certificações na época da decisão); disco local (sem CDN/replicação).

## ADR-005 · Auth JWT (HS256) + refresh token + argon2id + TOTP — **Accepted**

**Decisão:** access 15 min em memória; refresh opaco em DB (httpOnly cookie no web, Secure Storage no app); argon2id; TOTP obrigatório para admin plataforma, disponível para os demais; lockout 5 tentativas/15 min.
**Rejeitadas:** sessão por cookie (ruim para app); Auth0/Cognito (custo + dependência num tema central); bcrypt (argon2id é o estado da arte); MFA por SMS (SIM swap + custo).

## ADR-006 · Cobertura por bairro como default, catálogo curado pelo admin de área — **Accepted**

**Decisão:** área define modo default (`neighborhood` no interior); catálogo oficial de bairros (inclui informais) curado pelo admin local; internamente tudo vira polígono espacial; elegibilidade exige cobertura na coleta E na entrega; exclusões valem nos dois pontos.
**Rejeitadas:** raio-only (impreciso em cidade de geografia irregular); bairro-only sem polígono (trava expansão a cidades grandes); cobertura só de coleta (recusa pós-aceite explode).

## ADR-007 · Despacho em cascata: favoritos → ranking automático — **Accepted**

**Decisão:** cascata sequencial com timeout configurável por área (default 20 s/oferta, 60 s janela de favoritos); ranking por distância em rota + score + carga + preço; lock transacional no aceite; lista de entregadores online com localização NUNCA exposta à loja.
**Rejeitadas:** broadcast simultâneo (racing dispatch — abandonado por iFood/Uber/Loggi); escolha humana sempre (fadiga em pico, oligarquia de escolhidos); leilão reverso (v2, nicho de entrega não urgente).

## ADR-008 · Comprovação multi-modal: foto+GPS obrigatórios; referência e OTP como camadas — **Accepted**

**Decisão:** foto com EXIF/GPS no raio (default 80 m) é obrigatória em TODA entrega; número de referência (caso Menu Certo) como camada leve; OTP server-side (entregador nunca vê o código) como camada forte — OTP pós-M1.
**Rejeitadas:** foto sem GPS (fraude trivial); OTP sem foto (não prova condição da mercadoria); app do destinatário (ninguém instala); NFC/QR (hardware/fricção).

## ADR-009 v2 · PSP: **Safe2Pay** (substitui Pagar.me) — **Accepted (supersede ADR-009 v1)**

**Decisão:** Safe2Pay para (a) assinatura recorrente da loja, (b) cobrança por entrega cartão/PIX com split para subconta do entregador, (c) fatura mensal de taxas com PIX/cartão/boleto, (d) transferência de saque. Escrow interno de 24h pós-FINALIZADA mantido. Conciliação diária contra extrato.
**Contexto da troca:** decisão de negócio desta rodada; Safe2Pay cobre marketplace/split + boleto (essencial para a fatura mensal do pagamento direto) com custo competitivo nacional.
**Rejeitadas:** Pagar.me (substituído por decisão de negócio; camada de pagamento fica atrás de interface própria — trocar de PSP de novo não pode doer); Mercado Pago (taxas variáveis, acoplamento ao ecossistema ML); Stripe (PIX/boleto limitados no BR); processar na conta própria (vira instituição de pagamento de fato — inviável).
**Pendência:** [DECIDIR] validar no contrato Safe2Pay: split disponível no plano contratado, prazo de repasse de subconta, taxas — ajustar escrow se o provedor já retiver.

## ADR-010 · Integração Menu Certo: API key por área + webhooks HMAC com retry — **Accepted**

**Decisão:** `POST /v1/deliveries` com `Idempotency-Key` obrigatório (resposta cacheada 24h); API keys `jx_live_/jx_test_` hasheadas, escopadas, rate-limited; webhooks assinados HMAC-SHA256 com timestamp anti-replay e retry exponencial em 8 tentativas; versionamento por URL.
**Rejeitadas:** gRPC/GraphQL (complexidade sem ganho para 1 operação central REST); WebSocket (custo de conexão permanente); polling (latência e custo); OAuth2 (justificável só com terceiros independentes — v2).

## ADR-011 · Validação do entregador em 2 níveis: simples e completa — **Accepted (nova)**

**Decisão:** dois níveis em vez de quatro. **Simples** = CPF validado + selfie com documento + telefone + e-mail. **Completa** = simples + CNH com EAR + CRLV + MEI ativo + antecedentes (se a área exigir). A área configura o nível mínimo; aprovação item a item pelo admin de área.
**Contexto:** 4 níveis eram granularidade sem demanda real; 2 níveis mapeiam o mundo real do interior ("confio nele" vs "quero papelada").
**Rejeitadas:** 4 níveis (complexidade de configuração e de UI sem benefício no M1); zero validação (risco legal e de marca inaceitável); validação 100% automatizada por IA no M1 (custo e falso negativo; admin local revisa melhor — IA entra como apoio pós-M1).

## ADR-012 · Pagamento direto ao entregador como modalidade de 1ª classe — **Accepted (nova)**

**Decisão:** a loja escolhe por entrega: cartão, PIX (via Safe2Pay, com split) ou **direto ao entregador** (dinheiro/PIX pessoal). No direto: plataforma não processa a corrida; entregador confirma recebimento na conclusão; taxa de plataforma acumula em fatura mensal da loja; "não recebi" abre disputa mediada pelo admin de área; reincidência da loja (2+ procedentes/30 dias) bloqueia a modalidade por 90 dias.
**Contexto:** no interior, dinheiro e PIX direto são o costume; exigir intermediação total criaria atrito letal à adoção. Bônus estrutural: entregador SEM MEI pode trabalhar (MEI só para repasse via plataforma — RN-024), destravando o onboarding da malha.
**Rejeitadas:** intermediação obrigatória de 100% dos pagamentos (atrito de adoção + exclui entregador sem MEI); modalidade direta sem registro (perderíamos a taxa e a telemetria); cobrar a taxa do entregador no direto (quem deve a taxa é a loja — o entregador não é cliente pagador da operação).
**Risco aceito:** evasão de fatura → mitigada por RN-025 (bloqueio >7 dias) e RN-027 (proteção do entregador).

## ADR-013 · Score sem consequência financeira no M1 — **Accepted (nova)**

**Decisão:** M1 coleta e EXIBE o score com componentes explicáveis (delta, pesos, motivo), mas não aplica consequência automática (taxa/prioridade). Consequências entram na v1.1 com 90 dias de dados reais.
**Rejeitadas:** consequência desde o dia 1 (sem base estatística → injustiça + risco PLP 152); score oculto (replicaria a opacidade do iFood que decidimos corrigir).

## ADRs v1.1 (travadas, não re-discutir)

- **ADR-101 · GPS tracking por HTTP polling** 60–120 s com filtro de movimento de 50 m, tabela `delivery_locations` com retenção de 24h pós-entrega, Page Visibility API pausa o polling. Rejeitado: WebSocket (custo desproporcional ao volume atual).
- **ADR-102 · Gatilho de validação completa**: terceira área ativa OU 90 dias de operação dispara revisão do nível exigido por área (dívida de compliance documentada).
- **ADR-103 · Taxas versionadas temporalmente**: `effective_from/effective_until` em planos e taxas; admin edita sem deploy; entrega usa a taxa vigente na criação.
- **ADR-104 · Timer de aceite configurável por área (10–60 s, default 20 s)** com Redis TTL como fonte de verdade; cronômetro do app é só visual.

## Assumidos desta conversa para revisão

- [ASSUMIDO] Valores dos planos e taxas (tabela em visao-geral.md).
- [ASSUMIDO] Fatura mensal: fecha dia 1º, vence dia 8, bloqueio >7 dias (RN-025).
- [ASSUMIDO] Saque manual mínimo R$ 20; automático semanal às terças.
- [ASSUMIDO] OSRM self-hosted para rotas; Google como fallback pago.
- [ASSUMIDO] SMS apenas no momento "a caminho"; resto via push/e-mail (RN-018).
- [ASSUMIDO] Reversão automática de suspensão quando o SLA de recurso estoura (RN-016).
- [ASSUMIDO] Bloqueio da modalidade direta por 90 dias após 2 disputas procedentes (RN-027).
- [ASSUMIDO] APK Android direto no M1; lojas oficiais no M2.
