# Phase 8: Despacho em cascata + oferta + aceite - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega o fluxo F-05: uma entrega `CRIADA` (Phase 7) é despachada em **cascata** (favoritos → ranking automático), oferecida a um entregador por vez com **timeout** (Redis TTL como fonte de verdade — ADR-104), e **aceita** com **lock transacional** que garante aceite único mesmo em corrida de rede. No aceite, a entrega vai a `ACEITA` (máquina de estados da Phase 7), as demais ofertas pendentes da cascata são canceladas, e loja+destinatário são notificados (push). A oferta ao entregador mostra **apenas bairro + distância** do destino (RN-013 — endereço completo só após coleta, Phase 9). Inclui as entidades `merchant_courier_favorites`/`merchant_courier_blocks`, o ranking (distância em rota via OSRM + score + carga + preço), e o app do entregador (home online/offline + sheet de oferta com cronômetro). **Não** entrega coleta/comprovação/entrega (Phase 9 — a entrega para em ACEITA), nem cobrança (Phase 10).
</domain>

<decisions>
## Implementation Decisions

### Cascata de despacho (ADR-007 / RN-009)
- **D-01:** Cascata SEQUENCIAL (nunca broadcast — RN-009). 1) monta elegíveis: online + cobre coleta E entrega (Phase 6) + carga < limite + não bloqueado pela loja. 2) Se a loja tem favoritos elegíveis → cascata nos favoritos (1 por vez, timeout configurável da área default 20s; janela total de favoritos default 60s — config da Phase 6). 3) Esgotou favoritos → cascata no ranking automático. [auto] travado por ADR-007/RN-009.
- **D-02:** Ranking automático = distância em rota (OSRM) + score (placeholder Phase 13 — no M1 score coletado mas sem peso financeiro, ADR-013) + carga atual + preço da tabela do entregador. [auto] (ADR-007).

### Oferta com timeout (ADR-104)
- **D-03:** Cada oferta tem timer configurável por área (10-60s, default 20s); **Redis TTL é a fonte de verdade** do timer; o cronômetro do app é só visual. Timeout/recusa → próximo da cascata. [auto] travado por ADR-104.
- **D-04:** Oferta no app mostra: origem (endereço completo da coleta), destino (apenas BAIRRO + distância — RN-013), valor da corrida, cronômetro. Endereço completo do destino só após coleta (Phase 9). [auto] travado por RN-013.

### Aceite único (lock — peça crítica)
- **D-05:** Aceite usa **lock transacional** (Redis lock por entrega + SELECT FOR UPDATE no DB — reuso do padrão da Phase 7). Dois aceites simultâneos (corrida de rede) → o segundo recebe "essa entrega acabou de ser aceita" sem penalidade (F-05 E3). Aceite → transição CRIADA→ACEITA (Phase 7); demais ofertas da cascata canceladas; nome/foto/placa/score do entregador visíveis para a loja. [auto] travado por ADR-007 + F-05 E3.

### Favoritos e bloqueados
- **D-06:** `merchant_courier_favorites` e `merchant_courier_blocks` (pares loja↔entregador, SEPARADOS). Bloqueio é privado, vale só para aquela loja, não afeta score do entregador (RN-014). Favoritos entram primeiro na cascata; bloqueados nunca recebem oferta da loja. [auto] travado por RN-014.

### Exceções (F-05)
- **D-07:** E1 cascata esgotada sem aceite → loja notificada com opções (aumentar frete/re-oferta, aguardar/re-cascata em 2min, cancelar sem custo). E4 loja cancela durante cascata → ofertas canceladas, sem custo (só cobra após aceite — RN-004). E2 (aceitou e sumiu) e E3 (corrida) tratados. [auto] (F-05 E1-E4).

### Integrações
- **D-08:** OSRM (distância/ETA em rota) atrás de adapter (Stub de dev; fallback haversine ×1.4 com flag eta_degraded). Push (Web Push VAPID) atrás de adapter para notificar oferta/aceite. Ambos com Stub nos testes. [auto] (integracoes.md §6/§8, DRV-006 pattern).

