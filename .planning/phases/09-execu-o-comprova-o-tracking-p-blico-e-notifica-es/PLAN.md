# PLAN — Phase 9: Execução, comprovação, tracking público e notificações

> Gerado por `gsd-planner` em 2026-06-10.
> Validado por `gsd-plan-checker` em {date} — status: {PASS|BLOCK|FLAG}.

## Goal

Fechar o ciclo operacional da entrega (F-06): da `ACEITA` à `FINALIZADA`, com comprovação foto+EXIF/GPS antifraude (server-side, geofence), tracking público sem login com mapa ao vivo (DEC-002), notificações multicanal com fallback, confirmação de pagamento direto, cancelamentos RN-004 e os jobs de ciclo. Migration **0008** reversível. Backend + 3 superfícies de UI (Entregador Ionic, Loja web, Tracking público).

## Success criteria

Para fechar este plano, TODOS os critérios abaixo devem ser verdes:

- [ ] Foto sem GPS **ou** fora do raio → rejeição **server-side** com motivo legível (RFC-7807); 3 falhas → flag `low_confidence` + entrega segue para revisão do admin de área (não trava para sempre). `@pytest.mark.mysql` cobre `ST_Distance_Sphere` com par conhecido (SRID/ordem `POINT(lng,lat)`).
- [ ] **Ordem do pipeline garantida por teste:** `extract_gps_from_raw(raw)` roda ANTES de qualquer reprocess/strip; o derivativo armazenado é limpo, mas o GPS já foi lido e validado (oposto do KYC).
- [ ] Número de referência: 3 tentativas erradas → orienta ligar à loja; loja libera manualmente (auditável).
- [ ] Transição COLETADA revela o endereço completo do destino (RN-013); ENTREGUE/RECUSADA via `transition()` Phase 7 (append-only).
- [ ] Telefone inacessível fora de `ACEITA→FINALIZADA` (teste por estado — RN-022).
- [ ] Tracking público responde **SEM auth** via `public_token`; token inválido → 404 genérico (anti-enumeração) + estado de erro na UI; serializer NÃO emite PII do entregador (nome completo/telefone/CPF) nem telefone do destinatário; endereço destino só após COLETADA.
- [ ] Ingestão de localização: aceita posição só do courier dono da entrega (IDOR fechado, 404 não 403) e só na janela `ACEITA→COLETADA`; aware-UTC.
- [ ] Job `purge_locations`: `delivery_locations` de entregas terminais há >24h são hard-deleted (LGPD). Job `finalize_deliveries`: ENTREGUE há >24h sem disputa → FINALIZADA. Job `absent_timeout`: "ausente" >10min → habilita retornar.
- [ ] Notificações 3 momentos: fallback push→email; SMS **só** no "a caminho"; cada tentativa registrada em `notifications`.
- [ ] "Não recebi" pagamento direto → entrega conclui ENTREGUE + abre registro `payment_dispute`.
- [ ] Wireframe-contract de `06`, `07`, `13`, `26`; mapa **lazy** (LCP = timeline, não o mapa); estados loading/sucesso/vazio/erro/offline-mobile em cada tela.
- [ ] Migration 0008 reversível (`downgrade` testado; sem `drop_index` redundante de FK — lição da 0006).
- [ ] Todos os testes relacionados passam (`uv run pytest` incl. `-m mysql`; `npm test`).
- [ ] Lint limpo (`uv run ruff check .`).
- [ ] Commits atômicos por task com mensagem padronizada.

## REQs referenciados

- REQ-026 — F-06 com 6 exceções
- REQ-027 — foto+EXIF/GPS geofence
- REQ-028 — número de referência
- REQ-029 — cancelamentos RN-004
- REQ-030 — tracking público + mapa ao vivo (DEC-002 / ADR-101 promovida)
- REQ-031 — notificações 3 momentos
- REQ-032 — janela de telefones (RN-022)
- REQ-035 (parcial) — confirmação de pagamento direto
- REQ-049 — multicanal com fallback
- REQ-055 — estados de UI

---

## Skills Consultadas

Cada skill teve regras aplicadas a uma ou mais tasks. Citação sem aplicação concreta é inválida.

### Matriz UI (obrigatórias — has_ui:true)
- `ui-ux-pro-max` — T-12/T-15/T-16/T-17: estética editorial-técnica; mono carrega dado (ETA, `delivery_id`, valores, horários), Fraunces italic SÓ em "rapidinho." do header de tracking, persimmon como acento reservado (estado atual da timeline, marcador "agora"), CTA de operação crítica em superfície carvão `--text`. Anti-AI-slop: sem gradiente no mapa, sem glassmorphism no banner de ETA.
- `ux-advanced/design-tokens-system` — T-11..T-17: zero `#hex`; tudo via CSS vars semânticas herdadas da Phase 3/7 (`--surface*`, `--state-*`, `--brand`); mapa e timeline também (UI-SPEC §11 — 0 tokens inventados).
- `product/component-library-governance` — T-11: 8 componentes NOVOS (`jx-proof-capture`, `jx-geofence-pill`, `jx-direct-payment-confirm`, `jx-pending-upload-banner`, `jx-tracking-timeline`, `jx-tracking-banner`, `jx-live-map`, `jx-notice`) são compostos/estendidos a partir do design system; `jx-proof-capture` é **wrapper** de `jx-doc-upload` (não fork); reuso de `jx-state-badge`/`jx-accepted-courier-card`/`jx-score-chip`/estados Phase 3.
- `quality/accessibility-pro` — T-11..T-17: AA nos dois temas; touch ≥44px (CTA crítico ≥52px); `aria-live` em toda mudança de estado (endereço liberado, ENTREGUE, GPS confirmado, foto enviada); mapa com alternativa textual = timeline + banner ETA, `role="img"`/`aria-label`; foco move para alertas; `axe-core` zero violações críticas em 07 e 26.
- `ux-advanced/empty-states-polish` — T-15/T-16: tracking sem dados ("Sua entrega está sendo preparada…"), comprovações vazias, link inválido — causa + ação.

