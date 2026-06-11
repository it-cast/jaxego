# Phase 9: Execução, comprovação, tracking público e notificações - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Fecha o ciclo operacional da entrega (F-06): do `ACEITA` até `FINALIZADA`. O entregador segue até a coleta, tira **foto com GPS** (geofence, RN-005/RN-017) → `COLETADA` (**revela o endereço completo do destino** — RN-013), segue até o destino, tira foto da entrega (ou valida número de referência) → `ENTREGUE`; se pagamento **direto**, confirma o recebimento (RN-026); após 24h sem disputa → `FINALIZADA` (job). Trata os desvios `RECUSADA_NO_DESTINO` (ausente/recusado, RN-004 retorno). Entrega o **tracking público** (tela 26, sem login) com timeline + **mapa em tempo real** (DEC-002 — GPS polling 60-120s, MapLibre/OSM tiles, `delivery_locations`), as **notificações** em 3 momentos (push/e-mail; SMS só "a caminho" RN-018) multicanal com fallback, a janela de telefones (RN-022), e os cancelamentos RN-004. Inclui `delivery_proofs`, `delivery_locations` (DEC-002), `notifications`, `direct_payment_confirmations`, `push_subscriptions`. **Não** entrega cobrança online cartão/PIX (Phase 10), fatura mensal/disputas/saques (Phase 11), nem score (Phase 13). Disputa de pagamento direto "não recebi" abre registro mas a mediação completa é Phase 11/13.
</domain>

<decisions>
## Implementation Decisions

### Coleta → entrega → comprovação (F-06)
- **D-01:** ACEITA → app mostra rota até coleta + ligar/mensagem (janela de telefones RN-022). "Cheguei na coleta" → confere itens → **foto da coleta** (mercadoria/fachada) com **GPS validado no raio da coleta** (geofence 80m default da área, Phase 6) → `COLETADA`. **Endereço completo do destino revelado AGORA** (RN-013). [auto] (F-06 passos 1-3).
- **D-02:** Rota até destino. Geofence de aproximação dispara notificação "está chegando" ao destinatário. No destino: **foto da entrega** (porta/fachada/recebedor); se método = número de referência → digita o nº; valida contra reference_number. → `ENTREGUE`. [auto] (F-06 passos 4-5).

### Comprovação foto+EXIF/GPS (RN-005/RN-017, ADR-008)
- **D-03:** Toda transição para COLETADA/ENTREGUE exige **foto com EXIF/GPS dentro do raio** (server-side: extrair EXIF GPS, validar geofence; sem GPS válido → bloqueia e orienta; 3 falhas → flag `low_confidence` + revisão do admin de área). Foto no B2 (reuso StoragePort Phase 5). **OTP de comprovação fica fora do M1** (TD-003). [auto] travado por RN-005/RN-017/ADR-008.
- **D-04:** Upload offline-tolerante (mobile/offline-first): foto fica no device e sobe quando reconectar (flag pending_upload); a transição só conclui com upload OK. [auto] (integracoes.md §7).

### Pagamento direto — confirmação (RN-026)
- **D-05:** Se pagamento = direto → tela "Recebeu o pagamento?" → entregador confirma "Recebi R$ X em dinheiro/PIX" (`direct_payment_confirmations`). "Não recebi" → entrega conclui (ENTREGUE) mas abre `payment_dispute` (registro; mediação é Phase 11/13). [auto] travado por RN-026/F-06 E6.

### FINALIZADA (job)
- **D-06:** Após 24h sem disputa → `FINALIZADA` (job arq). No M1 (só direto) não há liberação de saldo (escrow é Phase 10/11). [auto] (F-06 passo 8, RN-006 nota).

### Desvios (F-06)
- **D-07:** E2 destinatário AUSENTE → botão "ausente" → notifica + telefone p/ ligar → 10min sem resposta → "retornar" → `RECUSADA_NO_DESTINO` (reason absent); loja paga corrida + retorno (RN-004, % da área). E3 RECUSA → foto + motivo → RECUSADA_NO_DESTINO (reason refused). E1 foto sem GPS/fora do raio → rejeição na hora; 3 falhas → low_confidence. E4 número de referência não bate (3x) → orientar ligar à loja. [auto] (F-06 E1-E4).
- **D-08:** Cancelamentos RN-004: antes do aceite custo zero (Phase 8); após aceite antes da coleta → 50% da corrida; após coleta → 100% + retorno (% da área). No M1 (direto) isso é registrado na entrega; cobrança efetiva é fatura (Phase 11). [auto] travado por RN-004.

### Tracking público + mapa ao vivo (DEC-002)
- **D-09:** Tracking público (tela 26, SEM login, via public_token da Phase 7): timeline dos estados + ETA + **mapa em tempo real** — posição aproximada do entregador (DEC-002/ADR-101 promovida): app do entregador faz **polling de localização HTTP 60-120s** (filtro de movimento 50m, Page Visibility pausa em background), grava em `delivery_locations` (retenção 24h pós-entrega); o mapa usa tiles OpenStreetMap/MapLibre. **NUNCA expõe PII do entregador além do permitido** (RN-013/RN-022); endereço completo do destino só no tracking após COLETADA. [auto] travado por DEC-002/ADR-101.

### Notificações (RN-018, RN-022)
- **D-10:** Notificações proativas ao destinatário em 3 momentos (aceite, a caminho/aproximação, entregue). Canal: **push/e-mail**; **SMS somente no "a caminho"** com link de tracking (quota do plano — RN-018). Multicanal com fallback (push→email; SMS provider primário→fallback→email). Telefones acessíveis às partes só na janela ACEITA→FINALIZADA (RN-022). `notifications` + `push_subscriptions` (registro do device do entregador/loja). [auto] travado por RN-018/RN-022.

