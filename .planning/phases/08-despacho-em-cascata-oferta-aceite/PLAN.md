# PLAN — Phase 8: Despacho em cascata + oferta + aceite

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Transformar uma entrega `CRIADA` (Phase 7) em `ACEITA` via **cascata sequencial** de ofertas (favoritos → ranking automático, nunca broadcast — RN-009), cada uma com **timeout cuja fonte de verdade é o Redis TTL** (ADR-104), terminando num **aceite único garantido por lock** (Redis `Lock` + `SELECT … FOR UPDATE` + máquina de estados idempotente) que sobrevive a corrida de rede (F-05 E3 — segundo aceite recebe 409 sem penalidade). Entregar o app do entregador (home online/offline + sheet de oferta com cronômetro, destino só **bairro + distância** — RN-013) e as listas de favoritos/bloqueados da loja (RN-014). A entrega **para em ACEITA** — coleta/comprovação é Phase 9, cobrança é Phase 10.

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] **Teste de corrida (critério central):** 2 aceites simultâneos da mesma oferta → exatamente 1 vence (entrega → ACEITA), o 2º recebe 409 `OfferAlreadyTakenError` **sem penalidade** (`@pytest.mark.mysql` + Redis real). `tests/dispatch/test_accept_race.py` verde.
- [ ] **Teste de contrato de privacidade (RN-013):** payload de `OfferOut` **não contém** `dropoff_address`/`dropoff_number`/`dropoff_complement` — só `dropoff_neighborhood` + `distance_m` + origem completa + valor + cronômetro. `assert "dropoff_address" not in payload`. `tests/dispatch/test_offer_privacy.py` verde.
- [ ] **Redis TTL é a fonte de verdade do timer (ADR-104):** oferta expira pelo `SET ex=timeout_oferta_s`; timeout → próximo candidato da cascata; cronômetro do app é cosmético. `tests/dispatch/test_offer_ttl.py` verde.
- [ ] **Bloqueado nunca recebe oferta (RN-014):** courier bloqueado pela loja jamais aparece em `build_candidates` (nem favoritos nem ranking). Favoritos elegíveis vêm primeiro. `tests/dispatch/test_eligibility.py` verde.
- [ ] **Cascata esgotada (E1) + loja cancela durante cascata (E4):** E1 → loja notificada com 3 opções (aumentar frete/re-oferta, aguardar 2min, cancelar sem custo — RN-004); E4 → ofertas pendentes canceladas sem custo. `tests/dispatch/test_cascade.py` + `test_cancel_during_cascade.py` verdes.
- [ ] **OSRM degrada sem bloquear (REQ-054):** OSRM fora → haversine ×1.4 + flag `eta_degraded`; o despacho continua. `tests/integrations/test_routing.py` verde (Stub + caminho degradado).
- [ ] **Aceitar oferta p95 < 200ms** (endpoint quente — lock + FOR UPDATE não estouram o budget; push é enfileirado, nunca síncrono).
- [ ] **Wireframe-contract** de `04-entregador-home.html`, `05-entregador-oferta.html`, `15-loja-favoritos.html` coberto; coleta (Phase 9) e cobrança (Phase 10) fora.
- [ ] **`axe-core` zero violações críticas** na home, no sheet, no cronômetro, nas listas e no card do aceito (AA claro + dark — DEC-001).
- [ ] aware UTC (TD-010) em TODO timestamp de oferta/aceite/TTL; zero `datetime.utcnow()` no módulo `dispatch/`.
- [ ] Todos os testes relacionados passam (`cd apps/api && uv run pytest`) — inclui `-m mysql` no CI com Redis + MySQL reais.
- [ ] Lint limpo (`cd apps/api && uv run ruff check .`; lint de naive datetime TD-010 cobrindo `dispatch/`).
- [ ] Commit atômico por wave com mensagem padronizada.

## REQs referenciados

- **REQ-024** — Despacho em cascata (favoritos→ranking) com locks; cascata esgotada → opções da loja (E1); teste de concorrência 2 aceites; Redis TTL fonte de verdade; loja cancela → ofertas canceladas (E4).
- **REQ-025** — Oferta com privacidade do destino (RN-013): destino só BAIRRO + distância; endereço completo só após COLETADA; teste de contrato no payload.
- **REQ-012 (dados)** — Favoritos/bloqueados da loja na elegibilidade (`merchant_courier_favorites`/`_blocks`, area-scoped, UNIQUE por par).
- **REQ-054** — OSRM/ETA `[ASSUMIDO]` para ranking e estimativa, atrás de adapter com fallback haversine.

---

## Skills Consultadas

Cada skill abaixo teve regras aplicadas a uma ou mais tasks deste plano. Citar skill sem aplicação concreta é inválido (plan-checker flaga).

**Backend / concorrência / segurança / integração**

- `domain/fastapi-production-patterns` — T-03, T-04, T-05, T-08: endpoints `/v1/offers/active`, `/accept`, `/decline`, favoritos/blocks com Pydantic v2 `extra="forbid"`, RFC-7807, `get_current_user` + papel entregador, AreaScoped no WHERE (404 nunca 403), idempotência por header em escrita relevante (DRV-003).
- `product/api-design-contracts` — T-03, T-04: contrato de `OfferOut` (RN-013 por construção — schema separado SEM campos FULL) e `AcceptResponse`; versionamento `/v1`; erro tipado `OfferAlreadyTakenError(409)` / `NotOfferTargetError(404)`.
- `domain/mysql-schema-design` — T-01: migration 0007 `merchant_courier_favorites`/`merchant_courier_blocks` area-scoped, `UNIQUE(area_id, merchant_id, courier_id)`, FK RESTRICT (DRV-002), utf8mb4, soft delete em domínio, índices para a query de candidatos; reusa convenções das migrations 0002-0006.
- `systematic-debugging` — T-02, T-04, T-06: o **aceite único** é a peça crítica — Pitfall 3 (double-advance da cascata: compare-and-advance + lock `cascade:{id}`), Pitfall 1 (2º aceite recebe penalidade — proibido), Pitfall 5 (release de lock de outro dono — usar `Lock.release()`, nunca `DEL`). Teste de corrida real (2 coroutines) é o critério nº 1.
- `owasp-security` — T-01..T-08 (ver `## Threat model`): A01 (autorização da oferta = courier-alvo, posse no WHERE), A02 (VAPID key via env, `Lock.release` seguro), A03 (Pydantic `extra="forbid"`), A04 (invariante de aceite único no backend, rate limit, timeouts), A08 (idempotência), A09 (zero PII em log), A10 (allowlist SSRF do OSRM).
- `quality/observability-production` — T-03, T-04, T-06, T-07 (ver `## Observability checklist`): **KPI norte do projeto = tempo `criação→aceite`** (evento estruturado no aceite com `delivery_id`+`area_id`+`elapsed_ms`); eventos de oferta/aceite/recusa/expiração auditados com `request_id`; zero PII em log (só ids/states).
- `quality/senior-quality-bar` — T-01, T-05, T-09 (Gate 8): segredo VAPID nunca no repo (`Field(default=None)`), sem N+1 na montagem de candidatos (carga de coverage/pricing em lote, padrão `estimate.py`), endpoint de aceite com decisão de auth explícita, nenhum endpoint sem auth.
- `meta/orchestration-decision-tree` — T-06: decisão LOW-1 (arq job re-agendável vs loop vs keyspace notifications) — orquestração da cascata com `dispatch_offer_task` re-enfileirável (`_defer_by=timeout_oferta_s`), estado em Redis; tier map do RESEARCH (orquestração → API/arq worker; TTL → Redis; aceite → Redis+MySQL).

