# Phase 7: Criação de entrega + máquina de estados (modalidade direta) - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega o fluxo F-03 de criação de entrega pela loja (manual) e a **máquina de estados** canônica da entrega — coração transacional do sistema. A loja preenche coleta (pré-preenchida com a loja), entrega (CEP/autocomplete → bairro do catálogo da Phase 6), destinatário (nome/telefone), itens, método de comprovação (foto default; OTP desabilitado "em breve"), e escolhe a forma de pagamento — **nesta phase só a modalidade DIRETA** (cartão/PIX via Safe2Pay é Phase 10). O sistema calcula estimativa de frete (mediana das tabelas elegíveis — RN-030), valida o limite do plano (RN-028) e cria a entrega no estado `CRIADA`. Inclui as entidades `deliveries`, `delivery_state_transitions` (append-only, trigger), `recipients`, e a **máquina de 7 estados** (RN-019: CRIADA, ACEITA, COLETADA, ENTREGUE, RECUSADA_NO_DESTINO, CANCELADA, FINALIZADA) com transições válidas apenas via máquina, sempre logadas (RN-012). **Não** entrega despacho/oferta/aceite (Phase 8 — a entrega nasce CRIADA e fica aguardando), nem comprovação/execução (Phase 9), nem cobrança online (Phase 10).
</domain>

<decisions>
## Implementation Decisions

### Criação de entrega (F-03)
- **D-01:** Form de nova entrega (tela 12): coleta (pré-preenchida com a loja, editável), entrega (CEP/autocomplete → bairro do catálogo Phase 6), destinatário (nome, telefone E.164), itens (descrição, qtd, valor declarado opcional), observações, método de comprovação (foto default; foto+referência; OTP selecionável mas DESABILITADO badge "em breve"). [auto] (F-03 passos 1-3).
- **D-02:** Forma de pagamento da corrida POR ENTREGA (RN-023): nesta phase só **direto ao entregador** habilitado; cartão/PIX selecionáveis mas marcados "em breve" (Phase 10). No direto, a entrega nasce sem cobrança online; a taxa de plataforma acumula na fatura mensal (fatura é Phase 11). [auto] (RN-023/RN-024, escopo).

### Máquina de estados (RN-019) — coração do sistema
- **D-03:** Exatamente 7 estados (CRIADA, ACEITA, COLETADA, ENTREGUE, RECUSADA_NO_DESTINO, CANCELADA, FINALIZADA). Transições SÓ via máquina de estados explícita; transição inválida → erro (422). Novo estado exigiria ADR. Nesta phase a entrega só chega a CRIADA (e CANCELADA pela loja antes do aceite); ACEITA+ vêm nas Phases 8/9, mas a MÁQUINA inteira é definida aqui. [auto] travado por RN-019/DRV-001.
- **D-04:** `delivery_state_transitions` append-only (INSERT-only via TRIGGER MySQL como audit_log — RN-012), com timestamp, ator, motivo, GPS quando houver, IP. Trigger nega UPDATE/DELETE (mesmo padrão da migration 0002). [auto] travado por RN-012.

### Estimativa de frete (RN-030)
- **D-05:** Estimativa mostrada à loja antes de confirmar = MEDIANA das tabelas dos entregadores online elegíveis para o trecho (cobertura coleta E entrega — Phase 6). Valor final = tabela do entregador que aceitar (Phase 8), nunca acima do teto exibido +10% (senão re-confirma). `[ASSUMIDO]` — implementar simples. [auto] (RN-030, TD-009 já registrada).
- **D-06:** Exceção: nenhum entregador online cobre origem E destino (F-03 E2) → criação permitida com aviso "0 entregadores disponíveis agora"; loja decide criar ou cancelar. Endereço fora da área (E1) → "fora da cobertura" + captura de interesse. [auto].

### Limite de plano (RN-028)
- **D-07:** Loja no limite do plano (Free 2/mês, contador zera dia 1º) → 3ª entrega bloqueada com modal de upgrade (sem dark pattern, "agora não" visível). Contador de uso em merchant_subscriptions (Phase 4). Fatura vencida >7 dias bloquearia criação (RN-025) — mas fatura é Phase 11; aqui deixar o gancho. [auto] (F-03 E4, RN-028).

### Destinatário
- **D-08:** `recipients` — identidade separada do endereço (nome, telefone, email opcional); hash de CPF para antifraude (nunca CPF puro). Contadores de entregas/recusas. [LGPD]. [auto] (entidades recipients).

