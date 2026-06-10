# PLAN — Phase 7 Plan 07-00: Criação de entrega + máquina de estados (modalidade direta)

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Entregar o coração transacional do Jaxegô: a **criação de entrega F-03 pela Loja na modalidade direta** e a **máquina de 7 estados** (RN-019) com histórico append-only (RN-012). Backend cria a migration 0006 (`deliveries`, `delivery_state_transitions` com trigger, `recipients`), define a máquina inteira (7 estados, transições válidas, `transition()` com lock pessimista), compõe a estimativa mediana (RN-030) sobre a elegibilidade espacial da Phase 6 e o gate de limite de plano (RN-028). Frontend entrega o form de nova entrega (tela 12), o `jx-state-badge` + 3 componentes governados, a lista (tela 14), o dashboard (tela 11) e o `jx-upgrade-modal` (E4). **Sem despacho (Phase 8), comprovação (Phase 9), cobrança online (Phase 10) ou fatura (Phase 11).** A entrega nasce `CRIADA` e fica aguardando.

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] Migration 0006 cria `deliveries`, `delivery_state_transitions`, `recipients` com convenções 0001-0005 (utf8mb4, FK RESTRICT, `DATETIME(6)`, `AreaScopedMixin`); `alembic upgrade head` e `downgrade -1` funcionam.
- [ ] `delivery_state_transitions` é append-only: `UPDATE`/`DELETE` → erro MySQL `SIGNAL 45000` (errno 1644) — teste `@pytest.mark.mysql` verde.
- [ ] Máquina de estados define os **7 estados completos** (RN-019); teste **exaustivo** de transições inválidas → `InvalidTransitionError(422)`.
- [ ] F-03 cria entrega no estado `CRIADA` (modalidade `direct`); `payment_method` `card`/`pix` → 422 "em breve" (D-02).
- [ ] Estimativa = mediana (centavos inteiros) das tabelas dos entregadores online elegíveis (RN-030); 0 elegíveis (E2) → cria com aviso (D-06); destino fora do catálogo (E1) → 422 fora-de-cobertura.
- [ ] Limite de plano (RN-028): 3ª entrega no Free → 402/409 com payload de upgrade (D-07); `CANCELADA` não conta no COUNT.
- [ ] IDOR (TH-03): Loja só vê/cria/cancela suas entregas; recurso de outra loja/área → **404**.
- [ ] PII do destinatário (telefone/endereço/CPF) nunca em log (TH-04); `recipients` guarda só `cpf_hash` (D-08).
- [ ] Concorrência (TH-01): 2 transições simultâneas → 1 vence via `FOR UPDATE` — teste de corrida `@pytest.mark.mysql` verde.
- [ ] Frontend: form tela 12, `jx-state-badge` (7 estados), lista tela 14, dashboard tela 11, `jx-upgrade-modal` — wireframe-contract de `12`/`11`/`14` coberto; zero `#hex` hardcoded; `axe-core` zero violações críticas nas 3 telas (claro+dark).
- [ ] Todos os testes relacionados passam (`make test`) e lint limpo (`make lint`).
- [ ] Commits atômicos com mensagem padronizada.

## REQs referenciados

- **REQ-021** — F-03 criação de entrega (pagamento direto primeiro; cartão/PIX na Phase 10).
- **REQ-022** — 7 estados append-only.
- **REQ-023** — estimativa de frete `[ASSUMIDO RN-030]`.
- **REQ-011 (parcial)** — limite do plano (Free 2/mês).

---

## Skills Consultadas

Cada skill teve regras aplicadas a uma ou mais tasks. Citação sem aplicação concreta é inválida.

### Backend / segurança / dados

- `domain/mysql-schema-design` — T-01: `deliveries`/`recipients` com `AreaScopedMixin`, FK RESTRICT, índices explícitos `(area_id, merchant_id, created_at)` (COUNT do limite + lista tela 14) e `(area_id, state)` (despacho Phase 8); dinheiro em `Integer` centavos (nunca Float); `DATETIME(6)` via `UTC_DATETIME`. Separação estrutural endereço-completo × campos-revelados-antes-da-coleta (RN-013).
- `domain/fastapi-production-patterns` — T-04/T-05: router `/v1/deliveries` async, dependência `area_scope` + ownership da loja, `AsyncSession` com `select(...).with_for_update()` na transição; RFC-7807 nos erros; idempotência via `Idempotency-Key` na criação.
- `product/api-design-contracts` — T-03/T-04: `CreateDeliveryBody` (Pydantic v2, `extra="forbid"`, enum estreito `payment_method`); `DeliveryOut` com PII mascarada; contratos versionados `/v1`; estados retornados como código canônico (consumidos pelo `jx-state-badge`).
- `owasp-security` — T-02/T-03/T-04: A04 invariante server-side (transição validada no backend, `FOR UPDATE`; estado-alvo nunca vem do cliente); A03 `extra="forbid"` + enum (anti mass-assignment) + ORM parametrizado (anti SQLi); A01 `AreaScoped` + 404 cross-tenant; A02 só `cpf_hash`. Herdado do `## Security Baseline` (8 ameaças).
- `br/lgpd-compliance` — T-01/T-03/T-06: minimização (nome+telefone obrigatórios = base legal execução de contrato; email/CPF opcionais); `cpf_hash` SHA-256 nunca puro (D-08); telefone mascarado na lista/dashboard `(11) 9••••-1234`; RN-021 campos anonimizáveis (recipients separado); RN-013 nota de fronteira para Phase 8.
- `quality/observability-production` — T-04/T-05: log estruturado por endpoint (`request_id`, `merchant_id`, `endpoint`, `status_code`, `duration_ms`); eventos de transição auditados em `delivery_state_transitions` (ator/motivo/timestamp aware-UTC/IP); PII mascarada via `mask_phone`/`mask_document` (filtro central, não disciplina por chamada); query de mediana/COUNT logada se > threshold.
- `quality/senior-quality-bar` (Gate 8) — T-02/T-04/T-08: máquina de estados server-side (sem confiar no cliente); zero N+1 na lista (tela 14) e no COUNT do limite; IDOR fechado por `AreaScoped`+ownership→404; PII fora de log; sem segredo no repo; dinheiro em centavos inteiros.
- `meta/orchestration-decision-tree` — planejamento: decisão de paralelizar wave backend (T-01..T-05, agente `backend-architect`) e wave frontend (T-06..T-10, agente `frontend-developer`) por não compartilharem arquivos; squad-review pós-execute (ROADMAP).