**UI (matriz UI obrigatória + flags Phase 8)**

- `ui-ux-pro-max` — T-10, T-11, T-12: editorial-técnica — cronômetro, valor (R$), distância (km), score (87,4) e placa em **mono**; persimmon como única cor de ação (botão Aceitar). Anti AI-slop: sem gradiente/glow no card de oferta, **sem confete** ao aceitar, cronômetro com motion **com intenção** (aro que esvazia, não pulso neon).
- `product/component-library-governance` — T-10, T-11, T-12: **reusar** `jx-availability-toggle`/`jx-state-badge`/`jx-data-table`/4 estados; novos componentes governados (story + baseline §10 do UI-SPEC): `jx-offer-sheet`, `jx-offer-timer`, `jx-favorite-row`, `jx-blocked-row`, `jx-accepted-courier-card`, `jx-score-chip`.
- `ux-advanced/design-tokens-system` — T-10: consumir só camada semântica (`var(--surface)`/`var(--brand)`) + adicionar **5 vars `--score-*`** derivadas mecanicamente de `color.score_level` (mesmo padrão das `--state-*` da Phase 7) em `_tokens.scss`/`_semantic.scss` (claro + dark). Nenhuma cor inventada; nenhuma var de superfície/texto/brand nova.
- `quality/accessibility-pro` — T-10, T-11, T-12: AA nos dois temas; cronômetro **não-só-visual** (`aria-live="polite"` por marcos abrir/10s/5s/expirar + número mono + aro — nunca cor-only); sheet `role="dialog"` + foco preso; touch ≥44px (Aceitar ~52px); score/estado nunca por cor sozinha; `axe-core` zero violações críticas.
- `ux-advanced/empty-states-polish` — T-10, T-12: home "Aguardando ofertas" (online, fila vazia) com copy calma + ponto pulsando lento; favoritos/bloqueados vazios; loja sem entregadores na cascata (E1).
- `br/ux-copywriting-ptbr` — T-10, T-11, T-12: sentence case, CTA verbo+objeto sem ponto ("Aceitar entrega", "Recusar"); E3 "Essa entrega acabou de ser aceita por outro entregador. Sem problema — a próxima é sua." (sem culpa); "Aguardando ofertas".
- `ux-advanced/gesture-touch-patterns` — T-11: sheet de oferta entra de baixo (bottom-sheet Ionic); **sem swipe-to-accept** (aceite acidental = corrida perdida → botão grande deliberado); recusar é toque secundário explícito; tap-feedback scale .97 respeitando reduced-motion.
- `product/micro-animations-delight` + `ux-advanced/motion-design-patterns` — T-11: **cronômetro** (motion não-trivial) — aro/barra que esvazia 100%→0%, aceleração de cor nos últimos ~5s (`--warning`→`--error`), entrada do sheet `motion.normal` `easing_out`; **toda** animação respeita `prefers-reduced-motion` (vira estático + texto). Cronômetro nunca é fonte de verdade — reforço sensorial do TTL do servidor (ADR-104).
- `mobile/push-notifications-architecture` — T-07, T-11: a oferta chega por **Web Push VAPID** via **fila arq** (nunca push síncrono no request); payload **sem PII** (só `delivery_id` + deep link + "Nova oferta"); idempotência de envio; degrade silencioso (polling de oferta ativa quando push indisponível); tap na notificação fora do app abre o sheet.
- `ux-advanced/data-tables-ux` — T-12: listas favoritos/bloqueados da loja (tela 15) sobre `jx-data-table` (listagem governada) — linhas com ação, estados loading/empty/error, `aria-sort`/teclado herdados.
- `quality/error-ux-patterns` — T-11 (ver `## Error UX checklist`): F-05 E1-E4, oferta expirada, perdeu a corrida — `role="status"` (não `alert`), sem culpa; falha de rede no aceite com retry idempotente.
- `ux-advanced/dark-mode-theming` — T-10 (DEC-001): as 5 `--score-*` e o estado ACEITA validados AA em claro **e** dark sobre `--surface-sunken`/`--surface-elevated`; lift de neutros baixos (`prata`/`probation`) no dark, mesmo tratamento de `--state-criada`/`--state-cancelada`.
- `product/visual-regression-testing` — T-10/T-11/T-12 (`touches_shared_components:true`): os 6 componentes novos governados (`jx-offer-sheet`, `jx-offer-timer`, `jx-favorite-row`, `jx-blocked-row`, `jx-accepted-courier-card`, `jx-score-chip`) ganham story + baseline visual (claro+dark, fases do cronômetro calmo/atenção/urgente + reduced-motion estático); baseline criado nesta phase, comparação automática consolidada na Phase 9/release.
- `domain/ionic-patterns` — T-10/T-11: app do entregador é Ionic/Capacitor (ADR-003); sheet de oferta usa bottom-sheet Ionic, home usa tabs/lifecycle Ionic; respeitar `ion-content` scroll, safe-area (notch), e o ciclo de vida (`ionViewWillEnter`) para re-sync da oferta ativa ao voltar do background (Page Visibility + Redis TTL fonte de verdade ADR-104).
- `ux-advanced/responsive-breakpoint-strategy` — T-12: a tela 15 (favoritos/bloqueados da loja) é web responsivo — listas em breakpoint único desktop-first com colapso para mobile do painel da loja; herda os breakpoints estabelecidos na Phase 3.