### Claude's Discretion
- Biblioteca/abordagem da máquina de estados (enum + tabela de transições válidas vs lib).
- Estrutura exata de deliveries (muitos campos — ver entidades.md).
- Como calcular elegíveis para a mediana (reuso da elegibilidade espacial da Phase 6).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fluxo e regras
- `projeto/regras-negocio/fluxos.md` §F-03 (`:51-69`) — criação de entrega + exceções E1-E5
- `projeto/regras-negocio/regras.md` — RN-019 (7 estados), RN-012 (append-only), RN-023 (forma de pagamento), RN-028 (Free 2/mês), RN-030 (estimativa mediana), RN-013 (privacidade destino — relevante na Phase 8)
- `projeto/regras-negocio/entidades.md` §Transacional (deliveries, delivery_state_transitions, recipients)
- `.planning/DECISIONS.md` — DRV-001 (7 estados), ADR-012 (pagamento direto 1ª classe)

### UI
- `projeto/wireframes/12-loja-nova-entrega.html`, `11-loja-dashboard.html`, `14-loja-entregas.html`
- Design system + componentes Phase 3/4/5/6 (apps/web)

### Backend a reusar
- Phase 2: máquina append-only (trigger audit_log → replicar p/ delivery_state_transitions), AreaScoped, máscaras PII
- Phase 4: merchants/merchant_subscriptions (limite de plano, contador de uso)
- Phase 6: elegibilidade espacial (cobertura coleta E entrega), catálogo de bairros, tabela de frete dos entregadores
- migrations 0002-0005 (convenções, trigger pattern)

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-021 (F-03), REQ-022 (7 estados append-only), REQ-023 (estimativa), REQ-011 (parcial — limite plano)

### Segurança (Gate 4)
- `.claude/skills/standalone/owasp-security/SKILL.md` (api-input-validation, máquina de estados segura), `.claude/skills/br/lgpd-compliance/SKILL.md` (PII destinatário)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 2 trigger append-only (audit_log) → replicar para delivery_state_transitions na migration 0006.
- Phase 6 elegibilidade espacial (point_in_polygon, cobertura) → usar para achar entregadores elegíveis e calcular mediana de frete.
- Phase 4 merchant_subscriptions (contador de uso, limite de plano).
- Design system + forms BR + data-tables (lista de entregas tela 14).

### Established Patterns
- `/v1` API, RFC-7807, AreaScoped, idempotência. aware UTC (TD-010) em todos os timestamps de transição. PII (telefone destinatário) fora de log, mascarado.
- Máquina de estados: enum + conjunto de transições válidas; transição inválida → 422 (padrão das Phases 5/6).

### Integration Points
- deliveries vincula area + merchant + (entregador nullable até aceite) + recipient. Estimativa usa elegibilidade da Phase 6. A entrega CRIADA fica pronta para o DESPACHO (Phase 8) consumir. delivery_state_transitions é a fonte de verdade do histórico.
</code_context>

<specifics>
## Specific Ideas

- A máquina de estados é a peça mais crítica: definir TODAS as transições válidas e testar exaustivamente as inválidas (RN-019) — mesmo as que só serão exercidas nas Phases 8/9.
- delivery_state_transitions é imutável (trigger) — nunca UPDATE/DELETE; é o que dá auditabilidade e antifraude.
- Pagamento direto: a entrega nasce sem cobrança online; a confirmação de recebimento do entregador é na conclusão (Phase 9); a fatura mensal de taxas é Phase 11.
- Estimativa = mediana simples (TD-009, [ASSUMIDO]) — não over-engineerar.
</specifics>

<deferred>
## Deferred Ideas

- Despacho/oferta/aceite/cascata (entrega CRIADA → ACEITA) — Phase 8.
- Comprovação foto+GPS, COLETADA→ENTREGUE→FINALIZADA, confirmação de pagamento direto, tracking — Phase 9.
- Cobrança online cartão/PIX (Safe2Pay split) — Phase 10.
- Fatura mensal de taxas + bloqueio por fatura vencida (RN-025) — Phase 11.
- OTP de comprovação (RN-007) — pós-M1 (TD-003).
</deferred>

---

*Phase: 07-cria-o-de-entrega-m-quina-de-estados-modalidade-direta*
*Context gathered: 2026-06-10*