### UI (matriz obrigatória + flags Phase 7)

- `ui-ux-pro-max` — T-06/T-09/T-10: editorial-técnica (nº entrega, telefone, R$, frete, data em mono; Fraunces italic em 1 palavra do H1 do dashboard; persimmon = única cor de ação); anti-AI-slop (sem gradiente/glow/neon/confete ao criar).
- `quality/accessibility-pro` — T-07/T-06/T-09/T-10: AA nos dois temas; `jx-state-badge` nunca só por cor (texto+ícone); foco visível `--focus-ring`; erros via `aria-describedby`+`aria-invalid`; modal com foco preso e `Esc`; touch ≥44px; `prefers-reduced-motion`.
- `product/component-library-governance` — T-07/T-08: 4 componentes novos governados com story+baseline (`jx-state-badge`, `jx-estimate-box`, `jx-delivery-row`, `jx-upgrade-modal`); reuso de `jx-field`/`jx-data-table`/`jx-plan-card`/4-estados sem reinventar.
- `ux-advanced/design-tokens-system` — T-07: consumir só camada semântica (`var(--surface)`, `var(--brand)`) + 7 vars `--state-*` derivadas mecanicamente de `color.delivery_state`; nenhuma var de superfície/texto nova; zero `#hex`.
- `ux-advanced/dark-mode-theming` (DEC-001) — T-07: `jx-state-badge` padrão "superfície neutra + cor viva" que funciona claro+dark sem criar 7 tokens `_bg`; AA validado nos dois temas.
- `ux-advanced/empty-states-polish` — T-09/T-10: "nenhuma entrega ainda" (CTA Nova entrega), "nenhuma em curso", "nenhuma com esses filtros".
- `br/ux-copywriting-ptbr` — T-06/T-09/T-10: sentence case; CTA verbo+objeto sem ponto ("Chamar entregador"); rótulos de estado claros pt-BR; copy do modal honesta (sem dark pattern).
- `br/brazilian-forms` — T-06: `maskPhone`→`phoneToE164` (telefone E.164), `maskCep`/`isCepComplete` (CEP), `maskBrl` (valor declarado); `inputmode` correto; NUNCA `type="number"` para dinheiro/telefone.
- `ux-advanced/form-ux-mastery` — T-06: seções por `fieldset`; validação inline no blur; um erro por campo; CTA habilita só com form válido + destino dentro de área; estimativa visível antes de confirmar.
- `quality/error-ux-patterns` — T-06: E1 `jx-error-state` `role="alert"` (bloqueia); E2 `jx-warn-banner` `role="status"` (não bloqueia); E4 modal; transição inválida e falha-ao-criar acionáveis ("Tentar de novo").
- `ux-advanced/data-tables-ux` — T-09: lista tela 14 e "em curso" tela 11 sobre `jx-data-table` (filtro por estado/pagamento/período/busca, badge, ação por linha, loading/empty/error, paginação acessível); sem N+1 no consumo.
- `ux-advanced/saas-dashboard-patterns` — T-10: dashboard da Loja (tela 11) — KPIs em mono + tabela "em curso agora" + CTA primário; gancho de fatura `hidden` (Phase 11).

## Skills Dispensadas (com justificativa)