## Skills Dispensadas (com justificativa)

- `domain/saas-billing-canonical` / `domain/safe2pay-escrow-br` — **dispensadas**: esta phase para em ACEITA; cobrança da corrida é Phase 10/11 (RN-004 — só cobra após aceite, e o cálculo/cobrança não acontece aqui). Sem billing/subscription/payment/checkout nesta phase.
- `ux-advanced/file-upload-ux` — **dispensada**: comprovação foto+GPS é Phase 9 (deferido em CONTEXT). Nenhum upload nesta phase.
- `br/brazilian-forms` — **dispensada**: não há formulário novo de captura de dados pessoais/documentos nesta phase (favoritar é um toggle/busca leve; aceitar/recusar são botões; sheet não é form). Validação de body é Pydantic backend.
- `ux-advanced/saas-dashboard-patterns` — **dispensada**: a tela 15 (favoritos/bloqueados) é listagem governada simples sob `jx-data-table`, não um dashboard SaaS com widgets/KPIs. O card do aceito é componente pontual, não painel.
- `ux-advanced/payment-checkout-ux` / `ux-advanced/trust-safety-ux` (checkout) — **dispensadas**: sem checkout/pagamento nesta phase. (Confiança pós-aceite via `jx-accepted-courier-card` é coberta por `component-library-governance`/`ui-ux-pro-max`.)
- `br/lgpd-compliance` — **NÃO dispensada / consultada inline**: há PII de destino em risco (RN-013). A mitigação está no `## Threat model` (TH-2) e no `## Observability checklist` (TH-10): `OfferOut` sem campos FULL por construção; zero PII em log. Não há tela de consentimento/política nova nesta phase (o tratamento de PII do destinatário foi modelado na Phase 7), então a skill entra como princípio aplicado (minimização + zero-PII), não como task de UI dedicada.

---

## Tech debt deste plano (verificação obrigatória v0.8+)

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime (`urgency_class: pre_launch_high`) | Prazo inclui "toda phase com timestamps" — oferta/aceite/TTL têm timestamps. Entra: `expires_at`/`accepted_at` em **aware UTC** (`datetime.now(UTC)`); lint custom cobre `dispatch/`. | T-02, T-04, T-06 (critério de aceite explícito + lint) |
| TD-011 | Broadcast de despacho indisponível (`wont_fix_documented`) | **Não entra** — RN-009: broadcast é opt-in pós-M1, nunca default. A cascata sequencial desta phase é justamente a alternativa correta. Confirmado fora de escopo. | — |
| **TD-12-01 (NOVA)** | Web Push VAPID vs FCM no APK Android (LOW-3) | Criada nesta phase: M1 entrega `PushPort` + adapter VAPID + Stub; se o APK Capacitor exigir FCM, é **troca de adapter** (contrato isola). Sem confirmação do dono no piloto → registrar. `urgency_class: post_launch_30d`. | Registrada (não resolvida aqui) — ver `## Open questions` LOW-3 |

Demais TDs de `TECH-DEBT.md`: nenhuma outra com prazo nesta phase.

---

## Open questions / LOW confidence do RESEARCH (obrigatório)

Os 5 itens LOW do RESEARCH viram **task explícita** ou **decisão consciente de adiar** (Regra 12):

| Item RESEARCH | Confidence | Resolução neste plano |
|---------------|------------|------------------------|
| **LOW-1** — arq job re-agendável vs loop vs keyspace notifications p/ avanço no expire | LOW | **Decisão + Task T-06:** implementar `dispatch_offer_task` **re-enfileirável** (`_defer_by=timeout_oferta_s`), estado em `offer:{id}` (TTL) + `dispatch:{id}:candidates` (fila ordenada); avanço idempotente por compare-and-advance + lock `cascade:{id}` (Pitfall 3). Decisão documentada no PLAN; não fica "verificar depois". |
| **LOW-2** — fakeredis vs Redis real no teste de corrida | LOW | **Decisão + Task T-02:** **preferir Redis real** (compose já tem) sob marker `@pytest.mark.mysql`/integração para o teste de corrida (fidelidade do `Lock`); fakeredis como fallback rápido só no caminho **não-concorrente**. `conftest.py` provê ambas as fixtures. |
| **LOW-3** — Web Push VAPID vs FCM no APK Android | LOW | **TD-12-01** (post_launch_30d): contrato `PushPort` isola; troca de adapter se o APK exigir FCM. Confirmar com o dono no piloto. |
| **LOW-4** — contrato OSRM exato (perfil/versão self-hosted) | LOW | **Task T-05 + Gate 5:** adapter já degrada a 404/erro; `## Integration contracts` valida o contrato OSRM (`duration` s / `distance` m) contra o deploy real no `integration_check` (Gate 5). |
| **LOW-5** — payload mínimo de push sem PII | LOW | **Task T-07:** payload de push = `{delivery_id, deep_link, "Nova oferta"}` — **zero PII** (RN-013 + skill push); teste assertando ausência de endereço/telefone/nome no payload. |

---

## Threat model

Herdado do `## Security Baseline` do RESEARCH.md (10 ameaças). **Destaques desta phase:** TH-1 (race no aceite) e TH-2/TH-3 (PII do destino / localização do entregador).

