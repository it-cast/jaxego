---
gsd_state_version: 1.0
milestone: MS-02
milestone_name: Cadastros + área operável
status: in_progress
last_updated: "2026-06-10T22:10:00.000Z"
last_activity: "2026-06-10 — Phase 6 EXECUTADA (área operável: migration 0005 espacial + AreaConfig tipada/audit + catálogo de bairros ST_Contains + cobertura/piso/disponibilidade + admin web jx-data-table + entregador mobile)."
progress:
  total_phases: 14
  completed_phases: 6
  total_plans: 5
  completed_plans: 5
  percent: 43
---

# STATE — Current Execution State

> Documento vivo. Claude Code lê ao iniciar sessão. Atualiza ao fechar plano.
> Populado por `gsd-project-ingestor` em 2026-06-10 a partir de `projeto/` (36+ arquivos).

---

```yaml
milestone: MS-02
milestone_name: Cadastros + área operável
status: in_progress
release_target: v1.0 (piloto Pádua)
progress:
  total_phases: 14
  completed_phases: 6
  percent: 43
```

## Project Reference

See: `.planning/PROJECT.md` (ingest em 2026-06-10)

**Core value:** Malha de entregadores por área para o interior do Brasil, integrada ao Menu Certo, com pagamento direto como modalidade de 1ª classe.
**Current focus:** MS-01 (Fundação) completo. Próximo milestone: MS-02 (cadastros + área operável) — começa pela Phase 4 (cadastro de loja).

## Current Position

- **Milestone:** MS-02 (Cadastros + área operável) — em andamento
- **Phase atual:** 6 of 14 — Área operável (bairros, config, cobertura e tabela de frete) — ✅ EXECUTADA (verificação ao vivo MySQL pendente: migration 0005 + ST_Contains)
- **Próxima Phase:** 7 of 14 — Criação de entregas
- **Last activity:** 2026-06-10 — Phase 6 executada (área operável: migration 0005 espacial + AreaConfig tipada/audit + catálogo de bairros ST_Contains + cobertura/piso/disponibilidade + admin web jx-data-table + entregador mobile).

**Progress:** [████░░░░░░] 43%

## MS-01 — entregue

- **Phase 1:** monorepo, FastAPI `/health` (verificado ao vivo: 200), Docker Compose (api/worker/mysql/redis), Alembic, observabilidade, CI, guard naive datetime. 2 bugs runtime pegos no smoke ao vivo e corrigidos (cryptography, arq heartbeat).
- **Phase 2:** areas/users/area_admins/refresh_tokens/audit_log, auth JWT+refresh opaco+argon2id+TOTP+lockout, RBAC 6 papéis, isolamento multi-área, trigger append-only (verificado em MySQL 8 real: errno 1644). 69 testes.
- **Phase 3:** apps/web Angular 19 + Ionic 8, design system claro+dark (DEC-001) via tokens, componentes de estado, login → /v1/auth/login, shell 3 superfícies. ng build 155KB, 25 testes, zero hardcode.

## MS-02 — em andamento