- `domain/saas-billing-canonical` / `domain/safe2pay-escrow-br` — modalidade **direta**: a entrega nasce sem cobrança online; cartão/PIX/Safe2Pay são Phase 10. Nenhuma superfície de billing/checkout nesta phase.
- `ux-advanced/payment-checkout-ux` — sem checkout pago (Phase 10); pagamento direto é só uma escolha de radio, sem fluxo de cobrança.
- `ux-advanced/file-upload-ux` — não há upload nesta phase; comprovação por foto é **escolhida** (radiogroup) mas executada na Phase 9.
- `ux-advanced/gesture-touch-patterns` — superfície é a **Loja web** (desktop-first, responsivo); gestos do app são do entregador (Phase 8 mobile).
- `mobile/push-notifications-architecture` / `mobile/offline-first` — sem app/mobile/notificações nesta phase (Phase 8/9).
- `ux-advanced/chat-ux-patterns` — sem chat.
- `ux-advanced/onboarding-patterns` / `ux-advanced/trust-safety-ux` — sem signup novo (loja já cadastrada na Phase 4). **Nota:** o empty-state da "primeira entrega" usa o padrão de convite à ação (coberto por `empty-states-polish`/`saas-dashboard-patterns`), não onboarding de cadastro; trust-safety aplica-se ao tracking público (Phase 9), não aqui — o único PII do destinatário já é tratado por `lgpd-compliance` (máscara + minimização).
- `product/visual-regression-testing` — baseline de story é declarada (UI-SPEC §8) mas a suíte de regression visual completa (`touches_shared_components`) consolida na Phase 9; aqui registramos stories dos 4 componentes novos como gancho.
- `product/micro-animations-delight` / `ux-advanced/motion-design-patterns` — `has_non_trivial_motion: false` nesta phase (sem cronômetro/sheet de oferta — isso é Phase 8); motion limita-se a recálculo de estimativa e abertura de modal em `motion.normal` (coberto por `accessibility-pro` + `prefers-reduced-motion`).

---

## Tech debt deste plano (verificação obrigatória v0.8+)

Consultado `.planning/TECH-DEBT.md` filtrando itens com prazo nesta phase ou `urgency_class` no caminho.

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime (risco recorrente) — `urgency_class: pre_launch_high`, prazo "toda phase com timestamps (2,7,9,10,11)" | **Entra**: timestamps de transição precisam ser aware UTC | T-01, T-02 (todo `created_at` via `datetime.now(UTC)` + `UTC_DATETIME`; teste anti-naive) |
| TD-009 | Estimativa mediana simples (RN-030) — `post_launch_quarter` | Vínculo direto com REQ-023; mediana simples é o escopo aceito (não over-engineerar). Mantida como TD; aqui só implementamos a versão simples | T-03 (implementa mediana simples; TD permanece para reavaliar pós-90d) |
| TD-018 | Aumento de piso não revalida tabelas já salvas — `post_launch_quarter` (produto) | **Não entra**: é regra de pricing da Phase 6; estimativa só lê tabelas existentes, não revalida piso | — |

---

## Open questions / LOW confidence do RESEARCH (Regra 12 — obrigatório)

Cada item LOW do RESEARCH vira **task explícita** ou **decisão consciente de adiar (TD)**.

| Item RESEARCH | Confidence | Resolução neste plano |
|---------------|------------|------------------------|
| **LOW-1** — Concorrência da transição: lock pessimista `FOR UPDATE` vs otimista por `version` | LOW | **Decisão: lock pessimista** (mais simples e correto para o volume do piloto; Redis lock fica para o aceite da Phase 8 — ADR-104). → **Task T-02** implementa `transition()` com `select(...).with_for_update()`; **Task T-08** prova com teste de corrida `@pytest.mark.mysql` (TH-01). Critério: 2 transições simultâneas serializam, segunda revalida e falha 422 se inválida. |
| **LOW-2** — Formato do "preço para o trecho" na mediana quando entregadores misturam modo bairro/km | LOW | → **Task T-03**: `estimate.py` computa o **preço efetivo de cada entregador para o trecho específico** (bairro de destino conhecido → preço da linha do bairro; modo km → preço pela faixa da distância estimada) e tira a mediana dos efetivos. Critério verificável: teste com 1 entregador modo-bairro + 1 modo-km → mediana dos dois preços efetivos. |
| **LOW-3** — COUNT por query vs contador denormalizado; e se CANCELADA conta | LOW | **Decisão: COUNT por query** (sempre correto, sem drift) e **CANCELADA NÃO conta** (RN-004 custo zero pré-aceite; evita burlar contagem por create+cancel). → **Task T-04** implementa `deliveries_this_month()` com `WHERE ... AND state != 'CANCELADA'`; **Task T-08** testa o limite Free + que cancelar libera vaga. |
| **LOW-4** — Índices de `deliveries` + tipo de ID exposto (`public_token` ULID p/ tracking) | LOW | → **Task T-01**: criar índices `(area_id, merchant_id, created_at)` e `(area_id, state)`; **reservar coluna `public_token` (ULID, opaca, `unique`, gerada na criação)** para o tracking público da Phase 9 — barato reservar agora (A01 IDs não-sequenciais). PK interna permanece BIGINT autoincrement. Critério: migration cria os 2 índices + `public_token unique`; criação preenche um ULID. |

---

## Threat model

Herdado do `## Security Baseline` do RESEARCH.md (8 ameaças). Phase coleta PII do destinatário e a máquina de estados é crítica para integridade financeira/antifraude.

