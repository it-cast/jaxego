---
phase: 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete
plan: 03
subsystem: backend (couriers coverage/pricing/availability)
tags: [coverage, pricing-floor, availability, rn-003, rn-015, req-018]
requires:
  - "Plan 01 migration 0005 (courier_coverage_areas/courier_pricing_tables/couriers.is_online,max_concurrent)"
  - "Plan 02 Neighborhood (validação cross-area de cobertura)"
provides:
  - "coverage.is_eligible (dois pontos + exclusão) — primitivo da Phase 8"
  - "pricing.assert_above_floor / set_pricing (piso citado — RN-015)"
  - "availability.set_availability (só active) + compute_busy derivado"
  - "rotas self-only /v1/couriers/{id}/coverage|pricing|availability"
affects:
  - "apps/api/app/couriers/models.py (2 modelos novos + 2 colunas)"
  - "apps/api/app/couriers/router.py + schemas.py"
tech-stack:
  added: []
  patterns:
    - "funções puras (is_eligible/assert_above_floor/compute_busy) testáveis em SQLite"
    - "self-only via user_id do token == courier (sem role 'courier' fantasma)"
key-files:
  created:
    - apps/api/app/couriers/coverage.py
    - apps/api/app/couriers/pricing.py
    - apps/api/app/couriers/availability.py
  modified:
    - apps/api/app/couriers/models.py
    - apps/api/app/couriers/schemas.py
    - apps/api/app/couriers/router.py
    - apps/api/tests/conftest.py
decisions:
  - "self-only por user_id do token == courier (resolve_role não emite 'courier'); area-scoped; cross → 404"
  - "busy nunca persistido — compute_busy derivado (0 entregas no M1)"
metrics:
  duration: ~35min
  tasks: 2
  files: 7
  completed: 2026-06-10
---

# Phase 6 Plan 03: Cobertura + frete + disponibilidade Summary

Lado da oferta pronto para o despacho (Phase 8): cobertura include/exclude com elegibilidade nos dois pontos (RN-003), tabela de frete por bairro ou km com guard-rail de piso que CITA o valor ao rejeitar (RN-015 — a plataforma nunca fixa o preço) e disponibilidade online/offline só para courier `active` com `busy` derivado (REQ-018) — tudo area-scoped e self-only sobre a entidade `couriers` da Phase 5.

## Tasks Completed

| Task | Nome | Commit | Arquivos-chave |
|------|------|--------|----------------|
| 1 | Cobertura (RN-003) + piso (RN-015) | 0cae675 | models.py, coverage.py, pricing.py, schemas.py |
| 2 | Disponibilidade (REQ-018) + router | 2039232 | availability.py, router.py |

## Decisões / notas

- **Self-only sem role "courier" fantasma:** `resolve_role` (Phase 2) só emite `admin_plataforma` / `admin_area:*` / `user`. O plano sugeria `require_role("courier")`, que nunca casaria. Implementei a regra correta: o courier edita só o PRÓPRIO registro via `_own_courier` (`Courier.user_id == user.id`, area-scoped); qualquer mismatch → 404 (sem vazar existência). Isto é mais seguro que um role genérico e respeita o modelo de auth existente.
- **`busy` é sempre derivado** (`compute_busy(active_deliveries, max_concurrent)`); nenhuma coluna `busy`. A contagem real de entregas ativas chega na Phase 7/8 (0 no M1).
- **Piso vem do `AreaConfig` (Plan 01)** — `set_pricing` lê `piso_km`/`piso_entrega` da config tipada; nunca hardcoded. LOW-5: aumento de piso não revalida linhas já salvas (TD-018).

## Deviations from Plan

- **[Rule 2 - Segurança] Self-only por `user_id` em vez de `require_role("courier")`.** O role "courier" não existe no `resolve_role` do projeto; usar a sugestão literal do plano deixaria as rotas inacessíveis ou inseguras. Apliquei a regra de propriedade (token user == courier) + area scope, que é o requisito real (item 2/6 das Security Notes). Documentado aqui; sem mudança de contrato externo.

## Tech debt
- **TD-018** (registrada na Plan 01): aumento de piso retroativo só sinaliza, não bloqueia.

## Verificação local
- `uv run pytest -m "not mysql"` → **206 passed, 7 deselected (mysql)**.
- `uv run ruff check .` + `ruff format --check .` → limpos (151 arquivos).
- `uv run basedpyright app` → 0 errors.
- Testes: `test_coverage.py` (dois pontos + exclusão + set/list area-scoped), `test_pricing_floor.py` (piso km/entrega cita valor), `test_availability.py` (só active online; busy derivado) — todos verdes em SQLite.

## Itens @pytest.mark.mysql (rodar ao vivo)
- Nenhum específico desta plan (cobertura/piso/disponibilidade são testáveis em SQLite). Os FK RESTRICT das novas tabelas (`courier_coverage_areas`/`courier_pricing_tables`) só são enforced em MySQL real — cobertos pela migration 0005 ao vivo.

## Self-Check: PASSED
- coverage.py, pricing.py, availability.py — FOUND. Commits 0cae675, 2039232 — FOUND.