### Claude's Discretion
- Lib de extração de EXIF GPS (Pillow/exifread) server-side.
- Mecânica do polling de localização (endpoint de ingestão + tabela + retenção via job).
- Componente de mapa Angular (MapLibre GL JS) e fonte de tiles.
- Estrutura de notifications (adapter multicanal reusando push da Phase 8 + SMS/SES adapters da Phase 4).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fluxo e regras
- `projeto/regras-negocio/fluxos.md` §F-06 (`:109-128`) — coleta/entrega/comprovação + exceções E1-E6
- `projeto/regras-negocio/regras.md` — RN-004 (cancelamento), RN-005 (geofence), RN-013 (endereço destino), RN-017 (foto comprovação), RN-018 (notificações), RN-022 (janela telefones), RN-026 (confirmação pagamento direto)
- `projeto/regras-negocio/entidades.md` §Transacional (delivery_proofs, delivery_state_transitions, direct_payment_confirmations, recipients), §Integração (notifications)
- `.planning/DECISIONS.md` — ADR-008 (comprovação foto+GPS), **DEC-002 (mapa tempo real M1 / ADR-101 promovida)**, ADR-012 (pagamento direto)

### Integrações
- `projeto/docs-externos/integracoes.md` §4 (SMS), §5 (SES), §6 (Web Push), §7 (B2), §8 (OSRM/tiles)

### UI
- `projeto/wireframes/06-entregador-entrega-ativa.html`, `07-entregador-comprovacao.html`, `13-loja-detalhe-entrega.html`, `26-tracking-publico.html`
- Design system + componentes Phase 3-8 (apps/web), MapLibre (novo)

### Backend a reusar
- Phase 5: StoragePort (B2) + pipeline de imagem (EXIF — aqui PRESERVAR GPS, não strip!) — atenção: KYC fazia strip de EXIF; comprovação PRECISA do GPS.
- Phase 7: máquina de estados (COLETADA/ENTREGUE/RECUSADA_NO_DESTINO/FINALIZADA), deliveries, public_token, delivery_state_transitions
- Phase 8: push adapter, geofence/AreaConfig (Phase 6), elegibilidade
- Phase 4: SMS/SES adapters (multicanal)
- arq worker (jobs FINALIZADA, retenção de localização, ausente 10min)

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-026 (F-06), REQ-027 (foto+EXIF/GPS), REQ-028 (número referência), REQ-029 (cancelamentos), REQ-030 (tracking público), REQ-031 (notificações), REQ-032 (janela telefones), REQ-035 parcial (confirmação direto), REQ-049 (multicanal fallback), REQ-055 (estados UI)

### Segurança (Gate 4)
- `.claude/skills/standalone/owasp-security/SKILL.md` (link público sem auth, EXIF server-side, IDOR, geofence anti-spoof), `.claude/skills/br/lgpd-compliance/SKILL.md` (PII no tracking, retenção localização)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 5 StoragePort (B2) — REUSAR para fotos de comprovação. **DIFERENÇA CRÍTICA:** KYC fazia strip de EXIF; comprovação PRECISA extrair e validar o GPS do EXIF (não remover). Pipeline diferente (extrair GPS → validar geofence → guardar com flag).
- Phase 7 transition() + máquina de estados — COLETADA/ENTREGUE/RECUSADA/FINALIZADA.
- Phase 8 push adapter + Phase 4 SMS/SES adapters → notifications multicanal.
- Phase 6 AreaConfig (geofence_m, política_retorno) + elegibilidade espacial.
- arq jobs (FINALIZADA 24h, retenção localização 24h, ausente 10min).
- public_token (Phase 7) → tracking público sem login.

### Established Patterns
- `/v1` API, AreaScoped, RFC-7807, aware UTC (TD-010), PII fora de log, máquina de estados server-side, adapter+Stub.
- Tracking público é endpoint SEM auth (via public_token) — atenção a IDOR/enumeração de token (ULID opaco).

### Integration Points
- Consome ACEITA (Phase 8) → produz FINALIZADA. Fotos no B2. Notificações push/SMS/email. Mapa via tiles OSM. delivery_locations alimenta o mapa público.
</code_context>

<specifics>
## Specific Ideas

- **EXIF GPS é o oposto do KYC:** KYC remove EXIF (privacidade); comprovação EXTRAI e valida o GPS (antifraude geofence). Não confundir os pipelines.
- **DEC-002 (sua decisão):** mapa em tempo real no M1 — polling 60-120s, MapLibre/OSM, delivery_locations retenção 24h, Page Visibility pausa. WebSocket rejeitado (custo).
- Tracking público (tela 26) é SEM login — segurança via public_token opaco; nunca vazar PII do entregador/destinatário além do permitido (RN-013/RN-022).
- SMS só no "a caminho" (economia de quota, RN-018) — demais momentos push/email.
- Foto sem GPS/fora do raio → bloqueia; 3 falhas → low_confidence + revisão admin (não trava a operação para sempre).
- Upload offline-tolerante (interior tem conexão ruim) — foto no device, sobe depois.

</specifics>

<deferred>
## Deferred Ideas

- Cobrança online cartão/PIX + escrow + liberação de saldo — Phase 10.
- Fatura mensal de taxas + disputas (mediação completa) + saques — Phase 11.
- OTP de comprovação (entregador nunca vê o código) — pós-M1 (TD-003, RN-007).
- Score com peso — Phase 13 (ADR-013).
- Antifraude de foto por IA — pós-M1 (TD-008).
- "Aceitou e sumiu" (2× ETA) — registrado; automação fina pós-M1.
</deferred>

---

*Phase: 09-execu-o-comprova-o-tracking-p-blico-e-notifica-es*
*Context gathered: 2026-06-10*