| ID | Ameaça (STRIDE) | Vetor | Impacto | Likelihood | Mitigação | Task |
|----|-----------------|-------|---------|------------|-----------|------|
| **TH-1** | Race no aceite → dupla-aceitação (Tampering / lost update) | 2 entregadores aceitam no mesmo instante | **Crítico** | Médio | redis `Lock(f"accept:{id}", blocking_timeout=2)` + `SELECT … FOR UPDATE` (reusa `transition()`) + transição idempotente CRIADA→ACEITA. 2º → 409 **sem penalidade**. Defesa em profundidade. | T-04, T-02 |
| **TH-2** | Vazamento de PII do destino na oferta (RN-013) (Info Disclosure) | `OfferOut` inclui `dropoff_address`/número/complemento | **Alto** | Médio | Schema `OfferOut` separado, **sem campos FULL por construção** (model já isola); só `dropoff_neighborhood` + `distance_m`. Teste `assert "dropoff_address" not in payload`. | T-03 |
| **TH-3** | Localização dos entregadores online exposta à loja (Info Disclosure) | Endpoint da loja vaza coords dos candidatos | **Alto** | Baixo | Nenhum payload p/ a loja inclui localização de courier; a loja só vê nome/foto/placa/score **após** o aceite (ADR-007). | T-08, T-12 |
| **TH-4** | IDOR / autorização de oferta (EoP) | Entregador B aceita oferta de A; ou de outra área | Alto | Médio | Só o `courier_id == offer:{id}.courier_id` aceita (`NotOfferTargetError` → **404**, não 403); query filtra `area_id`. Posse no WHERE. | T-04 |
| **TH-5** | Bloqueado recebe oferta (RN-014) | Filtro de bloqueados esquecido na montagem | Médio | Médio | Bloqueados removidos por set-difference (area+merchant) **antes** de favoritos/ranking. Teste: bloqueado nunca em `build_candidates`. | T-02, T-06 |
| **TH-6** | Replay / abuso de aceite (Tampering) | Aceite reenviado; aceite após expiração | Médio | Baixo | Idempotência via máquina de estados (2º+ → 409); válido só enquanto `offer:{id}` existe e aponta p/ o courier; após `close_offer`/TTL → 404/409. | T-04 |
| **TH-7** | Push token / VAPID key vazando (Info Disclosure / Spoofing) | Chave privada no repo; PII no payload | Alto | Baixo | `VAPID_PRIVATE_KEY` só via env (`Field(default=None)` — Gate 8 FAIL-BLOCK se no repo). Payload sem PII (LOW-5). | T-07 |
| **TH-8** | DoS na cascata (DoS) | OSRM lento trava o worker; oferta nunca expira | Médio | Baixo | OSRM `httpx` timeout curto + fallback haversine (nunca bloqueia); rate limit de criação já existe (Phase 7); TTL atômico garante expiração mesmo com restart. Janela máxima finita. | T-05, T-06 |
| **TH-9** | SSRF via OSRM URL (SSRF) | `OSRM_BASE_URL` → metadata/IP interno | Alto | Baixo | Allowlist (`OSRM_ALLOWLIST_HOSTS`) no adapter (mesmo `_hosts()`/guard SSRF de `http.py`); rejeita IP privado/link-local. | T-05 |
| **TH-10** | PII em log durante o despacho (Info Disclosure) | Logar endereço/telefone do destinatário | Médio | Médio | Log só com ids/states (`delivery_id`, `courier_id`, `area_id`, contagem) — padrão `transition()`. Redação estrutural. | T-03, T-06, T-07 |

---

## Performance budget

Herdado de `.planning/config.json > performance_budget` para a UI; overrides de endpoint abaixo.

**Frontend** (app entregador + loja):
- LCP ≤ 2500 ms · INP ≤ 200 ms · CLS ≤ 0.1 · Bundle main ≤ 400 KB gzip.
- Sheet de oferta e cronômetro: entrada `motion.normal` (220ms) sem jank; `prefers-reduced-motion` → estático.
- Lazy loading: rota `/loja/favoritos` (tela 15) e o módulo do sheet carregados sob demanda.

**Backend** (endpoints quentes):
- **`POST /v1/offers/{delivery_id}/accept` p95 < 200ms** (endpoint quente, decisão sob pressão de tempo) — lock + FOR UPDATE não estouram; **push é enfileirado (arq), nunca síncrono** no request.
- `GET /v1/offers/active` p95 < 150ms (lê `offer:{id}` do Redis + dados não-PII).
- **Cascata não bloqueia:** `dispatch_offer_task` roda no worker arq, fora do request; OSRM com timeout curto + fallback (TH-8).
- N+1: **zero** na montagem de candidatos — coverage/pricing carregados em lote (padrão `estimate.py`); Gate 8 (senior-quality-bar) verifica.
- Connection pooling: dimensionado para o pico de criação de entregas da área (rate limit 30/min/loja já existe).

Medição: Lighthouse CI (frontend); `pytest-benchmark` no `accept` + Prometheus em prod (KPI tempo até aceite).

---

## Observability checklist

Aplicando `quality/observability-production`:

- [ ] **KPI norte do projeto — `tempo criação→aceite`:** no aceite, emitir evento estruturado `dispatch.offer.accepted` com `delivery_id`, `area_id`, `courier_id`, `elapsed_ms` (= `accepted_at − created_at`). Métrica de produto principal do Jaxegô.
- [ ] Eventos de cascata auditados (sem PII): `dispatch.offer.opened`, `dispatch.offer.declined`, `dispatch.offer.expired`, `dispatch.offer.accepted`, `dispatch.cascade.exhausted` (E1), `dispatch.offer.cancelled` (E4) — todos com `delivery_id`/`area_id`/`request_id`.
- [ ] `eta_degraded=True` logado (WARNING) quando OSRM cai no fallback haversine — observabilidade do degrade (TH-8), sem alarmar o entregador.
- [ ] Todo endpoint novo (`/offers/active`, `/accept`, `/decline`, favoritos/blocks) loga: `request_id`, `user_id`, `endpoint`, `method`, `status_code`, `duration_ms`.
- [ ] 4xx → WARNING (inclui 409 "já aceita" — é não-evento, não erro de servidor); 5xx → ERROR + alert.
- [ ] **Zero PII em log** (TH-10): nunca endereço/telefone/nome do destinatário; só ids/states. Redação estrutural central.
- [ ] `request_id`/`offer_id` não exibidos ao usuário final.
- [ ] `/healthz` inalterado (nenhum serviço de SO novo; só uma função adicionada à `WorkerSettings.functions`).

---

## Error UX checklist

Aplicando `quality/error-ux-patterns` (F-05 E1-E4):

- [ ] **E3 "perdeu a corrida"** (estado mais sensível): `jx-warn-banner` `role="status"` (NÃO `alert`, NÃO erro) — "Essa entrega acabou de ser aceita por outro entregador. Sem problema — a próxima é sua." Sem penalidade, sem culpa.
- [ ] **Oferta expirada** (E2/TTL): `role="status"` "Essa oferta expirou. Já estamos buscando a próxima pra você." Volta a "aguardando ofertas".
- [ ] **E1 cascata esgotada** (loja): `jx-warn-banner` `role="status"` com **3 opções de igual peso** (anti-dark-pattern): "Aumentar frete e chamar de novo" / "Aguardar e tentar em 2 min" / "Cancelar sem custo" (RN-004). Calmo, não alarmista.
- [ ] **E4 loja cancela durante cascata:** confirmação leve "Cancelar a entrega? Ninguém aceitou ainda, então não há cobrança."; entregadores com oferta pendente caem em "oferta expirada".
- [ ] **Falha de rede no aceite:** `jx-error-state` `role="alert"` "Não deu pra confirmar agora. Tentar de novo." + retry **idempotente** (mesmo `offer_id`; se outro levou → cai em E3, nunca aceita em duplicidade).
- [ ] Toast vs modal vs inline: sheet usa estados inline `role="status"`/`role="alert"`; nada de modal pesado sobre o sheet. Decisão consistente.

