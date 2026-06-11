# Phase 10: Safe2Pay núcleo — assinaturas, cobrança com split, escrow, estornos - Context

**Gathered:** 2026-06-11 (modo --auto; OQ-3 resolvida como SUPOSIÇÃO DOCUMENTADA — DEC-003)
**Status:** Ready for planning
**⚠ Sensível: dinheiro real. Lei do projeto: `docs/SAAS-BILLING-DOCS.md` (CLAUDE.md §18) + skill `domain/safe2pay-escrow-br` (obrigatória) + `domain/saas-billing-canonical`.**

<domain>
## Phase Boundary

Entrega o núcleo de pagamento online via Safe2Pay (ADR-009 v2): (a) **assinatura recorrente da loja** (cartão tokenizado / PIX automático), (b) **cobrança por entrega cartão/PIX com SPLIT** para a subconta do entregador (corrida → subconta entregador em escrow; taxa → conta Jaxegô + revenue share da área), (c) **escrow interno de 24h** pós-FINALIZADA antes de liberar a corrida no saldo do entregador, (d) **estornos** (cancelamento pré-aceite total; parcial RN-004), (e) **subconta do entregador** cadastrada quando MEI aprovado (RN-010). Toda a integração nasce com `[ASSUMIDO]` (DEC-003) atrás de **interface própria** (trocar de PSP/ajustar escrow não pode doer — ADR-009 v2). **Não** entrega fatura mensal de taxas do pagamento direto (Phase 11), disputas/saques (Phase 11), governança/revenue-share-relatório (Phase 13). Aqui: assinatura + cobrança split + escrow + estorno + webhooks Safe2Pay.
</domain>

<decisions>
## Implementation Decisions

### Suposições DEC-003 (OQ-3) — REVISAR quando o contrato Safe2Pay confirmar
- **D-01:** `[ASSUMIDO]` split/marketplace DISPONÍVEL no plano contratado. `[ASSUMIDO]` escrow interno 24h pós-FINALIZADA MANTIDO independente do prazo de repasse do PSP. `[ASSUMIDO]` taxa por transação parametrizável (seed/config, nunca hardcoded). Tudo atrás de interface própria. [auto] DEC-003.

### Padrões da lei de billing (SAAS-BILLING-DOCS — adaptar NestJS→FastAPI)
- **D-02:** **Criptografia (não muda):** token de cartão Safe2Pay em **AES-256-GCM** (`base64(iv12+tag16+ciphertext)`, chave `SAFE2PAY_TOKEN_ENCRYPT_KEY` 32 bytes hex); dados de cartão do frontend em **RSA-OAEP 2048** (frontend cifra com chave pública, backend decifra com privada — cartão NUNCA em texto puro nem em log). Endpoint GET de chave pública RSA. [auto] travado (SAAS-BILLING §4/§13).
- **D-03:** **Assinatura recorrente da loja:** cartão tokenizado (sandbox cobra raw; produção tokeniza→cobra com token) + PIX automático (autorização v3 + agendamento + webhooks). Estados: trial/active/blocked/cancelado. Cron diário de cobrança. Inadimplência: >10 dias → blocked, >20 dias → cancelado. Guard de assinatura ativa. [auto] (SAAS-BILLING §5-10).
- **D-04:** **Webhooks Safe2Pay** (sem auth, idempotentes por IdTransaction, logar payload em webhook_logs antes de processar, responder 200 <5s, trabalho pesado em fila arq). Validar assinatura/token do header. [auto] (SAAS-BILLING §8, integracoes.md §1).

### Split + escrow por entrega (skill safe2pay-escrow-br — NÃO está na SAAS-BILLING genérica)
- **D-05:** Cobrança por entrega cartão/PIX na CRIAÇÃO (F-03, mas modalidade cartão/PIX que estava "em breve" na Phase 7 agora ativa): `Amount = corrida + taxa`; **Split**: subconta_entregador ← corrida; conta_jaxego ← taxa (+ revenue share da área, `[DECIDIR]` OQ-1 default 20%). Recusa na criação → entrega NÃO nasce (F-03 E3, já previsto na Phase 7). [auto] (integracoes.md §1, ADR-009 v2).
- **D-06:** **Escrow interno 24h:** corrida retida em escrow após cobrança; FINALIZADA (Phase 9) + 24h sem disputa → libera no saldo sacável do entregador (saque é Phase 11). Tabela `platform_charges` (assinatura, corrida+taxa, item fatura, excedente SMS) com idempotency key + IdTransaction. [auto] (RN-006, F-07, entidades platform_charges).
- **D-07:** **Subconta do entregador:** cadastrada como recebedor/subconta Safe2Pay quando o MEI é aprovado no KYC (Phase 5 — gancho `mei_pending`/MEI ativo). Sem MEI → sem subconta → sem repasse via plataforma (RN-010; o direto da Phase 7-9 continua). [auto] (integracoes.md §1, RN-010).
- **D-08:** **Estornos:** cancelamento pré-aceite → estorno total automático; parcial conforme RN-004 (50%/100%+retorno) com estorno do excedente em até 5 dias úteis. Conciliação diária contra extrato Safe2Pay (diferença >R$0,01 → alerta admin plataforma). [auto] (integracoes.md §1, RN-004, F-07 E1).

### Interface própria (ADR-009 v2)
- **D-09:** Safe2Pay atrás de Protocol/adapter (`PaymentPort`) + impl httpx + **Stub de dev/teste** (NUNCA chamar API real nos testes; sandbox documentado). Trocar de PSP ou ajustar escrow = trocar impl, não o domínio. [auto] travado por ADR-009 v2.