- **Phase 4:** F-01 cadastro de loja no caminho Free. Backend: merchants/merchant_users/subscription_plans/merchant_subscriptions (migration 0003), service E1–E4 (CNPJ inativo, anti-enumeração, pago→pending_payment, Receita down→pending_validation), adapters Receita/SMS/SES/geocoding (Protocol+httpx+Stub+SSRF), OTP/job aware-UTC, seed idempotente. Frontend: wizard tela 02 (stepper, forms BR, persistência sem senha, E1/E2), estado vazio + captura de interesse, plano tela 16 data-driven, banners pending_* + onboarding. 112 testes backend (not-mysql) + 33 frontend, zero hex. TD-014/TD-015 registradas. ✅ verificada ao vivo MySQL.
- **Phase 5:** F-02 cadastro/KYC do entregador. Backend: couriers/courier_documents (migration 0004, AreaScoped, unique (area_id,cpf) → E2), StoragePort (Protocol+Stub FS+B2 boto3 S3v4) com presigned PUT/GET, pipeline media (magic bytes + Pillow WebP + strip total EXIF + SHA-256 do derivado, anti-bomb), endpoints /v1/couriers/* (signup público rate-limited, presign, complete, MEI) + /v1/admin/couriers/* (view-url, PATCH review item-a-item), máquina de estados dupla (422), KYC 2 níveis RN-002, MEI mei_pending RN-024 (E3), jobs aware-UTC (expiração + escalação 48h E5). Frontend: jx-doc-upload/jx-doc-card/jx-kyc-queue-table/jx-kyc-review-row (stories + a11y), wizard Ionic tela 03 (stepper condicional 3/4, draft sem senha E1, upload presign background), painel admin tela 19 (review otimista, CPF mascarado, Score placeholder), em-análise + banner mei_pending. **179 testes backend (not-mysql) + 46 frontend, zero hex.** TD-016 (antivírus PDF) registrada. **Pendente ao vivo:** migration 0004 reversível + FK RESTRICT (`pytest -m mysql`) + integration check B2 (Gate 5, conta real).
- **Phase 6:** Área operável (F-08 + RN-003/RN-015 + REQ-016/017/018). Backend: **migration 0005** (neighborhoods_catalog com `polygon POLYGON NULL SRID 4326` via DDL MySQL-only + courier_coverage_areas + courier_pricing_tables + couriers.is_online/max_concurrent); **AreaConfig** Pydantic tipada (ranges geofence/timeouts/pisos/retorno, `extra=forbid`) substituindo JSON cru + **audit before/after** em config sensível (RN-012/F-08 E2); módulo **neighborhoods/** (CRUD area-scoped, polígono GeoJSON validado por shapely, `point_in_polygon` ST_Contains lat-first via func.ST_* sem GeoAlchemy2 — LOW-1); **cobertura** include/exclude com elegibilidade nos dois pontos (RN-003), **tabela de frete** com piso citado na rejeição (RN-015 — plataforma nunca fixa preço), **disponibilidade** online/offline só para active + busy derivado (REQ-018), rotas self-only. Frontend: **jx-data-table** primitivo governado, tela 21A config da área (máscara monetária pt-BR + confirmação sensível before→after), tela 21B catálogo de bairros (CRUD + GeoJSON + remoção bloqueada), tela 10 entregador cobertura+preços (modo bairro/km + validação de piso citando o valor), **jx-availability-toggle**. **206 testes backend (not-mysql) + 65 frontend, zero hex.** TD-017 (SPATIAL INDEX nullable) + TD-018 (piso retroativo) + SUG-008/009 registradas. **Pendente ao vivo:** migration 0005 reversível + `ST_Contains` ponto-em-polígono dentro/fora (`pytest -m mysql tests/neighborhoods/test_spatial.py`) + smoke visual das telas 21/10.

## Atenção para MS-02+

1. **OQ-3 (contrato Safe2Pay) bloqueia a Phase 10** — resolver antes de chegar lá; Phases 4–9 podem prosseguir.
2. **OQ-1 (revenue share admin de área)** — idealmente decidir antes da Phase 10/13.
3. Valores de planos/taxas são `[ASSUMIDO]` — implementar parametrizado (seeds), nunca hardcoded.
4. **Seed de admin de plataforma** ainda não existe — necessário para smoke de login end-to-end e provavelmente para a Phase 4 (onboarding de loja).
5. Sem GitHub remote configurado — CI não validado em execução remota (item de release).

## Próximo passo

```

# Verificar Phase 6 ao vivo (MySQL real) — migration 0005 + ST_Contains ponto-em-polígono:

cd apps/api && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
cd apps/api && uv run pytest -m mysql tests/neighborhoods/test_spatial.py

# Smoke visual (telas 21A/21B/10) claro+dark; validação de piso citando o valor.

# Depois:

/gsd:reconcile-state 6      # reconciliação prometido vs. código
/gsd:discuss-phase 7        # Criação de entregas
```