| ID | Ameaça | Vetor | Impacto | Likelihood | Mitigação | Task |
|----|--------|-------|---------|------------|-----------|------|
| TH-01 | Tampering de transição + concorrência | Forçar transição inválida (CRIADA→ENTREGUE) ou 2 requisições simultâneas | Alto | Médio | Validação server-side contra `DELIVERY_TRANSITIONS` → 422; `SELECT ... FOR UPDATE` na linha (lock pessimista, LOW-1) | T-02, T-08 |
| TH-02 | Tampering do histórico de transições | `UPDATE`/`DELETE` em `delivery_state_transitions` (apagar prova) | Alto | Baixo | Trigger MySQL `BEFORE UPDATE/DELETE` → `SIGNAL 45000` (RN-012, idêntico migration 0002); tabela append-only | T-01, T-08 |
| TH-03 | IDOR / Broken Access Control | Loja A enumera/cancela entrega da loja B ou de outra área | Alto | Médio | `AreaScopedMixin` + `AreaScopedRepository` (`WHERE area_id`) + ownership por `merchant_id` → **404** (não 403, não vaza existência) | T-04, T-05, T-08 |
| TH-04 | Vazamento de PII do destinatário | Telefone/endereço em log ou output indevido | Alto | Médio | `mask_phone`/`mask_document` (filtro central A09); telefone só na janela ACEITA→FINALIZADA (RN-022) — em CRIADA não exposto a ninguém; RN-013 separa endereço-completo dos campos revelados antes da coleta | T-01, T-03, T-08 |
| TH-05 | CPF do destinatário em claro | CPF persistido/exposto puro | Médio | Baixo | `recipients` guarda só `cpf_hash` SHA-256 (D-08); CPF opcional (minimização); nunca em URL/log | T-01, T-03 |
| TH-06 | Injection (SQL / mass assignment) | Payload força `state`/`courier_id`/`fee_cents` ou SQLi | Alto | Médio | ORM/parametrizado (zero f-string); Pydantic `extra="forbid"`; `payment_method` enum estreito; campos derivados pelo servidor não vêm do body | T-03, T-04, T-08 |
| TH-07 | Abuso de criação / contorno de limite | Criação em massa; 3ª Free sem pagar | Médio | Médio | Rate limit por loja reusando `SlidingWindowLimiter` (`delivery_create_limiter`, **30/min por loja** — pico legítimo de loja movimentada ~1 entrega/2min com folga); limite de plano COUNT server-side → 402/409 upgrade | T-04, T-08 |
| TH-08 | LGPD (minimização/base legal/retenção) | Coleta excessiva de PII; retenção indevida | Médio | Médio | Coletar mínimo (nome+telefone obrigatórios = base legal execução de contrato; email/CPF opcionais); RN-021 `deliveries` anonimizável (recipients separado), nunca deletada; política declarada | T-01, T-03 |

**Checklist LGPD (base legal por campo):**
- `recipient.name` — obrigatório — execução de contrato (necessário para a entrega).
- `recipient.phone_e164` — obrigatório — execução de contrato (contato na entrega; janela RN-022).
- `recipient.email` — opcional — consentimento/legítimo interesse (notificação opcional).
- `recipient.cpf_hash` — opcional — legítimo interesse (antifraude); só hash, nunca puro.
- `delivery.dropoff_address_full` — obrigatório — execução de contrato; revelado ao entregador só pós-coleta (RN-013).

---

## Performance budget

Herdado de `.planning/config.json > performance_budget`.

**Frontend (telas 12/14/11):**
- LCP ≤ 2500ms · INP ≤ 200ms · CLS ≤ 0.1 · bundle main ≤ 400kb gzip.
- Rotas `/loja/entregas/nova`, `/loja/entregas`, `/loja` lazy-loaded sob o shell da Loja.
- Estimativa recalcula com debounce (`motion.normal`); skeleton durante recálculo (sem layout shift).

**Backend:**
- `POST /v1/deliveries` (criação, inclui estimativa mediana): **p95 < 200ms**. A query espacial de elegíveis usa índices da Phase 6 (`ST_Contains` indexado) + índice `(area_id, state/online)`; mediana é agregação Python sobre as linhas elegíveis (set pequeno). Estimativa NÃO pode estourar o budget — query espacial indexada obrigatória.
- `GET /v1/deliveries` (lista tela 14): paginada, **zero N+1** (join/loader único para recipient/courier; uma query + COUNT). p95 < 150ms.
- COUNT do limite de plano: índice `(area_id, merchant_id, created_at)` — não varre tabela.

Medição: Lighthouse CI (frontend) + pytest-benchmark nos endpoints críticos (criação/lista) e log de query lenta (observability).

---

## Observability checklist

Aplicando `quality/observability-production`:

- [ ] `POST /v1/deliveries`, `POST /v1/deliveries/{id}/cancel`, `GET /v1/deliveries` logam `request_id`, `merchant_id`, `endpoint`, `method`, `status_code`, `duration_ms`.
- [ ] 4xx (422 transição inválida, 402/409 limite, 404 IDOR) como WARNING; 5xx como ERROR.
- [ ] **Zero PII em logs**: telefone/endereço/CPF do destinatário mascarados via `mask_phone`/`mask_document` (filtro central A09). Teste `test_pii_masking.py` faz grep em logs = 0 ocorrências de PII.
- [ ] **Eventos de transição auditados** em `delivery_state_transitions`: cada transição grava `from_state`, `to_state`, `actor_user_id`, `reason`, `ip`, `gps` quando houver, `created_at` aware-UTC (D-04). Métrica de negócio: contagem de entregas criadas por área (KPI ROADMAP "métrica criação").
- [ ] Query de mediana/COUNT logada com WARNING se ultrapassar threshold de latência.
- [ ] `/healthz` inalterado (sem serviço novo).

---

## Error UX checklist

Aplicando `quality/error-ux-patterns` (UI):