---

## Integration contracts

`integration_check: true` (ROADMAP) — validados pelo `gsd-integration-checker` (Gate 5) após execução:

| Contrato | Consumer | Provider | Assertion |
|----------|----------|----------|-----------|
| `GET /v1/offers/active` | `apps/web/src/features/entregador/oferta/*` (polling de oferta ativa) | `apps/api/app/dispatch/router.py` | resposta `OfferOut` tem `{loja_nome, pickup_address, dropoff_neighborhood, distance_km, value_cents, ttl_total_s, ttl_remaining_s}` e **NÃO** tem `{dropoff_address, dropoff_number, dropoff_complement}` (RN-013) |
| `POST /v1/offers/{delivery_id}/accept` | `apps/web/src/features/entregador/oferta/offer.service.ts` | `apps/api/app/dispatch/router.py` | body vazio/idempotency-key header; 200 `AcceptResponse{delivery_id, state:"ACEITA"}`; 409 `OfferAlreadyTakenError`; 404 `NotOfferTargetError` |
| OSRM `GET /route/v1/{profile}/{coords}` (LOW-4) | `apps/api/app/integrations/routing.py` (RoutingHttpAdapter) | OSRM self-hosted (`OSRM_BASE_URL`, allowlist) | resposta tem `routes[0].duration` (s) e `routes[0].distance` (m); 404/erro → adapter devolve `RouteResult(degraded=True)` (haversine ×1.4), **nunca raise** |
| Web Push VAPID (envio) | `apps/api/app/workers/dispatch.py` (`send_push_task`) | navegador/PWA via `pywebpush` (Stub em test) | payload `{delivery_id, deep_link, title:"Nova oferta"}` **sem PII** (LOW-5); `content_type="aes128gcm"`; envio na fila, idempotente |

---

## Tasks

### T-01 — Migration 0007: favoritos & bloqueados (RN-014)

- **Type:** migration
- **Files:** `apps/api/alembic/versions/0007_dispatch_favorites_blocks.py`, `apps/api/app/merchants/models.py` (+ `MerchantCourierFavorite`, `MerchantCourierBlock`)
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — area-scoped, `UNIQUE(area_id, merchant_id, courier_id)`, FK RESTRICT (DRV-002), utf8mb4, soft delete; índices p/ a query de candidatos; reusa convenções 0002-0006.
  - `quality/senior-quality-bar` — índices que evitam scan na montagem de candidatos (sem N+1 futuro).
- **Descrição:** Duas tabelas **separadas** (RN-014). Favoritos com coluna de **prioridade** (ordem da cascata — D-01). Bloqueios com `reason` (privado da loja) + `created_at` aware UTC. Pares loja↔entregador, area-scoped. Nenhum backfill.
- **Success:** `uv run alembic upgrade head` aplica; `uv run alembic downgrade -1` reverte; tabelas com UNIQUE + FK RESTRICT + índice por `(area_id, merchant_id)`. Models mapeados.
- **Estimate:** 2-3h
- **Depends on:** none

### T-02 — Wave 0: scaffolding de testes (conftest + corrida + privacidade + elegibilidade)

- **Type:** test
- **Files:** `apps/api/tests/dispatch/conftest.py`, `tests/dispatch/test_accept_race.py`, `tests/dispatch/test_offer_privacy.py`, `tests/dispatch/test_eligibility.py`, `tests/dispatch/test_offer_ttl.py`, `tests/dispatch/test_cascade.py`, `tests/dispatch/test_cancel_during_cascade.py`, `tests/integrations/test_routing.py`, `tests/integrations/test_push.py`; `apps/api/pyproject.toml` (deps)
- **Skills aplicadas:**
  - `systematic-debugging` — o teste de corrida (2 coroutines/clients aceitando) é o critério nº 1; assertar "1 vence" **E** "perdedor sem penalidade" (Pitfall 1).
  - `domain/fastapi-production-patterns` — fixtures async (pytest-asyncio `auto`), marker `mysql` p/ FOR UPDATE.
- **Descrição:** Cria as fixtures (Redis **real** sob marker de integração + fakeredis para o caminho não-concorrente — **decisão LOW-2**; seed de couriers online/elegíveis, delivery CRIADA, favoritos/blocks). Testes começam **RED** (Nyquist — scaffolding antes da implementação). `uv add pywebpush` (runtime) + `uv add --group dev fakeredis`. Lint TD-010 estendido a `dispatch/`.
- **Success:** suíte coleta sem erro de import; `test_accept_race` existe e falha por ausência de implementação (RED); `fakeredis`/`pywebpush` instalados; `uv.lock` regenerado.
- **Estimate:** 3-4h
- **Depends on:** T-01

### T-03 — Schema de oferta `OfferOut` (RN-013) + endpoint `GET /v1/offers/active`

- **Type:** new_endpoint
- **Files:** `apps/api/app/dispatch/schemas.py` (`OfferOut`, `AcceptResponse`), `app/dispatch/offer_state.py` (wrapper Redis: `open_offer`/`current_offer`/`close_offer`, TTL helpers), `app/dispatch/router.py` (GET active), `app/dispatch/exceptions.py`
- **Skills aplicadas:**
  - `product/api-design-contracts` — `OfferOut` **separado**, sem campos FULL por construção (nunca `from_orm` do model inteiro — Pitfall 2); `/v1`.
  - `domain/fastapi-production-patterns` — `get_current_user` + papel entregador; AreaScoped; RFC-7807.
  - `quality/observability-production` — eventos sem PII; `quality/accessibility-pro` (contrato `ttl_total_s`/`ttl_remaining_s` p/ o cronômetro a11y).
