# Phase 5: Cadastro do entregador + KYC 2 níveis + documentos B2 - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Entrega o fluxo F-02 de cadastro e validação de entregador: wizard (dados pessoais com CPF, selfie com documento, veículo, e — se a área exigir COMPLETA — CNH com EAR + CRLV + MEI + antecedentes), upload de documentos para **Backblaze B2** (bucket privado, URL pré-assinada, hash SHA-256, compressão), validação de MEI na Receita (CNAEs compatíveis), e a **fila de revisão do admin de área** que aprova/reprova **item a item** com motivo (ADR-011, 2 níveis). Inclui as entidades `couriers`, `courier_documents`, a flag `mei_pending` (RN-024). **Não** entrega cobertura/tabela de frete (etapa 7 do F-02 → Phase 6), nem ofertas/despacho (Phase 8), nem saques (Phase 11). Cobertura e preços são Phase 6.
</domain>

<decisions>
## Implementation Decisions

### Wizard de cadastro do entregador (F-02 etapas 1-6)
- **D-01:** Wizard: (1) dados — nome, CPF, nascimento, telefone E.164, email, senha argon2id; valida CPF (dígito+situação), confirma telefone (SMS OTP) e email (link); (2) selfie com documento (foto rosto+CPF/CNH) → B2; (3) veículo (moto/bici/carro/a pé, placa se motorizado). Se área exige COMPLETA: (4) CNH com EAR + CRLV + MEI (consulta automática situação+CNAEs) + antecedentes (se área exigir). Progresso parcial salvo, retomada por 30 dias, lembretes dia 3/7. [auto] (F-02 passos 1-6, E1).
- **D-02:** Entregador escolhe a ÁREA onde vai atuar (lista de áreas ativas). Mesmo CPF pode ter cadastro de entregador em VÁRIAS áreas (novo vínculo por área); CPF já cadastrado na MESMA área → bloqueia. [auto] (F-02 passo 2, E2).

### KYC 2 níveis (ADR-011)
- **D-03:** Dois níveis: SIMPLES (CPF validado + selfie + telefone + email confirmados) e COMPLETA (simples + CNH EAR + CRLV + MEI ativo + antecedentes se área exigir). A área configura o nível mínimo exigido. Nunca menos que simples (RN-002). [auto] travado por ADR-011/RN-002.
- **D-04:** Aprovação **item a item** pelo admin de área (selfie ok? CNH ok?). Status por item: pending/approved/rejected(+motivo). Reprovação de item → notificação com motivo específico + reenvio só daquele item (não refaz o resto). Admin não revisa em 48h → escalação (notifica admin área + visibilidade admin plataforma). [auto] (F-02 passos 8-9, E4, E5).

### Documentos e Backblaze B2 (ADR-004)
- **D-05:** Documentos (selfie, CNH, CRLV, MEI, antecedentes) em bucket B2 **privado** (`jaxego-kyc-prod`), upload por **URL pré-assinada** direto do cliente, compressão server-side (máx 1920px, WebP), **hash SHA-256** registrado, expiração monitorada por job (CNH/CRLV/MEI). Acesso só via URL assinada de expiração curta. [auto] travado por ADR-004, integracoes.md §7, entidades courier_documents.
- **D-06:** Adapter de storage (Protocol + impl B2/S3-compatible + Stub de dev) — testes não tocam B2 real. [auto] (padrão da Phase 4).

### MEI e RN-024
- **D-07:** MEI consultado na Receita (situação + CNAEs compatíveis: 4930-2/01, 4930-2/02, 5320-2/02, 5229-0/99). MEI inexistente/inativo na validação completa → cadastro segue com flag `mei_pending`: pode trabalhar APENAS em entregas de pagamento DIRETO (RN-024); banner permanente de regularização. [auto] travado por RN-024 / F-02 E3. (O bloqueio de repasse via plataforma por falta de MEI — RN-010 — é Phase 10/11.)

### Status do entregador
- **D-08:** couriers.status: pending_kyc / active / suspended / banned. Só fica `active` com validação mínima da área completa (RN-002). Vínculo user↔área (couriers tem area_id). [auto] (entidades couriers).