- [ ] **E1 fora de área** — `jx-error-state` `role="alert"` sob o campo Bairro: "Endereço fora da nossa área de cobertura. Confira o bairro."; campo `aria-invalid`; CTA desabilitado enquanto destino fora; ação secundária "Avisar quando atendermos esse bairro" (gancho leve, sem promessa de data).
- [ ] **E2 0 entregadores** — `jx-warn-banner` `role="status"` (não bloqueia): "0 entregadores online agora para esse trecho — sua entrega pode demorar."; estimativa mostra "Sem estimativa agora"; CTA segue habilitado (D-06).
- [ ] **E4 limite de plano** — submit abre `jx-upgrade-modal` em vez de criar; copy honesta, "Agora não" de igual peso, sem dark pattern.
- [ ] **Transição inválida / falha ao criar** — `jx-error-state` `role="alert"` acionável "Não foi possível criar a entrega. Tente de novo." + "Tentar de novo"; `request_id` logado, não exibido.
- [ ] Validação inline no blur (não modal ao submit); um erro por campo via `aria-describedby`.
- [ ] Decisão consistente: inline para validação de campo, banner/alert para E1/E2, modal só para E4 (limite).

---

## Integration contracts

**N/A — `integration_check: false` no ROADMAP Phase 7.** Não há contrato cross-layer validado em runtime nesta phase (sem WebSocket, sem integração externa — `has_external_integration: false`). O consumo do `GET /v1/deliveries` pela tela 14 e do `POST /v1/deliveries` pela tela 12 é validado pelos testes de cada lado e pela reconciliação, não pelo integration-checker.

---

## Tasks

### Wave 1 (backend, paralelo entre si quando indicado) — `parallel-hint: backend-architect`

### T-00 — Wave 0: scaffold de testes (RED) + fixtures

- **Type:** test
- **Files:** `apps/api/tests/deliveries/__init__.py`, `conftest.py`, `test_state_machine.py`, `test_append_only.py`, `test_create.py`, `test_estimate.py`, `test_plan_limit.py`, `test_concurrency.py`, `test_isolation.py`, `test_pii_masking.py`
- **Skills aplicadas:**
  - `domain/fastapi-production-patterns` — fixtures de entrega/destinatário/entregador online elegível reusando padrões dos testes das Phases 4/6.
- **Descrição:** Criar os arquivos de teste (falhando — RED) e o `conftest.py` com fixtures (loja ativa, plano Free/pago, entregador online com cobertura+tabela elegível para um trecho). Marca `@pytest.mark.mysql` nos testes de trigger/concorrência.
- **Success:** `pytest apps/api/tests/deliveries` coleta os testes; todos falham por ausência de implementação (não por erro de import).
- **Depends on:** none

### T-01 — Migration 0006: `deliveries`, `delivery_state_transitions` (trigger), `recipients`