### Por flag/feature/camada
- `br/ux-copywriting-ptbr` — T-11..T-17: sentence case, CTA verbo+objeto, erro = o que houve + o que fazer (contrato de copy UI-SPEC §10).
- `ux-advanced/gesture-touch-patterns` — T-12/T-13: **sem swipe em ação crítica** (cheguei/confirmar = botão deliberado ≥52px — um gesto acidental não dispara transição server-side); pan do mapa com `touch-action` próprio não conflita com scroll; tap-to-enlarge na foto.
- `mobile/offline-first` — T-08/T-13: upload offline-tolerante (`pending_upload`, foto no device, transição só conclui com upload OK); polling resiliente (pausa offline/background, não acumula posições obsoletas); `jx-pending-upload-banner`.
- `mobile/push-notifications-architecture` — T-09/T-17: opt-in contextual (após primeira entrega, não no primeiro load); fallback silencioso; `push_subscriptions` registro do device; payload push ZERO PII (reusa `PushMessage`).
- `ux-advanced/file-upload-ux` — T-12: captura via `jx-doc-upload` (`capture="environment"`); preview, compressão, retry, progresso `role="progressbar"`.
- `quality/error-ux-patterns` — T-12/T-13/T-16: GPS fora do raio, número não confere (contador "tentativa 2 de 3"), upload offline, low_confidence — acionáveis e **não bloqueiam para sempre**; erro inline, não modal.
- `ux-advanced/trust-safety-ux` — T-10/T-16: tracking público expõe só PII permitida do entregador; footer de procedência; confirmação consciente de "não recebi" sem punir o entregador; posição aproximada (snap a via), nunca lat/long precisa em texto.
- `ux-advanced/responsive-breakpoint-strategy` — T-15/T-16: tela 13 (loja) 2 colunas ≥760px colapsa para 1; tracking público mobile-first `max-width ~480px`.
- `ux-advanced/dark-mode-theming` — T-11/T-16: dois temas inclusive o mapa (style/tile dark, marcador `--brand` nos dois temas, atribuição OSM legível) e a timeline; reage a `data-theme` sem reload (DEC-001).
- `domain/ionic-patterns` — T-12/T-13: app do entregador é Ionic/Capacitor; entrega ativa e comprovação full-screen na aba Entregas (tabbar oculta na operação ativa, foco na tarefa); Capacitor Camera/Geolocation.
- `product/visual-regression-testing` — T-18: baseline (claro+dark) dos 8 componentes novos + telas 06/07/13/26 (UI-SPEC §12); componentes compartilhados não regridem.