- **Descrição:** `OfferOut` expõe só `{loja_nome, pickup_address, dropoff_neighborhood, distance_m/km, value_cents, ttl_total_s, ttl_remaining_s, eta_min, eta_degraded}`. `GET /offers/active` devolve a oferta corrente do courier autenticado (lê `offer:{id}` do Redis — fonte de verdade do timer, ADR-104) ou 204. `offer_state.py` usa `datetime.now(UTC)` (TD-010).
- **Success:** `tests/dispatch/test_offer_privacy.py` verde (`assert "dropoff_address" not in payload`); `test_offer_ttl.py` lê `ttl_remaining_s` do Redis; GET active responde 200/204.
- **Estimate:** 3-4h
- **Depends on:** T-01, T-02

### T-04 — Aceite único (lock) + recusa — `POST /accept`, `/decline` (peça crítica, F-05 E3)

- **Type:** new_endpoint
- **Files:** `apps/api/app/dispatch/service.py` (`accept_offer`, `cancel_pending_offers`), `app/dispatch/router.py` (POST accept/decline)
- **Skills aplicadas:**
  - `systematic-debugging` — Redis `Lock` + `FOR UPDATE` + máquina de estados idempotente; 2º aceite → 409 **sem penalidade** (Pitfall 1); `Lock.release()` nunca `DEL` (Pitfall 5).
  - `owasp-security` — A01 (autorização courier-alvo → 404 `NotOfferTargetError`), A04 (invariante no backend), A08 (idempotência).
  - `quality/observability-production` — emite `dispatch.offer.accepted` com `elapsed_ms` (**KPI tempo até aceite**).
  - `domain/fastapi-production-patterns` — idempotency-key header; p95 < 200ms (push enfileirado, não síncrono).
- **Descrição:** `accept_offer` reusa `transition()` (Phase 7, já com FOR UPDATE) sob `Lock(f"accept:{id}", blocking_timeout=2)`; set `courier_id` antes da transição CRIADA→ACEITA; em sucesso `close_offer` + `cancel_pending_offers` + enqueue push (fila). 2º aceite cai em lock-miss / estado≠CRIADA / `InvalidTransitionError` → `OfferAlreadyTakenError(409)`. `/decline` → avança a cascata (compare-and-advance). aware UTC (TD-010).
- **Success:** **`tests/dispatch/test_accept_race.py` verde** (2 aceites simultâneos: 1 ACEITA, 1 → 409 sem registro de penalidade) com `@pytest.mark.mysql` + Redis real; `accept` p95 < 200ms (pytest-benchmark); idempotência (retry mesmo `offer_id` não dupla-aceita).
- **Estimate:** 4-5h
- **Depends on:** T-03

### T-05 — Adapter OSRM (`RoutingPort`) + Stub + fallback haversine + ranking (REQ-054, D-02, D-08)

- **Type:** infra
- **Files:** `apps/api/app/integrations/base.py` (+`RoutingPort`, `PushPort`, `RouteResult`), `app/integrations/routing.py` (RoutingHttpAdapter), `app/integrations/routing_stub.py` (haversine determinístico), `app/integrations/factory.py` (+`get_routing_adapter`), `app/dispatch/ranking.py` (`rank_key`), `app/core/config.py` (`OSRM_BASE_URL`, `OSRM_ALLOWLIST_HOSTS`)
- **Skills aplicadas:**
  - `owasp-security` — A10 SSRF: allowlist `_hosts()` (mesmo guard de `http.py`); rejeita IP privado.
  - `domain/fastapi-production-patterns` — adapter Protocol + factory (Stub em dev/test); httpx timeout curto.
  - `quality/senior-quality-bar` — OSRM **nunca raise** ao caller (Pitfall 4); degrade → `eta_degraded`.
- **Descrição:** `RoutingPort.route()` → `RouteResult(distance_m, duration_s, degraded)`. Adapter httpx contra OSRM `/route/v1` (`duration` s, `distance` m); erro/timeout → haversine ×1.4 + `degraded=True`. `rank_key(eta_s, load, price_cents, score)` — **score com peso 0 no M1** (ADR-013), presente na assinatura. Ranking reusa `effective_price_cents` (Phase 6).
- **Success:** `tests/integrations/test_routing.py` verde (Stub + caminho degradado: OSRM fora → haversine + `eta_degraded`, sem exceção); `rank_key` ordena por (eta, carga, preço) determinístico; SSRF allowlist testado.
- **Estimate:** 3-4h
- **Depends on:** T-02

### T-06 — Cascata sequencial: `build_candidates` + `dispatch_offer_task` (LOW-1, RN-009, E1)

- **Type:** infra
- **Files:** `apps/api/app/dispatch/cascade.py` (`build_candidates`: favoritos→ranking, exclui bloqueados, reusa `is_eligible`/`compute_busy`/`effective_price_cents` em lote), `app/workers/dispatch.py` (`dispatch_offer_task` re-enfileirável), `app/workers/settings.py` (+ registrar na `functions`), `app/dispatch/offer_state.py` (+ `dispatch:{id}:candidates`, compare-and-advance)
- **Skills aplicadas:**
  - `meta/orchestration-decision-tree` — **decisão LOW-1:** arq job re-enfileirável (`_defer_by=timeout_oferta_s`), estado em Redis; avanço idempotente.
  - `systematic-debugging` — double-advance (Pitfall 3): lock `cascade:{id}` + geração da oferta; recusa só avança se `offer:{id}` ainda é do candidato.
  - `owasp-security` — TH-5 bloqueado nunca recebe oferta; RN-009 nunca broadcast (1 por vez).
  - `quality/observability-production` — eventos da cascata sem PII; `eta_degraded` logado.
- **Descrição:** `build_candidates` monta online+active+cobertura(coleta E entrega via `is_eligible`)+carga<max+**não bloqueado**; **favoritos primeiro** (por prioridade), resto por `rank_key`; **sem N+1** (lote, padrão `estimate.py`). `dispatch_offer_task` abre `offer:{id}` (TTL = `timeout_oferta_s` da área — D-03), enfileira push, re-agenda p/ TTL+ε; no expire avança ao próximo (favoritos esgotam → ranking; tudo esgota → evento E1 + notifica loja). Lê config da área (não cria config). aware UTC.
- **Success:** `tests/dispatch/test_eligibility.py` (bloqueado fora, favoritos primeiro), `test_offer_ttl.py` (timeout → próximo), `test_cascade.py` (E1 esgotada → opções da loja) verdes; nunca dois `offer.opened` no mesmo instante.
- **Estimate:** 5-6h
- **Depends on:** T-03, T-04, T-05

### T-07 — Adapter push VAPID + Stub + fila + cancelamento durante cascata (D-08, E4, LOW-5)