- **Type:** migration
- **Files:** `apps/api/alembic/versions/0006_deliveries.py`, `apps/api/app/deliveries/__init__.py`, `apps/api/app/deliveries/models.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — `AreaScopedMixin`+`TimestampMixin`; FK RESTRICT; dinheiro `Integer` centavos; índices `(area_id, merchant_id, created_at)` e `(area_id, state)` (LOW-4); separação endereço-completo (`dropoff_address_full`, `dropoff_number`, `dropoff_complement`) × revelados-antes-coleta (`dropoff_neighborhood_id`, `distance_m`) por RN-013.
  - `owasp-security` / `br/lgpd-compliance` — `recipients` com `cpf_hash` (CHAR 64), sem CPF puro; PII anonimizável (RN-021); `public_token` ULID `unique` opaco (LOW-4, A01).
  - `quality/senior-quality-bar` — trigger append-only inviolável; dinheiro nunca Float.
- **Descrição:** Migration 0006 cria as 3 tabelas espelhando convenções 0002-0005. `deliveries`: `state` (default `CRIADA`), `merchant_id`, `courier_id` (NULL até aceite), `recipient_id`, `payment_method` ('direct'), `proof_method` ('photo'), `pickup_*`/`dropoff_*`, `estimate_min_cents`/`estimate_max_cents`/`fee_cents`, `public_token`, índices. `delivery_state_transitions` (`AreaScoped`): `delivery_id`, `from_state` (nullable), `to_state`, `actor_user_id`, `reason`, `gps_lat`/`gps_lng`, `ip`, `created_at`. `recipients` (`AreaScoped`): `name`, `phone_e164`, `email` (nullable), `cpf_hash` (nullable), contadores `deliveries_count`/`refusals_count`. Trigger `trg_dst_no_update`/`trg_dst_no_delete` (`SIGNAL 45000`) só em `dialect.name == "mysql"`; `downgrade` dropa triggers antes da tabela.
- **Success:** `alembic upgrade head` cria as 3 tabelas + 2 triggers (MySQL); `downgrade -1` reverte; models importam sem erro.
- **Depends on:** T-00

### T-02 — Máquina de estados (7 estados) + `transition()` com lock

- **Type:** new_endpoint (módulo de serviço)
- **Files:** `apps/api/app/deliveries/state_machine.py`, `apps/api/app/deliveries/service.py` (parte `transition`)
- **Skills aplicadas:**
  - `owasp-security` (A04) — transição validada server-side; estado-alvo nunca do cliente; `select(...).with_for_update()` (lock pessimista, LOW-1, TH-01).
  - `quality/senior-quality-bar` — `transition()` é o **único** ponto de escrita de estado; timestamp aware-UTC (TD-010).
  - `domain/fastapi-production-patterns` — espelha `couriers/state_machine.py` (dict-de-sets + `assert_*_transition` → 422); compõe gravação em `delivery_state_transitions`.
- **Descrição:** `DELIVERY_TRANSITIONS` com as 7 chaves completas (CRIADA→{ACEITA,CANCELADA}; ACEITA→{COLETADA,CANCELADA}; COLETADA→{ENTREGUE,RECUSADA_NO_DESTINO,CANCELADA}; ENTREGUE→{FINALIZADA}; RECUSADA_NO_DESTINO→{FINALIZADA}; CANCELADA/FINALIZADA terminais). `InvalidTransitionError(422)`. `assert_delivery_transition(current,target)`. `transition(session,*,delivery,to_state,actor_id,reason,gps,ip)`: carrega `FOR UPDATE`, valida, atualiza `state`, INSERT em transitions com `datetime.now(UTC)`. Criação chama `transition(None→"CRIADA")`.
- **Success:** `test_state_machine.py` verde — **todas** as transições inválidas (produto cartesiano dos 7 estados menos as válidas) → 422; válidas passam.
- **Depends on:** T-01

### T-03 — Estimativa mediana (RN-030) + schemas + recipient (hash CPF)

- **Type:** new_endpoint (serviço)
- **Files:** `apps/api/app/deliveries/estimate.py`, `apps/api/app/deliveries/schemas.py`, `apps/api/app/deliveries/service.py` (parte recipient + estimativa)
- **Skills aplicadas:**
  - `product/api-design-contracts` — `CreateDeliveryBody` (`extra="forbid"`, enum `PaymentMethod` `direct`/`card`/`pix`); `DeliveryOut` com telefone mascarado; `EstimateOut` (faixa min/max + fee).
  - `br/lgpd-compliance` — `hash_cpf` SHA-256 (D-08); minimização (nome+telefone obrigatórios, email/CPF opcionais); telefone mascarado no output.
  - `quality/senior-quality-bar` — mediana em centavos inteiros (sem Float); preço efetivo por trecho (LOW-2).
- **Descrição:** `median_cents(prices)` retorna `None` se vazio (E2). `effective_price_for_trip(courier, dropoff_nbhd_id, distance_m)` compõe `couriers/pricing.py` (modo bairro → linha do bairro; modo km → faixa da distância) — resolve LOW-2. `eligible_online_couriers(...)` compõe `is_eligible` (Phase 6) sobre entregadores `is_online=True`+`status=active`. `upsert_recipient(...)` com `hash_cpf` se vier CPF. Schemas Pydantic v2 com `extra="forbid"`; `payment_method != direct` → 422 "em breve" (D-02).
- **Success:** `test_estimate.py` verde — mediana de mix bairro/km; 0 elegíveis → `None` (E2); `test_create.py::test_card_em_breve` → 422.
- **Depends on:** T-01

### T-04 — Serviço `create_delivery` + limite de plano + router

- **Type:** new_endpoint
- **Files:** `apps/api/app/deliveries/service.py` (parte `create_delivery`/`cancel_delivery`/`deliveries_this_month`), `apps/api/app/deliveries/router.py`, `apps/api/app/api/v1/router.py` (registro)
- **Skills aplicadas:**
  - `owasp-security` (A01/A03/A04) — `area_scope` dep + ownership → 404 cross-tenant (TH-03); `extra="forbid"`; limite COUNT server-side; rate limit `delivery_create_limiter` 30/min/loja (TH-07).
  - `domain/fastapi-production-patterns` — `POST /v1/deliveries` (Idempotency-Key), `POST /v1/deliveries/{id}/cancel`, `GET /v1/deliveries` (paginado, sem N+1); RFC-7807.
  - `quality/observability-production` — log estruturado por endpoint, PII mascarada.
  - `quality/senior-quality-bar` — N+1 zero na lista; IDOR fechado; limite recalculado server-side.
- **Descrição:** `deliveries_this_month()` COUNT `WHERE area_id AND merchant_id AND created_at >= month_start AND state != 'CANCELADA'` (LOW-3); `>= plan.deliveries_per_month and not is_unlimited` → erro 402/409 com payload de upgrade (D-07). `create_delivery()`: resolve bairros, valida destino no catálogo (E1→422), checa limite, calcula estimativa (E2→aviso no payload), upsert recipient, INSERT delivery CRIADA, `transition(None→CRIADA)`. `cancel_delivery()`: ownership → `transition(CRIADA→CANCELADA)`. `GET` lista paginada da loja (loader único, mascara telefone).
- **Success:** `test_create.py`/`test_plan_limit.py`/`test_isolation.py` verdes — cria CRIADA; 3ª Free → upgrade; cross-loja → 404.
- **Depends on:** T-02, T-03

### T-05 — RN-013 nota de fronteira + serializer de loja (sem oferta)

- **Type:** refactor (documentação estrutural + serializer)
- **Files:** `apps/api/app/deliveries/schemas.py` (`DeliveryOut` loja), `apps/api/app/deliveries/README.md` (nota RN-013 para Phase 8)
- **Skills aplicadas:**
  - `br/lgpd-compliance` (RN-013) — `DeliveryOut` da loja contém endereço completo (loja é dona do dado); documentar que o futuro `OfferOut` do entregador (Phase 8) NÃO pode conter endereço completo — só `dropoff_neighborhood_id`+`distance_m` (separação já modelada em T-01).
  - `quality/senior-quality-bar` — fronteira de exposição por construção, não por filtro esquecível.
- **Descrição:** Garantir que `DeliveryOut` (superfície loja) expõe o que a loja digitou, e registrar em `README.md` do módulo a nota de design para a Phase 8 (payload de oferta sem endereço completo do destino — RN-013). NÃO implementar serializer de oferta (Phase 8).
- **Success:** `DeliveryOut` testado; nota RN-013 presente no README do módulo referenciando os campos separados de T-01.
- **Depends on:** T-04

### Wave 2 (frontend, paralelo à Wave 1 backend) — `parallel-hint: frontend-developer`

### T-06 — Form de nova entrega (tela 12) — F-03, E1/E2

- **Type:** ui_component
- **Files:** `apps/web/src/features/loja/entregas/nova-entrega.component.ts` (+ `.scss`/`.html`), rota em `app` routing
- **Skills aplicadas:**
  - `br/brazilian-forms` — `maskPhone`/`phoneToE164`, `maskCep`/`isCepComplete`, `maskBrl`; `inputmode` correto; nunca `type="number"`.
  - `ux-advanced/form-ux-mastery` — `fieldset` por seção; validação inline no blur; estimativa antes de confirmar; CTA habilita só com form válido + destino em área.
  - `quality/error-ux-patterns` — E1 `jx-error-state` alert; E2 `jx-warn-banner` status; falha-ao-criar acionável.
  - `br/ux-copywriting-ptbr` / `ui-ux-pro-max` — CTA "Chamar entregador"; mono em CEP/telefone/valor; sem confete.
  - `ux-advanced/design-tokens-system` — só vars semânticas; zero `#hex`.