### Backend / segurança / qualidade
- `owasp-security` — T-03/T-05/T-06/T-07/T-10: EXIF é evidência, não autoridade (geofence server-side); IDOR fechado por ownership na query (404 não 403); endpoint público justificado `# público:` + rate limit por IP + token 130 bits não-sequencial; magic bytes na foto (reuso `media/validation.py`); confirmação direta só do courier dono.
- `br/lgpd-compliance` — T-04/T-06/T-10/T-14: minimização no tracking; retenção 24h de `delivery_locations` (job de purga + hard-delete); janela RN-022; base legal = execução de contrato + legítimo interesse (antifraude); `delivery_locations`/`delivery_proofs` alcançáveis pelos endpoints de direitos do titular (Phase 14).
- `quality/performance-web-vitals` — T-16: mapa **lazy** (IntersectionObserver/import dinâmico do MapLibre após primeira pintura); LCP = timeline+banner ETA (texto), nunca o mapa; bundle do mapa fora do chunk crítico; marcador único, sem heatmap/clustering; budget LCP ≤2500ms garantido por não depender do mapa.
- `quality/observability-production` — T-03/T-05/T-06/T-07/T-09: `request_id` em erro; transição/comprovação auditadas (sem PII); filtro central mascara `phone/cpf/email/token`; métrica `% no SLA` (KPI secundário) e `low_confidence_rate`.
- `meta/orchestration-decision-tree` — planejamento: back/front paralelizados por wave; pipeline de comprovação (sensível) isolado em task dedicada com revisão concentrada (RESEARCH §Don't Hand-Roll key insight).
- `domain/fastapi-production-patterns` — T-03/T-05/T-06/T-07/T-10: `/v1`, Pydantic v2 `extra="forbid"`, RFC-7807, dependências de auth/ownership, idempotência onde relevante, enqueue de notificação no arq (nunca síncrono no request).
- `product/api-design-contracts` — T-05/T-06/T-10: contratos estáveis do endpoint público (serializer versionado por estado) e da ingestão de localização; consumidos pelo front (integration_check).
- `domain/mysql-schema-design` — T-02/T-03: `ST_Distance_Sphere` com `POINT(lng,lat)` (SRID/ordem), índice por `recorded_at` em `delivery_locations` (purga), migration 0008 reversível.
- `quality/senior-quality-bar` (Gate 8) — todas: sem segredo no repo, sem N+1 em listagens (tracking/timeline/locations carregam com join/limit), sem injection (query spatial parametrizada), endpoint público com decisão de auth explícita (`# público:`), zero PII em log.

## Skills Dispensadas (com justificativa)

- `domain/saas-billing-canonical` / `domain/safe2pay-escrow-br` — **dispensadas**: cobrança online cartão/PIX/escrow/split é Phase 10; aqui o custo de cancelamento RN-004 é apenas **registrado** na entrega (a cobrança efetiva é a fatura da Phase 11). Nenhuma chamada Safe2Pay nesta phase.
- `br/brazilian-forms` — **dispensada**: não há formulário CPF/CEP/máscara novo relevante. Inputs desta phase são número de referência (mono numérico simples) e radio de pagamento; recipient/forms já existem (Phase 7).
- `ux-advanced/onboarding-patterns` — **dispensada**: sem signup/onboarding nesta phase (entregador já cadastrado na Phase 5). O único opt-in (push) é coberto por `mobile/push-notifications-architecture`.
- `ux-advanced/saas-dashboard-patterns` / `ux-advanced/data-tables-ux` — **dispensadas**: a tela 13 é **detalhe** de uma entrega (timeline + aside), não listagem tabular/dashboard. Listagens da loja são Phase 7/8.
- `ux-advanced/payment-checkout-ux` — **dispensada**: a confirmação de pagamento direto é um fieldset "recebi/não recebi" (sem fluxo de checkout/cartão/PIX online — isso é Phase 10).

---

## Tech debt deste plano (verificação obrigatória v0.8+)

| TD ID | Descrição curta | Por que entra (ou não) neste plano | Task que resolve |
|-------|-----------------|-------------------------------------|------------------|
| TD-010 | Naive datetime proibido em domínio | **Prazo lista Phase 9 explicitamente.** Toda escrita de proof/location/job usa `datetime.now(UTC)`; `UTC_DATETIME` no schema | T-02, T-03, T-06, T-07 (aware-UTC em todas) |
| TD-003 | OTP de comprovação desabilitado ("em breve") | Deferido (ADR-008): `proof_method` aceita `otp` no enum mas só `photo`/`photo_reference` ativos. Badge UI evita retrabalho — **não implementar OTP** | — (escopo M1: foto+GPS) |
| TD-005 | ~~Tracking sem mapa~~ | **Cancelada por DEC-002** — o mapa ao vivo é ENTREGUE nesta phase | T-06, T-16 |
| TD-008 | Antifraude de foto por IA | Deferido pós-M1: em M1 a barreira é geofence server-side + low_confidence + revisão humana; sem contra-prova de IA | — (risco residual documentado em TH-1) |
| TD-014 | Tiles/geocoding OSM público com rate limit | **NOVA TD desta phase (LOW-5/A4):** tiles `tile.openstreetmap.org` têm política restritiva; piloto Pádua aceita baixo volume, self-host/provider antes de escalar | T-19 (registra TD-019) |

Demais TDs (001/002/004/006/007/009/011/012/013/015/016/017/018) não têm prazo nesta phase nem `urgency_class` que force entrada aqui.

---

## Open questions / LOW confidence do RESEARCH (Regra 12 — destino estruturado dos 5 LOW)

| Item RESEARCH | Confidence | Resolução neste plano |
|---------------|------------|------------------------|
| **A1** — `ST_Distance_Sphere` retorna metros e está disponível no MySQL 8 contratado | LOW | **Task T-02**: teste `@pytest.mark.mysql` com par conhecido (coleta ↔ ~100m) valida SRID/ordem e unidade; se indisponível, `geofence.py` cai no **fallback haversine** documentado (já previsto). Vira critério de aceite. |
| **A2** — `deliveries` (0006) tem POINTs de coleta E destino | LOW | **RESOLVIDO na investigação:** `deliveries.pickup_lat/lng` e `dropoff_lat/lng` (Float) já existem (`models.py:117-133`). **Não há backfill/geocoding.** T-02 usa essas colunas em `ST_Distance_Sphere(POINT(lng,lat),…)`. Critério de aceite confirma colunas presentes na 0006. |
| **A3** — Capacitor Camera preserva EXIF GPS no Android real | LOW | **Task T-01 (spike OBRIGATÓRIO, Wave 0)**: validar em device real se o plugin mantém EXIF GPS. **Fallback (contrato definido):** se strippar, capturar GPS via Capacitor Geolocation no momento da captura e enviar `{lat,lng}` junto da foto; o server valida geofence igual (EXIF OU lat/lng client, ambos = evidência, nunca autoridade). Decisão do spike vira contrato da foto consumido por T-03/T-12. |
| **A4 / LOW-5** — fonte de tiles OSM em produção | LOW | **TD-019 registrada** (`urgency_class: post_launch_30d`): piloto Pádua começa com OSM público + atribuição; T-19 abre a TD e cria spike-light de avaliação self-host/provider antes de escalar. Não bloqueia o M1. |
| **A5** — `watchPosition` em background suficiente no SO | LOW | **TD-020 registrada** (`urgency_class: post_launch_30d`): M1 aceita polling **só com app aberto** (Page Visibility pausa em background — degradação consciente e documentada na UI "atualiza a cada minuto"). T-08 implementa com Page Visibility; background contínuo é pós-M1. |

Nenhum item LOW fica como "verificar antes de executar" solto: A1→teste, A2→resolvido, A3→task de spike, A4/A5→TD formal com `urgency_class`.

---

## Threat model

Herdado da seção `## Security Baseline` do RESEARCH (9 ameaças). Destaques: EXIF spoof, tracking público sem auth, IDOR localização, retenção LGPD.

| ID | Ameaça | Vetor | Impacto | Likelihood | Mitigação | Task |
|----|--------|-------|---------|------------|-----------|------|
| TH-1 | **EXIF/GPS spoofing** — app injeta coordenada falsa no raio | EXIF client-supplied | Alto | Médio | Geofence **server-side** (`ST_Distance_Sphere` vs POINT da área, `geofence_m` Phase 6); EXIF nunca é autoridade; `low_confidence` após 3 falhas + revisão humana; GPS gravado na `delivery_state_transition` (RN-012, auditoria). IA antifraude é pós-M1 (TD-008, risco residual aceito) | T-02, T-03 |
| TH-2 | **Upload malicioso de foto** (polyglot, bomba, não-imagem) | bytes do cliente | Alto | Baixo | Magic bytes (`sniff_content_type` ignora content-type declarado) + `MAX_UPLOAD_BYTES` + `MAX_IMAGE_PIXELS` (reuso `media/validation.py`); **MAS** ler GPS do RAW ANTES do reprocess; strip só no derivativo armazenado | T-03 |
| TH-3 | **Tracking público sem auth vaza dados** | endpoint sem login | Alto | Médio | `# público:` por `public_token` opaco (Crockford 26ch ≈130 bits); expõe MÍNIMO (estado/timeline/ETA/posição aproximada); **sem nome/telefone/CPF do courier**; endereço destino só após COLETADA (RN-013); 404 genérico | T-05 |
| TH-4 | **PII no tracking/localização (LGPD)** | retenção indevida | Alto | Médio | Retenção 24h de `delivery_locations` (job `purge_locations`, hard-delete); só lat/lng (sem rastro permanente); telefones só na janela ACEITA→FINALIZADA (RN-022); base legal = execução de contrato | T-06, T-07, T-14 |
| TH-5 | **IDOR na ingestão de localização** — courier B posta na entrega de A | endpoint autenticado mal escopado | Alto | Médio | `get_delivery_for_courier(delivery_id, courier_id=courier.id)` no WHERE → 404; estado deve estar na janela móvel (ACEITA/COLETADA) | T-06 |
| TH-6 | **Enumeração de public_token** | varredura de tokens | Médio | Baixo | Token 130 bits não-sequencial (`_new_public_token` já existe) + **rate limit por IP** no endpoint público; 404 uniforme | T-05 |
| TH-7 | **Confirmação de pagamento direto por ator errado** | auth fraca | Médio | Baixo | `direct_payment_confirmations` só aceita do courier dono (ownership na query); "não recebi" → registro `payment_dispute` (mediação Phase 11) | T-10 |
| TH-8 | **PII em log / payload de push** | log/notificação | Médio | Médio | Push payload = `delivery_id` + deep link + título (`PushMessage`, zero PII); filtro central mascara `phone/cpf/email/token` | T-09 |
| TH-9 | **Link de tracking em SMS vaza** | reencaminhamento/histórico | Baixo | Médio | Link contém só token opaco (não credencial de PII); conteúdo já minimizado (TH-3); SMS só no "a caminho" reduz superfície | T-09, T-05 |

---

## Performance budget (UI + endpoint + mapa)

Herdado de `.planning/config.json > performance_budget` (LCP ≤2500ms, INP ≤200ms, CLS ≤0.1, bundle main ≤400kb gzip).

**Frontend:**
- Tracking público (tela 26): **LCP = timeline + banner ETA** (texto, render imediato), nunca o mapa. Mapa **lazy** (import dinâmico do MapLibre após primeira pintura via IntersectionObserver).
- `maplibre-gl` fora do chunk crítico (lazy route/component); página totalmente utilizável sem o mapa.
- CLS: placeholder de skeleton do mapa reserva altura (sem layout shift ao montar o mapa).
- `prefers-reduced-motion`: sem pan automático/tween — reposicionamento estático do marcador.

**Backend:**
- `POST /v1/deliveries/{id}/locations` (ingestão): leve, p95 ≤ 80ms — 1 INSERT + 1 SELECT de ownership; sem reprocess.
- `GET /v1/public/tracking/{token}` (público): p95 ≤ 150ms; sem N+1 (timeline + última localização carregadas com limit/join único); rate limit por IP.
- `POST proof` (comprovação): p95 ≤ 1500ms (inclui fetch RAW + EXIF + geofence + reprocess + put B2) — aceitável (operação única por transição, não em hot path de listagem).
- N+1: zero em tracking/timeline/locations.

Medição: Lighthouse CI (tracking público); pytest-benchmark nos endpoints de ingestão/público.

---

## Observability checklist (endpoints + jobs)

- [ ] Endpoints novos logam `request_id`, `endpoint`, `method`, `status_code`, `duration_ms` (e `courier_id`/`delivery_id` quando autenticado — IDs, nunca PII).
- [ ] Evento de transição (COLETADA/ENTREGUE/RECUSADA/FINALIZADA) e de comprovação (gps_ok / fora_raio / low_confidence) auditados sem PII — reusa o log estruturado de `transition()`.
- [ ] Erros 4xx → WARNING; 5xx → ERROR + alerta.
- [ ] **Zero PII em logs e no payload de push** (filtro central mascara `phone/cpf/email/token`).
- [ ] Métricas: `% no SLA` (KPI secundário — usa `accepted_at`/`collected_at`/`delivered_at`), `low_confidence_rate` (sinal de pipeline EXIF quebrado — warning sign do Pitfall 1), tamanho de `delivery_locations` (sinal de purga falhando).
- [ ] Jobs `finalize_deliveries`/`purge_locations`/`absent_timeout` logam contagem processada + duração; idempotentes; falha não derruba o worker.
- [ ] `/healthz` inalterado (sem serviço novo de rede além de adapters já existentes).

---

## Error UX checklist (UI — F-06 E1-E6)

- [ ] **E1** GPS fora do raio / sem GPS → "Você está fora do raio do endereço. Aproxime-se ou ative a localização." (acionável; CTA bloqueado até dentro do raio).
- [ ] **3 falhas → low_confidence** → "Não conseguimos confirmar a localização. Sua entrega segue para revisão da equipe — você pode concluir mesmo assim." (CTA destrava; não trava para sempre).
- [ ] **E2 ausente** → tela de espera + telefone (janela RN-022) + timer 10min mono; após timeout → "Retornar ao estabelecimento".
- [ ] **E3 recusa** → exige foto da recusa + motivo (textarea curta).
- [ ] **E4 número não confere** → "Número não confere (tentativa 2 de 3). Confirme com o destinatário ou ligue para a loja." (contador visível; 3x → atalho ligar à loja).
- [ ] **Upload offline** → "Salvo — enviando quando a conexão voltar." / "1 foto aguardando conexão." (reassuro, não erro). Entrega NÃO aparece ENTREGUE até upload+validação concluírem.
- [ ] **Link inválido (público)** → "Link de rastreio expirado ou entrega não encontrada. Confira com a loja." (anti-enumeração, não revela existência).
- [ ] Erro inline ao blur, não modal ao submit; toast vs inline consistente (inline para validação, toast `jx-notice` para notificação).

---

## Integration contracts (integration_check: TRUE — validados por stub, Gate 5)

| Contrato | Consumer | Provider | Assertion |
|----------|----------|----------|-----------|
| `POST /v1/deliveries/{id}/proof` (foto comprovação) | `apps/web` courier/proof (tela 07) | `apps/api/app/proofs/router.py` | multipart/presign com foto (EXIF GPS ou `{lat,lng}` fallback A3); resposta `{state, geofence_ok, low_confidence}` |
| Foto → B2 (`StoragePort`) | `proofs/service.py` | `integrations/storage.py` (B2 + stub) | `fetch(key)` RAW antes de `put_bytes` derivativo; presign correto |
| `POST /v1/deliveries/{id}/locations` (polling) | `apps/web` courier/active-delivery | `apps/api/app/tracking/locations.py` | body `{lat,lng}`; 404 se não-dono; 409 fora da janela |
| `GET /v1/public/tracking/{token}` (mapa+timeline) | `apps/web` public/tracking (tela 26) | `apps/api/app/tracking/public.py` | resposta minimizada por estado; sem PII do courier; tiles OSM carregam |
| Notificações push/SMS/email | `notifications/dispatcher.py` | `PushPort`/`SmsPort`/`EmailPort` (+ stubs) | fallback push→email; SMS só "a caminho"; payload push zero PII |
| Tiles OSM | `jx-live-map` (MapLibre) | `tile.openstreetmap.org` (piloto) | tile source raster carrega; atribuição visível (validado por stub/mocked tile no CI — não bate rede real) |

---

## Tasks

### T-01 — Spike Capacitor Camera/Geolocation EXIF GPS (A3 — OBRIGATÓRIO)

- **Type:** infra (spike)
- **Files:** `apps/web/src/app/courier/proof/exif-spike.md` (achado), POC descartável
- **Skills aplicadas:**
  - `domain/ionic-patterns` — Capacitor Camera/Geolocation plugin no device real
  - `mobile/offline-first` — captura no device, contrato da foto
- **Descrição:** Validar em device Android real se Capacitor Camera preserva EXIF GPS no arquivo capturado. Se SIM → contrato é "foto com EXIF". Se NÃO → contrato é "foto + `{lat,lng}` capturado via Geolocation no momento da captura, enviado junto". O server valida geofence igual nos dois casos (EXIF/lat-lng = evidência, nunca autoridade).
- **Success:** Achado documentado com a decisão do contrato da foto (EXIF-embed OU lat/lng-anexado); consumido por T-03 e T-12.
- **Depends on:** none

### T-02 — Geofence module + `ST_Distance_Sphere` (A1, A2 resolvido)

- **Type:** new_module + test
- **Files:** `apps/api/app/proofs/geofence.py`, `tests/proofs/test_geofence_db.py` (`@pytest.mark.mysql`), `tests/proofs/test_geofence.py` (haversine fallback)
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — `ST_Distance_Sphere(POINT(:plng,:plat), POINT(:tlng,:tlat))` (SRID/ordem lng,lat), parametrizado
  - `owasp-security` — query spatial parametrizada (anti-injection)
- **Descrição:** `within_radius(session, lat, lng, target_lat, target_lng, radius_m)` via `ST_Distance_Sphere`; usa `deliveries.pickup_lat/lng` (COLETADA) ou `dropoff_lat/lng` (ENTREGUE) — **colunas confirmadas em models.py:117-133**. `radius_m = AreaConfig.geofence_m` (Phase 6, default 80). Fallback haversine em Python documentado se a query spatial não compuser (A1).
- **Success:** Teste mysql com par conhecido (coleta ↔ ~100m): dentro do raio passa, fora rejeita; SRID/ordem corretos (distância plausível, não milhares de km — Pitfall 4). Fallback haversine testado isolado.
- **Depends on:** none

### T-03 — Pipeline de comprovação foto+EXIF/GPS (O OPOSTO DO KYC)

- **Type:** new_module + test
- **Files:** `apps/api/app/proofs/exif.py`, `apps/api/app/proofs/service.py`, `apps/api/app/proofs/models.py` (DeliveryProof), `apps/api/app/proofs/router.py`, `apps/api/app/proofs/schemas.py`, `tests/proofs/test_exif.py`, `tests/proofs/test_pipeline_order.py`, `tests/proofs/conftest.py`
- **Skills aplicadas:**
  - `owasp-security` — EXIF é evidência não autoridade; magic bytes (reuso `media/validation.py`); IDOR fechado (courier dono da entrega)
  - `domain/fastapi-production-patterns` — RFC-7807 com motivo legível; Pydantic `extra="forbid"`
  - `quality/observability-production` — log de gps_ok/fora_raio/low_confidence sem PII; aware-UTC (TD-010)
- **Descrição:** Ordem **obrigatória** (Pitfall 1): (a) fetch RAW via `StoragePort.fetch` → (b) magic bytes + size → (c) `extract_gps_from_raw(raw)` com `Image.getexif().get_ifd(IFD.GPSInfo)` (ou `{lat,lng}` client se A3 falhou) → (d) `within_radius` (T-02) → (e) ≤raio? OK : reject; conta falhas, 3ª → `low_confidence=True` + CTA destrava → (f) `reprocess_to_webp` + STRIP → B2 derivativo → (g) `transition()` (T-04) com `gps=(lat,lng)` para auditoria (RN-012). **NUNCA** chamar `reprocess_to_webp` antes de (c). `DeliveryProof` grava key, geofence_ok, low_confidence, método (coleta/entrega/recusa).
- **Success:** `test_pipeline_order` prova EXIF lido antes do strip; foto sem GPS/fora do raio → reject server-side; 3 falhas → low_confidence; conftest gera JPEG com GPS conhecido (piexif só no teste).
- **Depends on:** T-01, T-02

### T-04 — Transições F-06 (COLETADA/ENTREGUE/RECUSADA) + reveal RN-013 + cancelamentos RN-004

- **Type:** new_endpoint + test
- **Files:** `apps/api/app/proofs/service.py` (transições), `apps/api/app/deliveries/service.py` (reveal helper, cancel cost), `tests/proofs/test_transitions.py`, `tests/deliveries/test_cancel_cost.py`
- **Skills aplicadas:**
  - `owasp-security` — máquina de estados server-side append-only (reuso `transition()` Phase 7, RN-019)
  - `domain/fastapi-production-patterns` — `/v1`, AreaScoped, RFC-7807
  - `br/lgpd-compliance` — endereço destino só revelado APÓS COLETADA (RN-013, por construção)
- **Descrição:** ACEITA→COLETADA (com foto coleta T-03) revela `dropoff_address/number/complement` (RN-013). COLETADA→ENTREGUE (foto entrega OU número de referência T-09). COLETADA→RECUSADA_NO_DESTINO (reason `absent`/`refused`). Reuso de `transition()` (não reescrever a máquina). Cancelamento RN-004: custo calculado server-side por estado (antes da coleta 50%, após coleta 100%+retorno via `AreaConfig`) **registrado** na entrega (cobrança = Phase 11, não aqui).
- **Success:** Transições inválidas → 422 (máquina Phase 7); endereço completo só aparece no payload após COLETADA (teste por estado); custo de cancelamento correto por estado e apenas registrado.
- **Depends on:** T-03

### T-05 — Endpoint público de tracking + serializer de minimização de PII

- **Type:** new_endpoint + test
- **Files:** `apps/api/app/tracking/public.py`, `apps/api/app/tracking/serializer.py`, `tests/tracking/test_public.py`, `tests/tracking/test_serializer_pii.py`, `tests/tracking/test_phone_window.py`
- **Skills aplicadas:**
  - `owasp-security` — `# público:` justificado; 404 genérico; rate limit por IP (reuso `core/ratelimit.py`); token opaco
  - `br/lgpd-compliance` — minimização por estado; sem PII do courier; telefone só na janela ACEITA→FINALIZADA (RN-022)
  - `product/api-design-contracts` — contrato estável consumido pela tela 26
- **Descrição:** `GET /v1/public/tracking/{public_token}` SEM auth. `serialize_public(d)`: estado + timeline + ETA + posição aproximada (última `delivery_location`, snap a via); `dropoff` completo só em COLETADA/ENTREGUE/FINALIZADA, senão bairro; **nunca** nome completo/telefone/CPF do courier nem telefone do destinatário no payload. Token inválido → 404 genérico (anti-enumeração). Janela de telefones aplicada no serializer (RN-022).
- **Success:** Responde sem auth; token inválido → 404; payload sem PII proibida (teste assertivo de chaves); endereço só após COLETADA; telefone ausente fora de ACEITA→FINALIZADA.
- **Depends on:** T-02 (modelos), pode rodar paralelo a T-03/T-04 na estrutura

### T-06 — Ingestão de localização (anti-IDOR) + `delivery_locations`

- **Type:** new_endpoint + migration-part + test
- **Files:** `apps/api/app/tracking/locations.py`, `apps/api/app/tracking/models.py` (DeliveryLocation), `tests/tracking/test_locations_authz.py`
- **Skills aplicadas:**
  - `owasp-security` — ownership na query (`get_delivery_for_courier`), 404 não 403; janela de estado
  - `br/lgpd-compliance` — só lat/lng; `recorded_at` aware-UTC; índice por `recorded_at` para purga
  - `quality/performance-web-vitals` — endpoint leve (1 SELECT ownership + 1 INSERT)
- **Descrição:** `POST /v1/deliveries/{id}/locations` autenticado por courier. `get_delivery_for_courier(delivery_id, courier_id=courier.id)` → 404 se não-dono (TH-5). Estado deve estar em `ACEITA`/`COLETADA` → senão 409 ("fora da janela"). Grava `DeliveryLocation(delivery_id, area_id, lat, lng, recorded_at=now(UTC))`. `area_id` para AreaScoped.
- **Success:** Courier B postando na entrega de A → 404; fora da janela → 409; aware-UTC; INSERT idempotente-tolerante.
- **Depends on:** none (DeliveryLocation model definido aqui; migration agregada em T-11/T-02-migration — ver execution order)

### T-07 — Jobs de ciclo arq (finalize 24h / purge 24h / absent 10min)

- **Type:** infra (cron) + test
- **Files:** `apps/api/app/workers/lifecycle.py`, `apps/api/app/workers/settings.py` (registrar cron_jobs), `tests/workers/test_finalize.py`, `tests/workers/test_purge_locations.py`, `tests/workers/test_absent_timeout.py`
- **Skills aplicadas:**
  - `br/lgpd-compliance` — `purge_locations` hard-delete de `delivery_locations` >24h (retenção)
  - `quality/observability-production` — jobs idempotentes, logam contagem+duração, falha não derruba worker; aware-UTC
- **Descrição:** `finalize_deliveries`: ENTREGUE há >24h sem `payment_dispute` aberta → `transition()` FINALIZADA (D-06). `purge_locations`: DELETE `delivery_locations` de entregas terminais há >24h. `absent_timeout`: "ausente" há >10min sem resposta → habilita "retornar" (D-07 E2). Registrar em `WorkerSettings.cron_jobs` (mantém `functions` existentes, append-only no settings).
- **Success:** finalize só após 24h e sem disputa; purge remove >24h e preserva <24h; absent habilita após 10min; todos idempotentes (rodar 2x não duplica efeito).
- **Depends on:** T-04 (transition FINALIZADA), T-06 (DeliveryLocation)

### T-08 — Polling de localização resiliente + offline (front, A5)

- **Type:** ui_service
- **Files:** `apps/web/src/app/courier/active-delivery/location-polling.service.ts`, specs
- **Skills aplicadas:**
  - `mobile/offline-first` — polling pausa offline/background, filtro de movimento 50m, não acumula posições obsoletas
  - `domain/ionic-patterns` — Capacitor Geolocation `watchPosition`/`getCurrentPosition`
- **Descrição:** Polling HTTP 60-120s para `POST locations` (T-06). **Page Visibility API pausa** em background (A5 — M1 só com app aberto, degradação consciente → TD-020). Filtro 50m client-side. Resiliente: pausa offline, retoma online. Só ativo na janela ACEITA→COLETADA.
- **Success:** Pausa comprovada quando aba/app em background; não envia posições <50m de movimento; retoma após reconexão.
- **Depends on:** T-06

### T-09 — Notificações multicanal + push_subscriptions + confirmação direta

- **Type:** new_module + new_endpoint + test
- **Files:** `apps/api/app/notifications/dispatcher.py`, `apps/api/app/notifications/models.py` (Notification, PushSubscription), `apps/api/app/notifications/router.py`, `apps/api/app/payments_direct/service.py`, `apps/api/app/payments_direct/models.py` (DirectPaymentConfirmation), `tests/notifications/test_dispatcher.py`, `tests/payments_direct/test_confirm.py`
- **Skills aplicadas:**
  - `mobile/push-notifications-architecture` — `push_subscriptions` registro de device; payload zero PII (`PushMessage`)
  - `owasp-security` — confirmação direta só do courier dono (TH-7); PII fora de payload/log (TH-8)
  - `quality/observability-production` — registra cada tentativa em `notifications` (canal/status)
- **Descrição:** `dispatcher.notify(moment, delivery, ...)` enfileirado no arq: aceite/entregue → push→email; "a caminho" → push + SMS (só aqui, quota RN-018, Zenvia→Twilio→email) + email. Reusa `PushPort`/`SmsPort`/`EmailPort`. `POST/DELETE push_subscriptions`. Confirmação direta (RN-026): `cash`/`pix` → grava `DirectPaymentConfirmation`; `not_received` → ENTREGUE + abre registro `payment_dispute` (mediação Phase 11).
- **Success:** fallback push→email testado; SMS só no "a caminho"; "não recebi" → ENTREGUE + dispute; cada tentativa em `notifications`.
- **Depends on:** T-04

### T-10 — Número de referência + liberação manual (E4)

- **Type:** new_endpoint + test
- **Files:** `apps/api/app/proofs/service.py` (validação referência), `tests/proofs/test_reference.py`
- **Skills aplicadas:**
  - `quality/error-ux-patterns` — 3 tentativas → orientar; contador
  - `owasp-security` — liberação manual só pela loja dona, auditável
- **Descrição:** Método `photo_reference`: compara contra `delivery.reference_number`; 3 falhas → orienta ligar à loja + CTA bloqueado por nº. Liberação manual pela loja (registro auditável em transition reason).
- **Success:** nº correto → ENTREGUE; 3x errado → bloqueio + orientação; liberação manual registrada.
- **Depends on:** T-04

### T-11 — Migration 0008 (reversível) + 8 componentes UI base

- **Type:** migration + ui_component
- **Files:** `apps/api/alembic/versions/0008_*.py`, `apps/web/src/app/shared/` (8 componentes novos), `tests/db/test_migration_0008.py`
- **Skills aplicadas:**
  - `domain/mysql-schema-design` — 0008 cria `delivery_proofs`, `delivery_locations`, `notifications`, `push_subscriptions`, `direct_payment_confirmations`; índice `recorded_at`; **`downgrade` sem `drop_index` redundante de FK** (lição 0006)
  - `product/component-library-governance` + `ux-advanced/design-tokens-system` — scaffolds dos 8 componentes via tokens
- **Descrição:** Migration 0008 agregando todas as tabelas novas (modelos de T-03/T-06/T-09); `upgrade`/`downgrade` simétricos e reversíveis. Scaffolds dos 8 componentes novos (estrutura + tokens, lógica nas tasks de UI).
- **Success:** `alembic upgrade head` + `downgrade -1` limpos; tabelas presentes; componentes renderizam com tokens (zero `#hex`).
- **Depends on:** T-03, T-06, T-09 (modelos definidos)

### T-12 — Tela 06 (entrega ativa) + tela 07 (comprovação) — Entregador Ionic

- **Type:** ui_component
- **Files:** `apps/web/src/app/courier/active-delivery/` (tela 06), `apps/web/src/app/courier/proof/` (tela 07: `jx-proof-capture`, `jx-geofence-pill`, `jx-direct-payment-confirm`)
- **Skills aplicadas:**
  - `ux-advanced/file-upload-ux` + `domain/ionic-patterns` — câmera reusa `jx-doc-upload` (`capture="environment"`)
  - `ux-advanced/gesture-touch-patterns` — sem swipe em ação crítica; botões ≥52px
  - `quality/error-ux-patterns` + `quality/accessibility-pro` — GPS pill 3 estados (text+ícone, nunca cor só), aria-live, low_confidence destrava CTA
  - `br/ux-copywriting-ptbr` — contrato de copy UI-SPEC §10
- **Descrição:** Wireframe-contract de 06 (mapa rota lazy + overline progresso + contato janela RN-022 + CTA carvão + mini-stepper) e 07 (geofence pill + câmera + nº referência + pagamento direto + desvios ausente/recusa + timer 10min). Estados loading/sucesso/vazio/erro/offline.
- **Success:** Wireframe-contract 06/07; sem swipe crítico; GPS pill 3 estados acessíveis; CTA bloqueia/destrava conforme veredito server-side.
- **Depends on:** T-03, T-04, T-08, T-11

### T-13 — Upload offline-tolerante (`jx-pending-upload-banner`)

- **Type:** ui_service + ui_component
- **Files:** `apps/web/src/app/courier/proof/pending-upload.service.ts`, `jx-pending-upload-banner`
- **Skills aplicadas:**
  - `mobile/offline-first` — foto no device, sobe ao reconectar; transição só conclui com upload OK
  - `quality/accessibility-pro` — `role="status"`; status text+ícone
  - `br/ux-copywriting-ptbr` — "Salvo — enviando quando a conexão voltar."
- **Descrição:** Foto salva localmente quando offline (`pending_upload`); banner com contador; entrega exibida "Pendente de envio" (não ENTREGUE) até upload+validação server-side; ao reconectar retoma progresso e transiciona.
- **Success:** Com rede caída a UI mostra fila (não erro); entrega não vira ENTREGUE até upload OK; reconexão conclui.
- **Depends on:** T-12

### T-14 — Tela 13 (loja — detalhe da entrega)

- **Type:** ui_component
- **Files:** `apps/web/src/app/merchant/delivery-detail/` (`jx-tracking-timeline` reuso, cancelamento RN-004, liberação manual E4)
- **Skills aplicadas:**
  - `ux-advanced/responsive-breakpoint-strategy` — 2 colunas ≥760px colapsa
  - `br/ux-copywriting-ptbr` — rótulo de cancelar declara custo ("Cancelar (cobra 100% + retorno)")
  - `quality/accessibility-pro` — modal de cancelamento `role="dialog"`, ordem de tabulação 2 colunas
  - `br/lgpd-compliance` — telefone mascarado mono; janela RN-022
- **Descrição:** Wireframe-contract de 13: header + estado, mapa loja (lazy), timeline real, comprovações (thumbs), aside entregador (`jx-accepted-courier-card`) + valores + destinatário + link `/r/{token}`. Cancelamento com custo explícito (registro, cobrança Phase 11). Liberação manual E4.
- **Success:** Wireframe-contract 13; cancelar declara custo no rótulo; telefone mascarado; link público presente.
- **Depends on:** T-04, T-05, T-11

### T-15 — `jx-tracking-timeline` + `jx-tracking-banner` (compartilhados 13/26)

- **Type:** ui_component
- **Files:** `apps/web/src/app/shared/tracking/` (`jx-tracking-timeline`, `jx-tracking-banner`)
- **Skills aplicadas:**
  - `ui-ux-pro-max` — timeline tipográfica (mono nos horários/ETA), persimmon só no estado atual
  - `quality/accessibility-pro` — `aria-live` no item current; ponto preenchido (forma) + label `--text` (nunca cor só)
  - `ux-advanced/empty-states-polish` — pré-coleta tranquiliza
- **Descrição:** 7 estados em linha do tempo vertical (`color.delivery_state.*`), banner de ETA. Reusada em 13 (loja) e 26 (público). É a alternativa textual do mapa e o LCP do tracking.
- **Success:** Estados done/current/futuro distinguíveis por forma+label (não só cor); aria-live anuncia mudança.
- **Depends on:** T-11

### T-16 — Tela 26 (tracking público) + `jx-live-map` lazy + dark

- **Type:** ui_component
- **Files:** `apps/web/src/app/public/tracking/` (tela 26, SEM auth guard), `apps/web/src/app/shared/map/jx-live-map` (MapLibre)
- **Skills aplicadas:**
  - `quality/performance-web-vitals` — mapa lazy (import dinâmico pós-primeira-pintura); LCP = timeline; bundle do mapa fora do chunk crítico
  - `ux-advanced/trust-safety-ux` — só PII permitida; footer de procedência; posição aproximada
  - `ux-advanced/dark-mode-theming` — style/tile dark; marcador `--brand` nos dois temas; atribuição OSM legível
  - `quality/accessibility-pro` — mapa `role="img"`/`aria-label`; alternativa textual = timeline+ETA
  - `ux-advanced/empty-states-polish` — link inválido/expirado → `jx-error-state`
- **Descrição:** Wireframe-contract de 26: header de marca (Fraunces "rapidinho."), mapa lazy, banner estado+ETA, timeline, card entregador (PII limitada), footer. Mapa só na janela ACEITA→FINALIZADA. `maplibre-gl@^5.24.0` lazy. Refresh ~60s.
- **Success:** Wireframe-contract 26; LCP é a timeline (Lighthouse — mapa não atrasa LCP); link inválido → estado de erro; sem PII proibida no DOM; dark mode do mapa.
- **Depends on:** T-05, T-15

### T-17 — Notificações UI (`jx-notice`) + opt-in push

- **Type:** ui_component
- **Files:** `apps/web/src/app/shared/notice/jx-notice`, opt-in service
- **Skills aplicadas:**
  - `mobile/push-notifications-architecture` — opt-in contextual (após 1ª entrega, não no load); fallback silencioso
  - `quality/accessibility-pro` — toast `role="status"`, não rouba foco
  - `br/ux-copywriting-ptbr` — copy dos 3 momentos
- **Descrição:** `jx-notice` (in-app espelha push); opt-in contextual; gerência mínima em perfil ("Receber avisos neste aparelho" toggle `aria-pressed`).
- **Success:** opt-in não aparece no primeiro load; toast não rouba foco; fallback silencioso se negado.
- **Depends on:** T-09, T-11

### T-18 — Visual regression baseline (8 componentes + 4 telas)

- **Type:** test
- **Files:** stories/baselines (claro+dark) UI-SPEC §12
- **Skills aplicadas:**
  - `product/visual-regression-testing` — baseline dos 8 componentes novos + telas 06/07/13/26 (claro+dark)
- **Descrição:** Snapshots dos estados listados em UI-SPEC §12. Nome `{component}-{state}-{theme}-{viewport}.png`.
- **Success:** Baselines gravadas; CI compara; sem diff inesperado em componentes compartilhados.
- **Depends on:** T-12, T-13, T-14, T-15, T-16, T-17

### T-19 — Registrar TD-019 (tiles OSM produção) + TD-020 (background polling)

- **Type:** infra (doc)
- **Files:** `.planning/TECH-DEBT.md`
- **Skills aplicadas:**
  - `quality/observability-production` — registrar gatilho de escalonamento de volume
- **Descrição:** TD-019 (tiles OSM produção, A4/LOW-5, `post_launch_30d`, gatilho: volume > rate limit público → self-host/provider). TD-020 (background polling, A5, `post_launch_30d`, gatilho: M2/SO exigir background contínuo).
- **Success:** Duas TDs com `urgency_class` e gatilho em TECH-DEBT.md.
- **Depends on:** none

---

## Execution order

**parallel-hint: SIM** — back-front candidato. Backend (proofs/tracking/notifications/jobs) e frontend (telas/componentes) paralelizam por wave; o contrato A3 (T-01) destrava a câmera, e os endpoints (T-05/T-06) destravam o consumo do front.

- **Wave 0 (spikes/fundação, paralelo):** T-01 (spike A3 obrigatório), T-02 (geofence+mysql), T-19 (TDs). *Wave 0 cria os contratos e os scaffolds de teste (RESEARCH Wave 0 Gaps).*
- **Wave 1 (backend núcleo, paralelo):** T-03 (pipeline comprovação), T-05 (tracking público), T-06 (ingestão localização). *(T-03 depende de T-01+T-02; T-05/T-06 só de T-02/modelos.)*
- **Wave 2 (backend orquestração, paralelo):** T-04 (transições+reveal+cancel), T-09 (notificações+confirmação direta), T-10 (número referência). *(dependem de T-03.)*
- **Wave 3 (jobs + migration + front service):** T-07 (jobs ciclo), T-11 (migration 0008 + scaffolds), T-08 (polling front). *(T-07 dep T-04/T-06; T-11 dep modelos T-03/T-06/T-09; T-08 dep T-06.)*
- **Wave 4 (UI, paralelo):** T-12 (06/07), T-14 (13), T-15 (timeline/banner), T-17 (notificações UI). *(dependem de endpoints + T-11.)*
- **Wave 5 (UI dependente):** T-13 (offline — dep T-12), T-16 (tracking 26 — dep T-05+T-15).
- **Wave 6 (verificação visual):** T-18 (visual regression — dep todas as UI).

*Squad-review pós-execute (ROADMAP) com foco concentrado nas 2 peças sensíveis: pipeline de comprovação (ordem EXIF) e endpoint público (minimização PII).*

---

## Reconciliation expectations

`/gsd:reconcile-state 9` verifica:
- Arquivos de cada task existem; endpoints declarados têm handler.
- **Pipeline de comprovação:** `extract_gps_from_raw` é chamado ANTES de `reprocess_to_webp` no código real (não só no teste).
- Geofence usa `ST_Distance_Sphere` parametrizado (ou fallback haversine documentado).
- Serializer público NÃO emite chaves de PII proibida.
- `delivery_locations` tem índice `recorded_at` e job de purga registrado em `WorkerSettings.cron_jobs`.
- Migration 0008 tem `downgrade` simétrico (sem `drop_index` redundante de FK).
- Sem feature-fantasma (código sem task) nem arquivo-fantasma.

---

## Rollback plan

- Revert dos commits `feat(phase-9/...)` por task.
- Migration: `alembic downgrade -1` (0008 reversível) — remove as 5 tabelas novas.
- Ops: nenhum segredo novo (VAPID/B2/SMS/SES reusados); remover novos `cron_jobs` do worker e redeploy; remover `maplibre-gl` do bundle.

---

## Plan-checker report

{Preenchido automaticamente pelo gsd-plan-checker}

- Status: {PASS | FLAG | BLOCK}
- Skills coverage: {X/Y obrigatórias citadas}
- Threat model: presente (9 ameaças herdadas do Security Baseline)
- Performance budget: presente (UI + endpoint + mapa lazy)
- Observability checklist: presente
- Integration contracts: presente (6 contratos)
- Revision iteration: 1