- **Type:** infra
- **Files:** `apps/api/app/integrations/push.py` (PushVapidAdapter — pywebpush, só prod), `app/integrations/push_stub.py` (PushStubAdapter — registra envios), `app/integrations/factory.py` (+`get_push_adapter`), `app/workers/dispatch.py` (`send_push_task`), `app/core/config.py` (`VAPID_PRIVATE_KEY`/`PUBLIC_KEY`/`CLAIM_SUB` = `Field(default=None)`), `.env.example`; hook E4 em `app/deliveries/service.py` (cancelar entrega CRIADA → `cancel_pending_offers`)
- **Skills aplicadas:**
  - `mobile/push-notifications-architecture` — fila arq (nunca síncrono no request); idempotência; **payload sem PII** (LOW-5: `{delivery_id, deep_link, "Nova oferta"}`); degrade silencioso.
  - `owasp-security` — TH-7: VAPID key via env (Gate 8 FAIL-BLOCK se no repo); `content_type="aes128gcm"` (GCM desabilitado).
  - `quality/senior-quality-bar` — segredo nunca no repo.
- **Descrição:** `PushPort` + adapter VAPID (pywebpush, síncrono → roda no worker) + Stub (sem rede). `send_push_task` enfileirado no abrir-oferta e no aceite (notifica loja+destinatário). **E4:** cancelar entrega CRIADA durante a cascata → `cancel_pending_offers` (DEL `offer:{id}`, ofertas pendentes caem em "expirada"), sem custo (RN-004).
- **Success:** `tests/integrations/test_push.py` verde (Stub registra envio; **payload sem PII** — `assert` ausência de endereço/telefone/nome); `tests/dispatch/test_cancel_during_cascade.py` verde (E4 cancela ofertas sem custo); nenhum segredo no repo.
- **Estimate:** 3-4h
- **Depends on:** T-04, T-06

### T-08 — CRUD favoritos/bloqueados (RN-014) — endpoints da loja

- **Type:** new_endpoint
- **Files:** `apps/api/app/merchants/favorites.py` (CRUD favorites/blocks + reorder de prioridade), `app/merchants/router.py` (+ rotas), `app/merchants/schemas.py` (+ schemas)
- **Skills aplicadas:**
  - `domain/fastapi-production-patterns` — `get_current_user` + papel loja; AreaScoped (404); Pydantic `extra="forbid"`.
  - `owasp-security` — TH-3: nenhum payload da loja inclui localização do courier; A01 posse no WHERE.
  - `product/api-design-contracts` — contratos de favoritar/bloquear/reordenar.
- **Descrição:** Endpoints da loja: listar/adicionar/remover favorito (com `reorder` de prioridade — D-01), listar/adicionar/remover bloqueio (privado — RN-014). Adicionar favorito só de quem já atendeu a loja (privacidade — não há marketplace aberto). Bloqueio nunca afeta score do entregador.
- **Success:** CRUD area-scoped; reorder persiste prioridade; bloqueio privado (motivo nunca exposto ao entregador); testes de contrato verdes.
- **Estimate:** 3-4h
- **Depends on:** T-01

### T-09 — Tokens de score: 5 `--score-*` derivadas de `color.score_level` (UI-SPEC §7.1, DEC-001)

- **Type:** ui_component
- **Files:** `apps/web/src/styles/_tokens.scss` (+5 primitivos `--jx-score-*`), `apps/web/src/styles/_semantic.scss` (+5 vars `--score-*` claro + `@mixin jx-dark-theme`)
- **Skills aplicadas:**
  - `ux-advanced/design-tokens-system` — geração **mecânica** de `color.score_level` (probation/bronze/prata/ouro/diamante); nenhuma cor inventada (Gate 2).
  - `ux-advanced/dark-mode-theming` — lift de neutros baixos (`prata`/`probation`) no dark; AA validado sobre `--surface-sunken`.
- **Descrição:** Adicionar os 5 primitivos + 5 vars semânticas, mesmo padrão das `--state-*` da Phase 7 (que vieram de `color.delivery_state`). Pré-requisito visual dos chips de score.
- **Success:** `--score-*` resolvem em claro e dark; contraste AA sobre `--surface-sunken`/`--surface-elevated` (axe); zero `#hex` hardcoded (Gate 2).
- **Estimate:** 1-2h
- **Depends on:** none

### T-10 — App entregador: home (tela 04) + `jx-score-chip` + `jx-accepted-courier-card`

- **Type:** ui_component
- **Files:** `apps/web/src/features/entregador/inicio.page.ts` (estados de despacho), `shared/components/score-chip/score-chip.component.ts` (`jx-score-chip`), `shared/components/accepted-courier-card/accepted-courier-card.component.ts` (`jx-accepted-courier-card`) + stories
- **Skills aplicadas:**
  - `product/component-library-governance` — reusar `jx-availability-toggle`/`jx-state-badge`/`jx-empty-state`; novos componentes com story + baseline.
  - `ux-advanced/empty-states-polish` — home offline / "Aguardando ofertas" (ponto pulsando lento, reduced-motion → estático).
  - `br/ux-copywriting-ptbr` — copy calma sentence case.
  - `quality/accessibility-pro` — score/estado nunca cor-only (texto+valor mono); touch ≥44px.
  - `ui-ux-pro-max` — placa/score/valor em mono; anti AI-slop.
- **Descrição:** Home (tab Início): header + `jx-availability-toggle` (reuso Phase 6) + 4 estados de despacho mutuamente exclusivos (offline / aguardando / oferta ativa → abre sheet §3 / em uma entrega). `jx-score-chip` (5 níveis, texto+mono+cor). `jx-accepted-courier-card` (foto/nome/placa mono/score/`jx-state-badge` ACEITA — visível à loja; **sem** localização do courier — TH-3).
- **Success:** wireframe-contract de `04-entregador-home.html` coberto; `jx-score-chip` 5 níveis + card com/sem foto em stories claro+dark; axe zero violações críticas.
- **Estimate:** 4-5h
- **Depends on:** T-03, T-09

### T-11 — `jx-offer-sheet` + `jx-offer-timer` (tela 05, RN-013, cronômetro motion não-trivial)