- **Descrição:** Reactive form com seções Coleta (pré-preenchida loja, editável), Entrega (CEP→bairro do catálogo Phase 6, select de bairro), Destinatário (nome, telefone E.164), Itens (descrição, qtd, valor declarado opcional, nº pedido, obs), Comprovação (foto default; OTP desabilitado "em breve"), Pagamento (direto default; PIX/cartão "em breve"). E1 bloqueia CTA + captura de interesse; E2 banner não bloqueante. Submit no limite abre `jx-upgrade-modal` (T-08).
- **Success:** Wireframe-contract `12-loja-nova-entrega.html` coberto; `axe-core` zero violações críticas (claro+dark); zero `#hex`.
- **Depends on:** none (mock de API; integra com T-04 na reconciliação)

### T-07 — `jx-state-badge` + vars `--state-*` (7 estados) + `jx-estimate-box`

- **Type:** ui_component
- **Files:** `apps/web/src/shared/components/state-badge/*`, `apps/web/src/shared/components/estimate-box/*`, `apps/web/src/styles/_semantic.scss` (+ `_tokens.scss` 7 vars derivadas), stories
- **Skills aplicadas:**
  - `product/component-library-governance` — componentes governados com story+baseline.
  - `ux-advanced/design-tokens-system` / `ux-advanced/dark-mode-theming` — 7 `--state-*` derivadas de `color.delivery_state`; padrão "superfície neutra + cor viva" claro+dark.
  - `quality/accessibility-pro` — badge nunca só por cor (texto+ícone `aria-hidden`); AA dois temas.
- **Descrição:** `jx-state-badge` com `[state]` (código canônico) + `[variant]` (list|dashboard, troca só rótulo) — 7 estados RN-019 com cor+ícone+texto pt-BR. Gera as 7 vars `--state-*` de `color.delivery_state` em `_tokens.scss`/`_semantic.scss`. `jx-estimate-box` `role="status"` com variantes faixa (N entregadores), 0 entregadores (E2), carregando.
- **Success:** Stories dos 7 estados (list+dashboard, claro+dark) renderizam; checker de contraste AA passa; zero `#hex`.
- **Depends on:** none

### T-08 — `jx-upgrade-modal` (E4) — anti-dark-pattern

- **Type:** ui_component
- **Files:** `apps/web/src/shared/components/upgrade-modal/*`, stories
- **Skills aplicadas:**
  - `product/component-library-governance` — reusa `jx-plan-card` no comparativo.
  - `quality/accessibility-pro` — `role="dialog"` `aria-modal`, foco preso, foco inicial no título, `Esc` fecha, foco volta ao gatilho.
  - `br/ux-copywriting-ptbr` — copy honesta; "Agora não" de igual peso; sem urgência falsa.
- **Descrição:** Modal de limite (Free 2/mês): título factual, subtexto "contador zera dia 1º", comparativo via `jx-plan-card` data-driven de `GET /v1/plans`. "Agora não"/Esc/X equivalentes; nada pré-selecionado; form preserva o preenchido ao fechar.
- **Success:** Story "aberto" + "foco no agora-não" + mobile (claro+dark); `axe-core` zero violações; "Agora não" alcançável por teclado e de igual peso.
- **Depends on:** none

### T-09 — Lista de entregas (tela 14) — `jx-data-table` + `jx-delivery-row`