### Claude's Discretion
- Mecânica exata do agendamento da cascata (arq job vs loop com Redis) — provável arq job orquestrando ofertas sequenciais com Redis TTL.
- Estrutura do estado da oferta em Redis (offer:{delivery_id} com TTL, lista de candidatos).
- App do entregador: como receber a oferta (push + polling de oferta ativa).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fluxo e regras
- `projeto/regras-negocio/fluxos.md` §F-05 (`:90-106`) — despacho e aceite + exceções E1-E4
- `projeto/regras-negocio/regras.md` — RN-003 (cobertura), RN-009 (cascata, nunca broadcast), RN-013 (privacidade destino), RN-014 (bloqueio privado), RN-004 (cobra só após aceite)
- `projeto/regras-negocio/entidades.md` §Lado da oferta (merchant_courier_favorites/_blocks), §Transacional (deliveries)
- `.planning/DECISIONS.md` — ADR-007 (cascata), ADR-104 (timer Redis TTL), ADR-013 (score sem peso no M1)

### Integrações
- `projeto/docs-externos/integracoes.md` §6 (Web Push VAPID), §8 (OSRM/ETA)

### UI
- `projeto/wireframes/05-entregador-oferta.html`, `04-entregador-home.html`, `15-loja-favoritos.html`
- Design system + componentes Phase 3-7 (apps/web)

### Backend a reusar
- Phase 7: máquina de estados (CRIADA→ACEITA), transition() com FOR UPDATE, deliveries
- Phase 6: elegibilidade espacial (cobertura), disponibilidade online/offline/busy, tabela de frete
- Phase 4: adapter pattern (OSRM/push como novos adapters + Stub)
- Redis (já no compose) para lock + TTL de oferta
- migrations 0002-0006

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-024 (cascata+locks), REQ-025 (privacidade destino RN-013), REQ-012 (favoritos/bloqueados), REQ-054 (OSRM/ETA)

### Segurança (Gate 4)
- `.claude/skills/standalone/owasp-security/SKILL.md` (concorrência, IDOR, autorização de oferta), `.claude/skills/mobile/push-notifications-architecture/SKILL.md`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 7 transition() + FOR UPDATE → base do aceite único (adicionar Redis lock por cima).
- Phase 6 elegibilidade espacial + disponibilidade → monta lista de elegíveis.
- Redis no compose → lock de aceite + TTL de oferta (ADR-104).
- Adapter pattern (Phase 4) → OSRM e push como novos adapters com Stub.
- arq worker (Phase 1) → job que orquestra a cascata sequencial.

### Established Patterns
- `/v1` API, AreaScoped, RFC-7807. aware UTC (TD-010) em timestamps de oferta/aceite. Mobile Ionic (app entregador).
- Push notifications: VAPID, degrade silencioso (Phase 5/9 pattern).

### Integration Points
- Consome cobertura+disponibilidade (Phase 6), deliveries CRIADA (Phase 7). Produz ACEITA pronto para execução (Phase 9). Notifica loja/destinatário (push). OSRM para ranking.
</code_context>

<specifics>
## Specific Ideas

- O **aceite único** é a peça mais crítica (corrida de rede): Redis lock + FOR UPDATE; o segundo aceite recebe "já aceita" sem penalidade (testar concorrência de verdade — @pytest.mark.mysql/Redis).
- **RN-013:** a oferta NUNCA expõe o endereço completo do destino (só bairro+distância) — vazamento aqui é falha de privacidade. A localização dos entregadores online NUNCA é exposta à loja (ADR-007).
- Redis TTL é fonte de verdade do timer (ADR-104) — o cronômetro do app é cosmético; não confiar no cliente.
- Nunca broadcast (RN-009) — cascata sequencial sempre.
- OSRM fora → fallback haversine ×1.4 com flag eta_degraded (não bloqueia despacho).
</specifics>

<deferred>
## Deferred Ideas

- Coleta/comprovação foto+GPS/entrega/tracking (ACEITA→COLETADA→ENTREGUE) — Phase 9.
- "Aceitou e sumiu" (2× ETA sem chegar) cancelamento — comportamento na Phase 9 (aqui só o aceite).
- Broadcast opt-in por entrega — pós-M1 (TD-011).
- Cobrança da corrida — Phase 10/11.
- Score com peso no ranking — v1.1 (ADR-013; M1 score sem peso).
</deferred>

---

*Phase: 08-despacho-em-cascata-oferta-aceite*
*Context gathered: 2026-06-10*