- **Type:** ui_component
- **Files:** `apps/web/src/features/entregador/oferta/offer-sheet.component.ts` (`jx-offer-sheet`), `offer-timer.component.ts` (`jx-offer-timer`), `offer.service.ts` (GET active polling + accept/decline) + stories
- **Skills aplicadas:**
  - `ux-advanced/gesture-touch-patterns` — bottom-sheet Ionic; **sem swipe-to-accept**; Aceitar ~52px deliberado; tap-feedback scale .97 (reduced-motion → sem scale).
  - `product/micro-animations-delight` + `ux-advanced/motion-design-patterns` — cronômetro aro/barra que esvazia + aceleração de cor últimos ~5s (`--warning`→`--error`); reduced-motion → estático.
  - `quality/accessibility-pro` — sheet `role="dialog"` foco preso (Esc não fecha); cronômetro `aria-live` por marcos (abrir/10s/5s/expirar) + mono; nunca cor-only.
  - `quality/error-ux-patterns` — estados pós-decisão: ganhou / **perdeu a corrida (E3, `role="status"` sem culpa)** / expirou / falha de rede (retry idempotente).
  - `mobile/push-notifications-architecture` — push acorda → sheet sobe; degrade → polling.
  - `br/ux-copywriting-ptbr` — copy E3 sem culpa.
- **Descrição:** Sheet de oferta: cabeçalho (loja + cronômetro) · origem completa (coleta) · **destino só bairro + distância (RN-013 — nunca renderiza rua/número/destinatário)** · valor da corrida (mono `--brand`) · Aceitar/Recusar · estados terminais (§3.5). `jx-offer-timer` é **cosmético** (ADR-104) — re-sync ao valor autoritativo do servidor; nunca decide expiração sozinho.
- **Success:** wireframe-contract de `05-entregador-oferta.html` coberto; **nenhuma tela renderiza endereço completo/destinatário do destino** (RN-013 verificada na UI); stories oferta-ativa/processando/ganhou/perdeu-corrida/expirou/falha-rede + cronômetro calmo/atenção/urgente/reduced-motion em claro+dark; axe zero críticas.
- **Estimate:** 5-6h
- **Depends on:** T-03, T-04, T-10

### T-12 — Loja: favoritos & bloqueados (tela 15) — `jx-favorite-row` / `jx-blocked-row`

- **Type:** ui_component
- **Files:** `apps/web/src/features/loja/favoritos/favoritos.page.ts`, `shared/components/favorite-row/favorite-row.component.ts`, `shared/components/blocked-row/blocked-row.component.ts` + stories
- **Skills aplicadas:**
  - `ux-advanced/data-tables-ux` — duas listas separadas sobre `jx-data-table`/listagem governada; estados loading/empty/error.
  - `product/component-library-governance` — `jx-favorite-row` (posição·nome·`jx-score-chip`·stats·↑↓·remover) / `jx-blocked-row` (nome·data/motivo privado·desbloquear).
  - `quality/accessibility-pro` — ↑↓ por teclado ≥44px (não drag); primeiro/último com seta `aria-disabled`.
  - `br/ux-copywriting-ptbr` — "Favoritos recebem suas ofertas primeiro…"; confirmações leves (remover ≠ bloquear).
  - `ux-advanced/empty-states-polish` — listas vazias.
- **Descrição:** Tela 15 (loja, web): lista de favoritos com reorder ↑↓ (prioridade da cascata — D-01) e adicionar/remover; lista de bloqueados com desbloquear (motivo **privado** — RN-014, nunca exposto ao entregador). Consome T-08.
- **Success:** wireframe-contract de `15-loja-favoritos.html` coberto; reorder persiste; bloqueio privado; stories com-favoritos/vazios/loading em claro+dark; axe zero críticas.
- **Estimate:** 4-5h
- **Depends on:** T-08, T-09, T-10

---

## Execution order

Waves (grupos paralelizáveis). **`parallel-hint: back-front`** — após a Wave 1, o eixo backend (T-04/T-05/T-06/T-07/T-08) e o eixo frontend (T-09→T-10→T-11/T-12) podem progredir em paralelo, sincronizando pelos contratos de `OfferOut`/`accept` (T-03) e favoritos (T-08).

- **Wave 1 (paralelo):** T-01 (migration), T-09 (tokens score) — sem dependência.
- **Wave 2 (paralelo):** T-02 (testes Wave 0, depende T-01).
- **Wave 3 (paralelo):** T-03 (oferta+GET active), T-05 (OSRM+ranking), T-08 (CRUD favoritos) — todos dependem de T-01/T-02; T-05 só de T-02.
- **Wave 4 (paralelo):** T-04 (aceite único — crítico, depende T-03), T-10 (home+chips, depende T-03+T-09), T-12 (loja favoritos, depende T-08+T-09+T-10).
- **Wave 5 (paralelo):** T-06 (cascata, depende T-03+T-04+T-05), T-11 (sheet+cronômetro, depende T-03+T-04+T-10).
- **Wave 6:** T-07 (push+E4, depende T-04+T-06).

**6 waves, 12 tasks.**

---

## Reconciliation expectations

Ao fim da execução, o `/gsd:reconcile-state 8` verifica:

- Todos os arquivos listados em `Files` de cada task existem.
- Endpoints declarados (`/offers/active`, `/accept`, `/decline`, favoritos/blocks) têm handler implementado.
- Skills citadas de fato aplicadas: lock Redis + FOR UPDATE presentes no aceite; `OfferOut` sem campos FULL; allowlist SSRF no OSRM; payload de push sem PII; zero `datetime.utcnow()` em `dispatch/` (TD-010).
- Nenhum arquivo-fantasma; nenhuma feature fantasma.
- **Squad-review pós-execute** (ROADMAP: `post-execute: squad-review`) — revisão cruzada com foco em concorrência (TH-1) e privacidade (TH-2/TH-3).

Divergências entram em `RECONCILIATION.md` antes de fechar a fase.

---

## Rollback plan

Se este plano causar regressão:
- Revert dos commits `feat(phase-8/...)` por wave.
- Migration: `uv run alembic downgrade -1` (remove `merchant_courier_favorites`/`_blocks` — sem dados legados).
- Ops: `DEL offer:*` / `dispatch:*` no Redis (limpa estado de oferta órfão); remover `dispatch_offer_task` da `WorkerSettings.functions`; feature-flag de despacho off se houver oferta presa.

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: {presente | ausente | incompleto}
- Performance budget: {presente | N/A | incompleto}
- Observability checklist: {presente | N/A | incompleto}
- Integration contracts: {presente | N/A | incompleto}
- Revision iteration: {1 | 2 | 3 | final}
