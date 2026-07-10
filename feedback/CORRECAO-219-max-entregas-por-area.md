# CORRECAO-219 — max_entregas_simultaneas movido de couriers para areas.config

## Data
2026-07-09

## Problema
`couriers.max_concurrent` era um limite por entregador (coluna INTEGER), mas a
regra de negócio correta é que o limite deve ser definido pelo admin da área e
aplicado a todos os entregadores daquela área.

## Solução implementada

### 1. `areas/config_schema.py`
- Adicionado `max_entregas_simultaneas: int = Field(default=1, ge=1, le=10)` a `AreaConfig`
- Adicionado `"max_entregas_simultaneas"` a `SENSITIVE_KEYS` (mudanças auditadas)

### 2. `dispatch/cascade.py`
- `build_candidates` recebe novo parâmetro `area_max_concurrent: int = 1`
- Filtra entregadores usando `area_max_concurrent` no lugar de `courier.max_concurrent`

### 3. `workers/dispatch.py`
- Todas as 3 chamadas a `build_candidates` passam `area_max_concurrent=cfg.max_entregas_simultaneas`
- `cfg` já era carregado via `_area_config()` em todas as chamadas

### 4. `couriers/models.py`
- Removida coluna `max_concurrent: Mapped[int]`

### 5. `couriers/availability.py`
- Removidos `set_max_concurrent()` e `InvalidMaxConcurrentError`
- `compute_busy()` mantido (puro, ainda recebe `max_concurrent` como argumento)

### 6. `couriers/router.py`
- `set_availability` carrega `AreaConfig` da área para obter `max_entregas_simultaneas`
- Importados `Area` e `AreaConfig`

### 7. Testes
- Removido `max_concurrent=N` de todos os construtores `Courier()` em testes
- `dispatch/conftest.py`: área seed tem `config={"max_entregas_simultaneas": 2}` para manter semântica dos testes
- `test_availability.py`: `test_compute_busy_is_derived` corrigido manualmente após sed remover os args

### 8. Alembic — migration 0041
- `op.drop_column("couriers", "max_concurrent")`
- Aplicada em produção via `docker exec alembic upgrade head`

## Como o admin configura
Via `PATCH /v1/admin/area/config` com body `{"config": {"max_entregas_simultaneas": 3}}`.
A mudança é auditada em `write_audit("area.config.update", ...)`.

## Intervalo válido
`ge=1, le=10` — mínimo 1, máximo 10 entregas simultâneas por entregador.