### Claude's Discretion
- Lib de compressão de imagem (Pillow) e geração de presigned URL (boto3 contra B2 S3 endpoint, ou SDK B2).
- Estrutura do wizard mobile (Ionic) e do painel de revisão do admin (tela 19).
- Detalhe do job de expiração de documentos.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fluxo e regras
- `projeto/regras-negocio/fluxos.md` §F-02 (`:27-48`) — cadastro entregador, etapas + exceções E1-E5
- `projeto/regras-negocio/regras.md` — RN-002 (2 níveis), RN-024 (sem MEI no direto), RN-021 (LGPD), RN-016 (suspensão/recurso)
- `projeto/regras-negocio/entidades.md` §Lado da oferta (couriers, courier_documents)
- `.planning/DECISIONS.md` — ADR-011 (2 níveis), ADR-004 (B2 storage)

### Integrações
- `projeto/docs-externos/integracoes.md` §7 (Backblaze B2 + Cloudflare), §3 (Receita p/ MEI), §4 (SMS)

### UI
- `projeto/wireframes/03-cadastro-entregador.html`, `19-admin-area-entregador-detalhe.html`
- Design system + componentes Phase 3 (apps/web); adapters/seed/área da Phase 4

### Backend a reusar (Phase 2/4)
- `apps/api/app/auth/` (users/argon2id), `apps/api/app/areas/` (área+escopo), adapters da Phase 4 (Receita/SMS/storage pattern), `audit_log`, AreaScoped

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-013, REQ-014, REQ-015, REQ-019 (parcial mei_pending)

### Segurança (Gate 4)
- `.claude/skills/standalone/owasp-security/SKILL.md` — upload seguro, data-protection, SSRF; `.claude/skills/br/lgpd-compliance/SKILL.md`
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 4: adapter pattern (Receita/SMS/SES/geocoding + Stub + SSRF guard), seed/área, máscaras PII, ratelimit, máquina de estados — REUSAR para couriers e storage.
- Phase 2: users/argon2id, AreaScoped, audit_log, anti-enumeração.
- Phase 3: design system, componentes de estado, file-upload-ux (novo nesta phase), wizard stepper.

### Established Patterns
- `/v1` API, RFC-7807, idempotência, PII fora de log (CPF/documentos mascarados). área via escopo. aware UTC (TD-010) em OTP/expiração de documentos.
- Upload: presigned URL direto do cliente (não passa pelo backend), validar content-type/tamanho, hash no cliente confirmado server-side.

### Integration Points
- courier vincula a `areas`. Documentos no B2 (adapter). MEI via adapter Receita (reuso Phase 4). Revisão do admin → audit_log. Gate 5 valida contratos B2/Receita/SMS (stubs).
</code_context>

<specifics>
## Specific Ideas

- Arquivos KYC NUNCA públicos — só URL assinada de expiração curta (invariante de dados). Hash SHA-256 anti-tamper.
- Selfie/documentos são PII sensível (LGPD) — bucket privado, sem PII em log, anonimização agendada (RN-021).
- Reenvio item-a-item: reprovar a CNH não invalida a selfie já aprovada.
- mei_pending destrava onboarding no interior (RN-024) — entregador trabalha no direto sem MEI.
- Upload offline-tolerante no app (mobile/offline-first) — foto fica no device e sobe quando reconectar (relevante também na Phase 9; aqui o upload de KYC pode ser mais simples, mas a resiliência conta).
</specifics>

<deferred>
## Deferred Ideas

- Cobertura (bairros) e tabela de frete (F-02 etapa 7) — Phase 6.
- Online/offline/busy + ofertas/despacho — Phase 8.
- Bloqueio de repasse via plataforma por MEI (RN-010) + saques — Phase 10/11.
- Score do entregador — Phase 13.
- Recurso de suspensão (RN-016) UI completa — Phase 13 (aqui só status banned/suspended no schema).
</deferred>

---

*Phase: 05-cadastro-do-entregador-kyc-2-n-veis-documentos-b2*
*Context gathered: 2026-06-10*
