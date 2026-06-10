# Phase 4: Cadastro e ativação de loja - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega o fluxo F-01 completo: o dono de um estabelecimento se cadastra (CNPJ/CPF, nome fantasia, categoria, telefone, e-mail, senha), o sistema valida CNPJ na Receita, confirma e-mail (link) e telefone (SMS), geocodifica o endereço e vincula a loja à **área** correspondente (Pádua no piloto), e o dono escolhe um plano (Free pré-selecionado). Cobre as 4 exceções (E1–E4): CNPJ inativo, colisão de dados (anti-enumeração), pagamento de assinatura falha → Free, Receita fora do ar → pending_validation. Inclui as entidades `merchants`, `merchant_users`, `subscription_plans` (seeds), `merchant_subscriptions`, e o **seed da área Pádua + planos + admin**. **Não** entrega checkout pago real via Safe2Pay (Phase 10 — aqui só o caminho Free e o estado pending_payment), nem cadastro de entregador (Phase 5), nem criação de entregas (Phase 7).
</domain>

<decisions>
## Implementation Decisions

### Fluxo de cadastro (F-01)
- **D-01:** Wizard de cadastro: dados da conta (CNPJ ou CPF p/ autônomo, nome fantasia, categoria, telefone E.164, e-mail, senha argon2id) → confirmação e-mail (link) + telefone (SMS OTP) → endereço (geocodifica → vincula à área) → escolha de plano (Free pré-selecionado). [auto] (F-01 passos 1-7).
- **D-02:** Anti-duplicidade (RN-011): CNPJ/CPF + telefone + e-mail únicos por tipo de conta. Colisão → mensagem anti-enumeração ("Já existe conta com esse dado. Recuperar acesso?") sem dizer QUAL dado colidiu além do informado. [auto] travado por RN-011 / F-01 E2.

### Validação Receita Federal
- **D-03:** CNPJ validado na Receita (situação ativa) antes de ativar loja. Provider: minhareceita.org self-hosted primário + BrasilAPI fallback (DRV-006), atrás de uma interface/adapter própria. Em DEV/teste: adapter stub configurável (não chamar API real nos testes). [auto] (RN-011, integracoes.md §3).
- **D-04:** Exceções: CNPJ inativo/inexistente (E1) → bloqueia com mensagem clara + suporte. Receita fora do ar (E4) → cadastro segue `pending_validation`, loja usa Free com limite, revalidação por job (retry 6/6/12/24h). [auto] travado.

### Estados da loja
- **D-05:** Status do merchant: `pending_payment` (assinatura paga falhou → usa Free), `pending_validation` (Receita indisponível), `active`, `suspended`. Geocodificação sem área cobrindo → tela "Ainda não chegamos aí" + captura de interesse (e-mail+cidade) [estado vazio obrigatório]. [auto] (F-01 E3/passo 5, entidades merchants).

### Planos e assinatura (parte Free)
- **D-06:** Seeds de `subscription_plans`: Free (R$0, 2 entregas/mês, taxa R$2,00), Início, Profissional, Sem Limite — valores `[ASSUMIDO]` implementados como SEEDS EDITÁVEIS (DRV-009), NUNCA hardcoded. Plano Free é seed imutável. [auto] travado por DRV-009.
- **D-07:** Nesta phase, só o caminho Free é ativável de fato (cria `merchant_subscriptions` Free ativo). Plano pago → cria merchant em `pending_payment` e mostra aviso persistente; o checkout Safe2Pay real é a Phase 10. [auto] (escopo — Safe2Pay é MS-04).

### Integrações de notificação
- **D-08:** Confirmação de telefone via SMS OTP (Zenvia primário + Twilio fallback, DRV-007) atrás de adapter; confirmação de e-mail via AWS SES (link). Em DEV/teste: adapters stub (log/captura, sem envio real). Quota de SMS por plano. [auto] (integracoes.md §4/§5).

### Seed de bootstrap (pré-requisito)
- **D-09:** Seed inicial: área **Pádua** (codename `padua`, nível KYC, piso, geofence default), os 4 planos, e um **admin de plataforma** + **admin de área** de bootstrap (via comando CLI/script de seed, idempotente). Necessário para a loja se vincular a uma área e para os fluxos de aprovação seguintes. [auto] recomendado (lacuna identificada no fechamento do MS-01).

### Claude's Discretion
- Geocoding provider (Nominatim/OSM ou similar) atrás de adapter.
- Estrutura do wizard no frontend (stepper) e persistência de progresso parcial.
- Formato exato dos seeds (script Python `seed.py` vs migration de dados).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fluxo e regras
- `projeto/regras-negocio/fluxos.md` §F-01 (`:7-24`) — cadastro de loja, passos + exceções E1-E4
- `projeto/regras-negocio/regras.md` — RN-011 (anti-duplicidade), RN-021 (LGPD), RN-028 (Free 2/mês)
- `projeto/regras-negocio/entidades.md` §Lado da demanda (merchants, merchant_users, subscription_plans, merchant_subscriptions)

### Integrações
- `projeto/docs-externos/integracoes.md` §3 Receita Federal, §4 SMS, §5 SES
- `.planning/DECISIONS.md` — DRV-006 (Receita provider), DRV-007 (SMS), DRV-009 (planos como seeds)

### UI
- `projeto/wireframes/02-cadastro-loja.html`, `16-loja-plano.html`
- `docs/identidade-visual/tokens.json` + design system da Phase 3 (apps/web)

### Backend a reusar (Phase 2)
- `apps/api/app/auth/` (argon2id, users), `apps/api/app/areas/` (entidade Área + escopo), `apps/api/app/db/` (AreaScoped mixin, repository)

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-008 (F-01), REQ-009 (seeds de planos), REQ-006 (anti-duplicidade aplicada)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 2: users + argon2id + área + AreaScoped + audit_log; Phase 3: design system + componentes de estado + forms base + login.
- Adapters de integração: criar interface comum (Receita, SMS, SES, geocoding) com impl real + stub de dev.

### Established Patterns
- `/v1` API, RFC-7807 errors, idempotência por header. PII fora de log (CNPJ/CPF mascarados). área via escopo.
- Forms BR: validação de CNPJ/CPF (dígito + formato) no front e no back.

### Integration Points
- merchant vincula a `areas` (Phase 2). subscription a `subscription_plans` (seed). Notificações via adapters. Gate 5 (integration-checker) valida contratos Receita/SMS/SES (stubs no teste).
</code_context>

<specifics>
## Specific Ideas

- Anti-enumeração na colisão de cadastro (RN-011 / F-01 E2): nunca revelar QUAL dado colide.
- Valores de planos/taxas são `[ASSUMIDO]` → SEEDS editáveis, nunca constantes em código (DRV-009).
- Estado vazio "Ainda não chegamos aí" (endereço fora de área) é obrigatório com captura de interesse.
- Resiliência: Receita/SMS fora do ar NÃO bloqueiam o cadastro (pending_validation + Free + retry).
</specifics>

<deferred>
## Deferred Ideas

- Checkout pago real via Safe2Pay (cartão/PIX recorrente) — Phase 10.
- Cadastro/KYC de entregador — Phase 5.
- Criação de entregas — Phase 7.
- Limite de plano enforçado na criação de entrega (RN-028) — Phase 7 (aqui só o seed do limite).
</deferred>

---

*Phase: 04-cadastro-e-ativa-o-de-loja*
*Context gathered: 2026-06-10*