### Claude's Discretion
- Lib de cripto Python (cryptography — AES-GCM + RSA-OAEP; já presente desde Phase 1).
- Estrutura de platform_charges/merchant_subscriptions (estende Phase 4) e escrow ledger.
- Mecânica do cron de cobrança (arq) e conciliação.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Lei de billing (OBRIGATÓRIO)
- `docs/SAAS-BILLING-DOCS.md` — mecânica canônica (cripto AES-256-GCM/RSA-OAEP, endpoints Safe2Pay, cron, webhooks, inadimplência 10/20d, guard). **Adaptar NestJS→FastAPI/SQLAlchemy, mas a mecânica não muda.**
- `.claude/skills/domain/safe2pay-escrow-br/SKILL.md` (546 linhas — OBRIGATÓRIA) — split/marketplace + escrow por entrega (o que a SAAS-BILLING genérica não cobre)
- `.claude/skills/domain/saas-billing-canonical/SKILL.md` (se existir) — obrigatória billing
- CLAUDE.md §18 — billing é lei; sem inventar lógica

### Decisões
- `.planning/DECISIONS.md` — ADR-009 v2 (Safe2Pay, interface própria), **DEC-003 (OQ-3 suposições)**, ADR-012 (pagamento direto — coexiste)
- OQ-1 (revenue share admin de área — `[DECIDIR]`, default 20% assumido)

### Fluxo e regras
- `projeto/docs-externos/integracoes.md` §1 (Safe2Pay split/escrow/webhooks — CRÍTICA)
- `projeto/regras-negocio/fluxos.md` §F-03 (criação cartão/PIX), §F-07 (pagamento da corrida e taxas)
- `projeto/regras-negocio/regras.md` — RN-004 (cancelamento/estorno), RN-006 (escrow 24h), RN-010 (MEI p/ repasse), RN-029 (upgrade pro-rata/downgrade)
- `projeto/regras-negocio/entidades.md` §Financeiro (platform_charges), §Lado da demanda (merchant_subscriptions — Phase 4)

### UI
- `projeto/wireframes/16-loja-plano.html` (checkout/assinatura), `12-loja-nova-entrega.html` (pagamento cartão/PIX agora ativo)
- Design system + jx-plan-card/componentes Phase 3-9

### Backend a reusar
- Phase 4: merchant_subscriptions, subscription_plans (seeds), máquina de estados merchant, adapter pattern, SSRF guard
- Phase 7: deliveries com payment_method (card/pix/direct — card/pix estavam "em breve", agora ativos), criação F-03
- Phase 9: FINALIZADA (gatilho do escrow 24h)
- Phase 1: cryptography lib, config por env, arq worker

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-010 (assinatura recorrente), REQ-011 (upgrade pro-rata/downgrade), REQ-034 (cobrança com split), REQ-036 (escrow 24h), REQ-019 completo (subconta entregador), REQ-029 financeiro (estornos)

### Segurança (Gate 4 — CRÍTICO, é dinheiro)
- `.claude/skills/standalone/owasp-security/SKILL.md` (auth-and-session, idempotência, webhooks HMAC, cripto, PCI-adjacent); `.claude/skills/br/lgpd-compliance/SKILL.md`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 4 merchant_subscriptions/subscription_plans + adapter pattern (Receita/SMS) → PaymentPort no mesmo padrão.
- Phase 1 cryptography (já instalada) → AES-256-GCM + RSA-OAEP.
- Phase 7 deliveries.payment_method ENUM(card/pix/direct) — card/pix estavam selecionáveis "em breve"; agora o caminho cartão/PIX cria cobrança+split.
- Phase 9 FINALIZADA → gatilho do escrow 24h (job arq).
- Phase 5 KYC MEI aprovado → gancho para cadastrar subconta Safe2Pay.

### Established Patterns
- adapter+Stub, aware UTC (TD-010), PII/segredos fora de log (cartão/token/api-key NUNCA em log), idempotência por header/IdTransaction, RFC-7807.
- Money em centavos inteiros (Phase 7) — NÃO float.

### Integration Points
- Cobrança split na criação de entrega cartão/PIX (Phase 7 reaberto p/ card/pix). Escrow alimenta saldo (saque Phase 11). Subconta vem do MEI (Phase 5). Webhooks Safe2Pay processam status. Conciliação diária.
</code_context>

<specifics>
## Specific Ideas

- **É DINHEIRO REAL.** Idempotência em TODA escrita de cobrança (IdTransaction/idempotency key). Cartão/CVV/token NUNCA em log nem em texto puro (AES-256-GCM + RSA-OAEP). Webhooks idempotentes. Conciliação diária contra extrato.
- **DEC-003:** tudo `[ASSUMIDO]` atrás de interface própria — split/prazo/taxa parametrizados; revisar com contrato real. Escrow interno 24h independente do PSP.
- Sandbox vs produção: token não funciona em sandbox; cobrança recorrente com token só em produção (SAAS-BILLING §13). Stub nos testes.
- Coexistência: pagamento direto (Phase 7-9) continua; cartão/PIX é a adição. A taxa de plataforma incide nas três modalidades (RN-023).
- Money em centavos inteiros (consistente com Phase 7), nunca float.
</specifics>

<deferred>
## Deferred Ideas

- Fatura mensal de taxas do pagamento direto + bloqueio por fatura vencida (RN-025) — Phase 11.
- Disputas (mediação) + saques (payouts) — Phase 11.
- Relatório de revenue share do admin de área — Phase 13.
- Confirmação do contrato Safe2Pay (split/prazo/taxa reais) → ADR que supera DEC-003.
</deferred>

---

*Phase: 10-safe2pay-n-cleo-assinaturas-cobran-a-com-split-escrow-estornos*
*Context gathered: 2026-06-11*