- **Type:** ui_component
- **Files:** `apps/web/src/features/loja/entregas/entregas-list.component.ts` (+ scss/html), `apps/web/src/shared/components/delivery-row/*`, stories
- **Skills aplicadas:**
  - `ux-advanced/data-tables-ux` — filtro estado/pagamento/período/busca; badge; ação por linha; loading/empty/error; paginação acessível.
  - `ux-advanced/search-filter-ux` — filtros preservam contexto (query params); "limpar filtros" no empty.
  - `ux-advanced/empty-states-polish` — empty com/sem filtro distintos.
  - `br/lgpd-compliance` — telefone fora da lista por padrão; se exibido, mascarado.
- **Descrição:** Lista sobre `jx-data-table`: colunas Nº(mono)/Data(mono)/Destino/Entregador("—" se CRIADA)/Frete(mono)/Pagamento/Status(`jx-state-badge` list)/Ação. Ação "Cancelar" só em CRIADA (sem custo, confirmação leve); "ver" sempre. Estados loading/empty/error embutidos.
- **Success:** Wireframe-contract `14-loja-entregas.html` coberto; `axe-core` zero violações; sem `#hex`; ação cancelar só em CRIADA.
- **Depends on:** T-07

### T-10 — Dashboard da Loja (tela 11) — KPIs + em curso

- **Type:** ui_component
- **Files:** `apps/web/src/features/loja/dashboard/*` (estender), stories
- **Skills aplicadas:**
  - `ux-advanced/saas-dashboard-patterns` — KPIs mono + tabela "em curso" + CTA primário; gancho de fatura `hidden`.
  - `ui-ux-pro-max` — H1 com Fraunces italic em "certinho"; persimmon única cor de ação.
  - `ux-advanced/empty-states-polish` — primeira-entrega convida à ação.
- **Descrição:** Dashboard `/loja`: gancho fatura `hidden` (Phase 11), H1 italic, CTA "+ Nova entrega", 4 KPIs (entregas hoje, tempo médio, fretes hoje, entregas do plano "12/40" RN-028 — todos mono, da API), tabela "em curso agora" (`jx-state-badge` dashboard; só CRIADA nesta phase), empty/onboarding da primeira entrega.
- **Success:** Wireframe-contract `11-loja-dashboard.html` coberto; `axe-core` zero violações; KPIs da API (nada hardcoded); zero `#hex`.
- **Depends on:** T-07

### Wave 3 (integração de testes backend)

### T-11 — Testes de integridade, concorrência e PII (GREEN final)

- **Type:** test
- **Files:** `apps/api/tests/deliveries/test_append_only.py`, `test_concurrency.py`, `test_pii_masking.py`, `test_isolation.py`
- **Skills aplicadas:**
  - `quality/senior-quality-bar` — máquina/IDOR/PII/N+1 cobertos por teste.
  - `owasp-security` — TH-01/TH-02/TH-03/TH-04 com critérios verificáveis.
- **Descrição:** `test_append_only.py` (`@pytest.mark.mysql`): `UPDATE`/`DELETE` em `delivery_state_transitions` → erro MySQL 1644. `test_concurrency.py` (`@pytest.mark.mysql`): 2 transições simultâneas → 1 vence (FOR UPDATE). `test_pii_masking.py`: grep PII em logs = 0; telefone não exposto em CRIADA. `test_isolation.py`: cross-loja/área → 404.
- **Success:** Todos verdes; suíte completa `uv run pytest && uv run ruff check .` limpa.
- **Depends on:** T-04, T-05

---

## Execution order

Waves (grupos paralelizáveis) — **`parallel-hint`: backend e frontend rodam em paralelo (sem arquivos compartilhados).**

- **Wave 0:** T-00 (scaffold de testes RED).
- **Wave 1 — backend (`backend-architect`):** T-01 → T-02, T-03 (paralelos após T-01) → T-04 → T-05.
- **Wave 2 — frontend (`frontend-developer`), em paralelo à Wave 1:** T-07 → (T-09, T-10); T-06; T-08 (todos após T-07 onde dependem).
- **Wave 3:** T-11 (depende de T-04, T-05).

> `files_modified` de backend (`apps/api/...`) e frontend (`apps/web/...`) não se sobrepõem → paralelização segura. Integração real (form→`POST /v1/deliveries`, lista→`GET /v1/deliveries`) é validada na reconciliação, não pelo integration-checker (`integration_check: false`).

---

## Reconciliation expectations

Ao fim, `/gsd:reconcile-state 7` verifica:

- As 3 tabelas e os 2 triggers existem (migration aplicada); models batem.
- Endpoints `POST /v1/deliveries`, `POST /v1/deliveries/{id}/cancel`, `GET /v1/deliveries` têm handler.
- Máquina com 7 chaves; `transition()` é o único ponto de escrita de `state`.
- `recipients` sem CPF puro; logs sem PII; telefone mascarado na lista.
- Telas 12/14/11 + 4 componentes novos existem; zero `#hex`; stories presentes.
- Nenhum arquivo-fantasma; nenhuma feature fantasma (despacho/comprovação/checkout NÃO aparecem).

---

## Rollback plan

- Revert do(s) commit(s) `feat(phase-7/...)`.
- `alembic downgrade -1` (dropa triggers antes das tabelas; remove `deliveries`/`transitions`/`recipients`).
- Sem ações de ops externas (sem integração externa nesta phase).

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: {presente | ausente | incompleto}
- Performance budget: {presente | N/A | incompleto}
- Observability checklist: {presente | N/A | incompleto}
