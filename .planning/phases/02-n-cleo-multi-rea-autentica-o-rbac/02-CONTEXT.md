# Phase 2: Núcleo multi-área + autenticação + RBAC - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas — maioria já travada por ADR)
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega o núcleo de identidade e isolamento da plataforma: entidade **Área** (`areas`), entidade **User** global, autenticação (JWT access + refresh opaco, argon2id, TOTP), RBAC dos 6 papéis, middleware de escopo de área (`area_id` em tudo — ADR-001/RN-001), e infraestrutura append-only (audit_log + trigger negando UPDATE/DELETE). **Não** entrega cadastro de loja/entregador (Phase 4/5), nenhuma UI (has_ui:false — login UI vem na Phase 3), nem regras de negócio de entrega. Apenas a fundação de auth + multi-área sobre a qual todas as outras phases assentam.
</domain>

<decisions>
## Implementation Decisions

### Autenticação (ADR-005 — travada)
- **D-01:** JWT **HS256**, access token de **15 min** (stateless, em memória no cliente). Refresh token **opaco** persistido em DB (não-JWT), rotacionável. Web: refresh em cookie httpOnly+Secure; app: Secure Storage. [auto] travado por ADR-005.
- **D-02:** Hash de senha com **argon2id** (parâmetros recomendados OWASP). Nunca bcrypt. [auto] travado.
- **D-03:** **TOTP** obrigatório para admin de plataforma; disponível (opt-in) para os demais papéis. [auto] travado.
- **D-04:** Lockout de **5 tentativas / 15 min** por conta; resposta 423/429. Anti-enumeração: mensagens de erro que não revelam se e-mail existe. [auto] travado por ADR-005 + RN-011.

### Multi-área e isolamento (ADR-001 / RN-001 — travada)
- **D-05:** `area_id` obrigatório em TODA tabela de domínio; tabelas globais são exatamente `users`, `audit_log`, `ai_usage_log`. [auto] travado.
- **D-06:** Middleware injeta o escopo de área do token; toda query de domínio filtra por área. Admin de plataforma pode bypassar com **flag auditada**. Acesso cross-área de admin de área → **403**. [auto] travado por ADR-001/RN-001 + F-08 E1.
- **D-07:** Teste de isolamento obrigatório: seed de 2+ áreas, query cross-área deve retornar 403/vazio. É critério de aceite da phase. [auto] (ROADMAP verificação).

### RBAC (6 papéis)
- **D-08:** Papéis: admin_plataforma, admin_area (owner/manager/viewer), loja_dono, loja_operador, entregador, destinatário(sem login). Vínculos via tabelas de associação (area_admins, merchant_users, etc. — schema completo nas phases que criam as entidades; aqui só users + areas + area_admins para fechar auth/RBAC). Permissões por papel checadas em dependency do FastAPI. [auto] recomendado (visao-geral.md papéis).
- **D-09:** Um mesmo `user` pode ter múltiplos vínculos (dono de loja numa área, entregador em outra) — RBAC resolve papel por contexto de área. [auto] (entidades.md relações).

### Append-only / auditoria (RN-012 — travada)
- **D-10:** `audit_log` e tabelas de transição são **INSERT-only via trigger** MySQL que nega UPDATE/DELETE. Teste: UPDATE em audit_log → erro MySQL (critério de aceite). [auto] travado por RN-012.
- **D-11:** Ações administrativas sensíveis gravam before/after no audit_log com ator, timestamp, IP. [auto] travado.

### LGPD (RN-021)
- **D-12:** PII de `users` (email, telefone, CPF, nome) marcada; CPF mascarado em telas que não exigem o dado completo; PII nunca em log de aplicação (já enforced pela config de observabilidade da Phase 1). Hooks de anonimização (exclusão→30d) ficam como schema/flags aqui; jobs efetivos na Phase 14. [auto] travado por RN-021.

### Claude's Discretion
- Estrutura interna dos módulos (`app/auth/`, `app/areas/`, `app/core/security.py`).
- Biblioteca TOTP (ex.: `pyotp`) e de JWT (ex.: `pyjwt` / `python-jose`) — escolher na pesquisa de segurança.
- Formato exato do payload do JWT (claims: sub, area_scope, role, exp, jti).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Auth e segurança
- `.planning/DECISIONS.md` — ADR-005 (auth completa), ADR-001 (multi-área)
- `.claude/skills/standalone/owasp-security/SKILL.md` — fonte do gate 4 / Security Baseline (auth-and-session, api-input-validation)
- `projeto/regras-negocio/regras.md` — RN-001 (escopo área), RN-011 (anti-duplicidade), RN-012 (append-only), RN-021 (LGPD), RN-022 (janela de telefones)

### Entidades
- `projeto/regras-negocio/entidades.md` §Núcleo multi-área (areas, area_admins, users)
- `.planning/REQUIREMENTS.md` — REQ-001, REQ-002, REQ-004, REQ-005, REQ-006, REQ-007

### Papéis
- `projeto/regras-negocio/visao-geral.md` §Papéis e permissões
- `projeto/regras-negocio/fluxos.md` F-08 (admin de área, escopo, 403 cross-área)

### Convenções herdadas (Phase 1)
- `.planning/phases/01-funda-o-t-cnica-repo-infra-api-skeleton/01-CONTEXT.md` — DRV-002/003, naive datetime guard (TD-010)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (da Phase 1)
- `app/main.py` app factory + middleware de request_id/observabilidade — auth middleware se encaixa aqui.
- `app/db/` sessão async SQLAlchemy + Alembic configurado — primeiras migrations reais (areas, users, area_admins, audit_log + trigger) entram aqui.
- Guard de naive datetime ativo — usar datetimes aware (UTC) em tokens/expiração (atenção a `exp`, lockout windows).

### Established Patterns
- `/v1` prefix para API de negócio; `/health` na raiz. Auth endpoints sob `/v1/auth/*`.
- Logs JSON com `user_id` — preencher o campo quando autenticado, sem vazar PII.

### Integration Points
- Toda phase futura consome o middleware de escopo de área e as dependencies de RBAC criadas aqui.
</code_context>

<specifics>
## Specific Ideas

- Lockout windows e `exp` do JWT são datetimes — risco direto de naive datetime (TD-010); usar sempre `datetime.now(UTC)`.
- Anti-enumeração de conta (RN-011 / F-01 E2): nunca revelar QUAL dado colide.
- O bypass do admin de plataforma sobre o escopo de área TEM que ser auditado (audit_log) — não pode ser silencioso (RN-001).
</specifics>

<deferred>
## Deferred Ideas

- Cadastro/onboarding de loja (F-01) — Phase 4.
- Cadastro/KYC de entregador (F-02) — Phase 5.
- UI de login (tela 01) — Phase 3 (shell + design system).
- Jobs de anonimização LGPD efetivos — Phase 14.
- Entidades de domínio (merchants, couriers, deliveries) — phases respectivas.
</deferred>

---

*Phase: 02-n-cleo-multi-rea-autentica-o-rbac*
*Context gathered: 2026-06-10*
