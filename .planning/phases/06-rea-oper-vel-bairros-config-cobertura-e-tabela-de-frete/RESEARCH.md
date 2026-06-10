# Phase 6: Área operável — bairros, config, cobertura e tabela de frete — Research

**Researched:** 2026-06-10
**Domain:** MySQL 8 spatial (POINT/POLYGON, SRID 4326, índices espaciais) + modelagem de cobertura/preço com piso
**Confidence:** HIGH (espacial MySQL — verificado em docs oficiais) / MEDIUM (integração GeoAlchemy2 ↔ aiomysql async — não bem documentada, ver LOW confidence)

---

<user_constraints>
## User Constraints (from 06-CONTEXT.md)

### Locked Decisions
- **D-01:** `neighborhoods_catalog` por área, curado pelo admin local: nome + polígono OPCIONAL (GeoJSON/WKT → tipo espacial MySQL). Inclui bairros informais. Modo default da área = `neighborhood`. Polígono é opcional no M1 (bairro por nome funciona). Travado por ADR-006.
- **D-02:** CRUD de bairros no painel do admin de área (tela 21), escopado por área (RBAC + AreaScoped).
- **D-03:** Admin de área configura: nível de validação (simples/completa), piso de frete (por km E por entrega), raio de geofence (m), timeouts de despacho (oferta default 20s, favoritos default 60s — ADR-104/ADR-007), política de retorno (% sobre a corrida). Tudo em `areas`. Mudanças sensíveis → audit_log.
- **D-04:** `courier_coverage_areas` — bairros do catálogo onde o entregador atende, com exclusões. Vale para coleta E entrega (RN-003). Elegibilidade exige cobertura nos DOIS pontos; exclusões vetam nos dois.
- **D-05:** `courier_pricing_tables` — linhas por bairro OU faixas por km, com % de retorno. Respeita PISO da área (rejeita preço abaixo do piso com mensagem citando o piso). A plataforma NUNCA fixa o preço.
- **D-06:** Entregador alterna online/offline; `busy` derivado da carga (entregas ativas vs máx simultâneas). Só entregador `active` (KYC ok) pode ficar online. Estado pronto para o despacho (Phase 8).
- **D-07:** Tipos espaciais nativos do MySQL 8 (POINT, POLYGON, SRID 4326) + índices espaciais; elegibilidade por `ST_Contains`/`ST_Within`; geofence por raio (`ST_Distance_Sphere`) quando não há polígono.

### Claude's Discretion
- Formato de entrada de polígono no admin (desenhar no mapa vs colar GeoJSON — M1 aceita GeoJSON/coordenadas; desenho no mapa é nice-to-have).
- Estrutura exata das tabelas de cobertura/preço e índices espaciais.
- Como representar "por km" vs "por bairro" no schema de pricing.

### Deferred Ideas (OUT OF SCOPE)
- Despacho/ofertas/cascata (consome cobertura+disponibilidade) — Phase 8.
- Criação de entregas (usa bairro do catálogo) — Phase 7.
- Mapa interativo de tracking (MapLibre) — Phase 9 (DEC-002).
- Desenho de polígono no mapa pelo admin — nice-to-have pós-M1.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-003 | Catálogo de bairros | Schema `neighborhoods_catalog` (§Modelagem); POLYGON nullable; SRID 4326 |
| REQ-002 (UI config — tela 21) | Config da área | Estende `Area.config` (JSON já existe) com validação tipada + audit (§Modelagem, §Security) |
| REQ-016 | Cobertura coleta E entrega | `courier_coverage_areas` (include/exclude); RN-003 nos dois pontos (§Modelagem, §Pattern 3) |
| REQ-017 | Tabela de frete com piso | `courier_pricing_tables` (modo bairro\|km); validação de piso RN-015 (§Validação de piso) |
| REQ-018 | Online/offline/busy | Campos em `couriers`; `busy` derivado (§Modelagem) |
| REQ-044 (parcial) | KYC fila + config + bairros | Config + bairros desta phase; fila KYC já em Phase 5 |
</phase_requirements>

## Summary

A Phase 6 torna a área operável apoiada inteiramente no **suporte espacial nativo do MySQL 8.0** — não em um banco espacial externo. As três decisões técnicas centrais já estão travadas (D-07): tipos `POINT`/`POLYGON` com **SRID 4326**, índices `SPATIAL`, elegibilidade por ponto-em-polígono (`ST_Contains`/`ST_Within`) e geofence por raio (`ST_Distance_Sphere`) quando não há polígono. O MySQL 8.0 é maduro nisso: desde a 8.0 os SRIDs têm significado real (geometrias 4326 são tratadas como geográficas, em metros) `[CITED: dev.mysql.com/doc/refman/8.0]`.

A descoberta mais importante do research é uma **divergência entre a expectativa do ecossistema e a realidade do projeto**: GeoAlchemy2 é um toolkit PostGIS-first; o suporte a MySQL existe mas é secundário e a combinação **GeoAlchemy2 + aiomysql + SQLAlchemy 2 async não é bem documentada** `[VERIFIED: WebSearch + GeoAlchemy2 issue #318]`. O projeto Jaxegô usa `mysql+aiomysql` em produção e **`sqlite+aiosqlite` in-memory nos testes** (com `Base.metadata.create_all` e `@pytest.mark.mysql` para o que é MySQL-only) `[VERIFIED: apps/api/tests/conftest.py, apps/api/app/db/session.py]`. Tipos espaciais nativos quebram `create_all` no SQLite. Por isso a recomendação primária diverge do caminho "óbvio".

**Primary recommendation:** **NÃO** adotar a pilha ORM completa do GeoAlchemy2. Definir as colunas espaciais como `Geometry`/`POLYGON`/`POINT` apenas no nível da **migration Alembic** (DDL bruto MySQL), mantendo nos models SQLAlchemy uma coluna espacial com `.with_variant()` que degrada para algo benigno no SQLite (ou models MySQL-only para as tabelas espaciais). Executar toda a lógica espacial via **`func.ST_*` em SQL bruto/Core** (`ST_GeomFromGeoJSON`, `ST_Contains`, `ST_Distance_Sphere`, `ST_AsGeoJSON`), testando o ponto-em-polígono com `@pytest.mark.mysql` (espelhando o padrão já estabelecido na Phase 5) e a lógica de **piso e cobertura por NOME** em SQLite. Polígono é opcional no M1 — a cobertura por nome de bairro já entrega valor e é 100% testável sem MySQL.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Validação/parse de GeoJSON de polígono | API / Backend | — | Input não confiável; valida antes de tocar o DB (anti-DoS) |
| Armazenar POLYGON/POINT (SRID 4326) | Database / Storage | — | Tipo espacial + SPATIAL INDEX são do MySQL; nunca recalcular no app |
| Ponto-em-polígono (elegibilidade) | Database / Storage | API | `ST_Contains` roda no MySQL; o app monta a query e interpreta |
| Geofence por raio (fallback sem polígono) | Database / Storage | API | `ST_Distance_Sphere` no MySQL retorna metros |
| Validação de piso (RN-015) | API / Backend | — | Regra de negócio pura; comparação numérica testável em SQLite |
| RBAC de área (admin edita só a sua) | API / Backend | — | `AreaScoped` + `resolve_role` já existem (Phase 2) |
| Audit de config sensível | API / Backend | Database | `write_audit` grava `before/after` em `audit_log` |
| Estado online/offline/busy | API / Backend | Database | `busy` é DERIVADO (carga); persistir só online/offline |
| CRUD de bairros / config / cobertura / preço (tela 21, 10) | Frontend Server / Client | API | Formulários Angular/Ionic consomem `/v1` |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| MySQL | 8.0 (travado em stack.md) | Tipos espaciais nativos, SPATIAL INDEX (R-tree), funções `ST_*` | Já é o banco do projeto; spatial nativo dispensa PostGIS `[VERIFIED: stack.md:13]` |
| SQLAlchemy | 2.x (travado) | ORM + Core para montar as queries `func.ST_*` | Já no projeto; `func.ST_Contains(...)` funciona sem GeoAlchemy2 `[VERIFIED: stack.md:11]` |
| Alembic | (travado) | Migration 0005 com DDL espacial bruto | Padrão do projeto; migrations 0001–0004 já existem `[VERIFIED: apps/api/alembic/versions/]` |
| aiomysql | (driver atual) | Driver async MySQL | Já configurado: `mysql+aiomysql://...` `[VERIFIED: apps/api/app/core/config.py:32]` |
| Pydantic | v2 (FastAPI 0.115) | Validação tipada do GeoJSON / ranges numéricos / piso | Já no projeto; valida input espacial antes do DB |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| GeoAlchemy2 | 0.20.x (mais recente) | Tipo `Geometry` mapeável + `WKBElement` na leitura | SÓ se a equipe quiser o tipo ORM; ver LOW-1 antes de adotar. Recomendação: **dispensar no M1** |
| shapely | 2.x | Validar/medir polígono (área, nº de vértices) no app antes de inserir | Defesa anti-DoS de polígono gigante; valida GeoJSON server-side |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MySQL spatial nativo | PostGIS (Postgres) | Troca de banco = ADR + reescrita; MySQL 8 cobre o caso do M1. **Rejeitado por ADR-006/stack.** |
| `func.ST_*` em Core (nativo) | GeoAlchemy2 ORM completo | GeoAlchemy2 é PostGIS-first; async+aiomysql+MySQL pouco documentado (LOW-1). Mais risco que valor no M1. |
| POLYGON por bairro | Geofence raio-only | ADR-006 rejeitou raio-only explicitamente (cidades de geografia irregular). Mas raio é o **fallback** sem polígono. |
| Coluna `Geometry` nos models | lat/lng Float (como `merchants`) | `merchants` já guarda `lat/lng` Float (NÃO POINT nativo). POINT nativo só onde precisa de SPATIAL INDEX/`ST_Contains`. |

**Installation:**
```bash
# Já tudo no projeto. Adicionar APENAS se for validar polígono no app (recomendado):
uv add shapely
# GeoAlchemy2: NÃO adicionar no M1 sem decidir LOW-1 primeiro.
```

**Version verification:**
```bash
# Confirmar a versão do MySQL do compose antes de assumir funções (ST_Distance_Sphere existe ≥ 5.7.6):
docker compose exec mysql mysql --version
# GeoAlchemy2 (se for adotar): npm/pip equivalente
python -c "import geoalchemy2, sys; print(geoalchemy2.__version__)"
```
`ST_GeomFromGeoJSON`/`ST_AsGeoJSON` existem desde 5.7.5; `ST_Distance_Sphere` desde 5.7.6; SRS com significado real desde 8.0 — todos disponíveis no MySQL 8.0 travado `[CITED: dev.mysql.com/doc/refman/8.0/en/spatial-geojson-functions.html]`.

## Architecture Patterns

### System Architecture Diagram

```
ADMIN DE ÁREA (tela 21)                ENTREGADOR (tela 10, mobile)
   │ POST/PATCH /v1/areas/{id}/config     │ PUT /v1/couriers/{id}/coverage
   │ POST /v1/neighborhoods (GeoJSON)     │ PUT /v1/couriers/{id}/pricing
   │                                      │ PATCH /v1/couriers/{id}/availability
   ▼                                      ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI /v1  (AreaScoped dependency → WHERE area_id)          │
│                                                              │
│  ┌────────────────┐  validação de input ANTES do DB         │
│  │ Pydantic v2    │  · GeoJSON: tipo Polygon, nº vértices,   │
│  │ + shapely      │    área máx (anti-DoS)                   │
│  └───────┬────────┘  · piso: preço ≥ piso da área (RN-015)  │
│          │           · ranges: geofence_m, timeouts          │
│          ▼                                                   │
│  ┌─────────────────────────────────────────┐                │
│  │ service: monta func.ST_* (Core)          │                │
│  │  · insert: ST_GeomFromGeoJSON(:gj,2,4326)│                │
│  │  · query: ST_Contains(poly, point)       │                │
│  │  · fallback: ST_Distance_Sphere ≤ geofence│               │
│  └───────┬──────────────────────┬────────────┘               │
│          │ write_audit(before/after) em config sensível      │
└──────────┼──────────────────────┼───────────────────────────┘
           ▼                      ▼
   ┌───────────────┐      ┌──────────────────────┐
   │ audit_log     │      │ MySQL 8 (InnoDB)     │
   │ (before/after)│      │ neighborhoods_catalog│  POLYGON SRID 4326
   └───────────────┘      │   (+ SPATIAL INDEX)  │  (nullable → ver pitfall 1)
                          │ courier_coverage_areas│ include/exclude
                          │ courier_pricing_tables │ mode bairro|km + piso check
                          │ areas.config (JSON)    │ kyc/piso/geofence/timeouts
                          │ couriers.is_online     │ online/offline
                          └──────────────────────┘
                                   ▲
                                   │ consumido depois por:
                          Phase 7 (criação) · Phase 8 (despacho/elegibilidade)
```

### Recommended Project Structure
```
apps/api/app/
├── areas/
│   ├── models.py        # Area.config já existe (JSON) — adicionar config tipada/validada
│   ├── config_schema.py # NOVO: Pydantic AreaConfig (kyc_level, piso_km, piso_entrega,
│   │                     #        geofence_m, timeout_oferta_s, timeout_favoritos_s,
│   │                     #        politica_retorno_pct) + ranges + audit hook
│   └── service.py       # estender update_area p/ validar config + write_audit sensível
├── neighborhoods/       # NOVO módulo
│   ├── models.py        # neighborhoods_catalog (POLYGON nullable — model MySQL-only/variant)
│   ├── schemas.py       # GeoJSON in/out (shapely valida), name
│   ├── spatial.py       # NOVO: helpers func.ST_* (point_in_polygon, within_geofence)
│   ├── service.py       # CRUD bairro (AreaScoped); ST_GeomFromGeoJSON na escrita
│   └── router.py        # /v1/neighborhoods
└── couriers/            # estender (Phase 5 já existe)
    ├── models.py        # + is_online, max_concurrent
    ├── coverage.py      # NOVO: courier_coverage_areas (include/exclude)
    ├── pricing.py       # NOVO: courier_pricing_tables (mode bairro|km, piso check)
    └── availability.py  # NOVO: online/offline; busy DERIVADO
```

### Pattern 1: Coluna espacial só na migration; lógica via `func.ST_*`
**What:** Definir `POLYGON`/`POINT NOT NULL SRID 4326 + SPATIAL INDEX` no DDL da migration; nos models, manter a tabela MySQL-only (ou variant que vira `TEXT`/nada no SQLite). Toda leitura/escrita espacial usa `func.ST_*` em SQL Core.
**When to use:** Sempre nesta phase, para `neighborhoods_catalog.polygon` e qualquer POINT que exija SPATIAL INDEX.
**Example:**
```python
# Source: padrão derivado de [VERIFIED: dev.mysql.com spatial-geojson-functions] +
#         convenção do projeto (apps/api/alembic/versions/0004_couriers_kyc.py)
# --- migration 0005 (DDL bruto onde Alembic não modela Geometry nativo) ---
op.execute("""
    ALTER TABLE neighborhoods_catalog
    ADD COLUMN polygon POLYGON NULL SRID 4326
""")
# ATENÇÃO: SPATIAL INDEX exige NOT NULL. polygon é NULLABLE (opcional no M1),
# logo NÃO é possível SPATIAL INDEX direto nesta coluna (ver Pitfall 1).

# --- insert via service (SQL Core, async) ---
from sqlalchemy import text
await session.execute(
    text("""
        INSERT INTO neighborhoods_catalog (area_id, name, polygon, created_at, updated_at)
        VALUES (:area_id, :name,
                ST_GeomFromGeoJSON(:gj, 2, 4326),  -- options=2: aceita só geometrias
                :now, :now)
    """),
    {"area_id": area_id, "name": name, "gj": geojson_str, "now": now},
)
```

### Pattern 2: Ponto-em-polígono para elegibilidade (`ST_Contains`)
**What:** Dado um POINT (coleta/entrega) testar se cai num POLYGON de bairro.
**When to use:** Base da elegibilidade (RN-003) — consumida pela Phase 8.
**Example:**
```python
# Source: [CITED: geoalchemy2 orm_tutorial — ST_Contains] adaptado p/ MySQL nativo
from sqlalchemy import func, select
# point construído com SRID 4326. ATENÇÃO À ORDEM DE EIXOS (ver Pitfall 2).
point = func.ST_GeomFromText(f"POINT({lat} {lng})", 4326)  # 4326 = lat lng!
stmt = select(Neighborhood.id).where(
    func.ST_Contains(Neighborhood.polygon, point)
)
# ST_Within(point, polygon) é o inverso e equivalente para este caso.
# MBRContains usa só a bounding box (mais rápido, menos preciso) — usar como
# pré-filtro grosso, nunca como decisão final de elegibilidade.
```

### Pattern 3: Cobertura nos DOIS pontos + exclusões (RN-003)
**What:** Elegível só se a cobertura inclui o bairro da coleta E o da entrega, e nenhum dos dois está na lista de exclusão.
**When to use:** Modelagem de `courier_coverage_areas`.
**Example:**
```python
# Pseudocódigo da regra (a query real é Phase 8; aqui define o schema):
def is_eligible(coverage, pickup_nbhd_id, dropoff_nbhd_id) -> bool:
    included = {r.neighborhood_id for r in coverage if r.kind == "include"}
    excluded = {r.neighborhood_id for r in coverage if r.kind == "exclude"}
    pts = {pickup_nbhd_id, dropoff_nbhd_id}
    if pts & excluded:           # exclusão veta nos DOIS pontos
        return False
    return pts <= included        # AMBOS precisam estar incluídos (RN-003)
```

### Pattern 4: Geofence por raio quando não há polígono (`ST_Distance_Sphere`)
**What:** Sem polígono de bairro, usar distância esférica em metros do centro/ponto de referência.
**When to use:** Bairro sem polígono (M1) ou validação de geofence (RN-005, default 80 m — consumido na Phase 9).
**Example:**
```python
# Source: [VERIFIED: dev.mysql.com spatial-convenience-functions — ST_Distance_Sphere]
# Retorna metros; aceita Point/MultiPoint em SRID geográfico (4326). Default radius = raio médio.
within = func.ST_Distance_Sphere(point_a, point_b) <= geofence_m
```

### Anti-Patterns to Avoid
- **Recalcular ponto-em-polígono no Python (ray casting caseiro):** o MySQL faz isso correto e indexado. Não hand-roll (ver §Don't Hand-Roll).
- **Inverter eixos lat/lng:** GeoJSON é `[lng, lat]`; WKT em SRID 4326 é `lat lng`. Misturar = elegibilidade silenciosamente errada (Pitfall 2).
- **`SPATIAL INDEX` em coluna nullable:** o MySQL recusa — coluna de índice espacial precisa de `NOT NULL` (Pitfall 1).
- **Plataforma fixar o frete:** RN-015 proíbe; a plataforma só impõe piso e calcula sugestão.
- **Sobrescrever `Area.config` inteiro sem validar/auditar:** `update_area` atual troca o JSON cru; config sensível precisa de validação tipada + `write_audit`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ponto dentro de polígono | Ray-casting em Python | `ST_Contains`/`ST_Within` (MySQL) | Casos de borda (vértices, polígono côncavo, antimeridiano) já resolvidos e indexados |
| Distância geográfica | Haversine manual | `ST_Distance_Sphere` (metros) | MySQL usa o raio do SRS; menos erro de unidade `[VERIFIED]` |
| Parse/validação de GeoJSON | Regex/parser próprio | `shapely` (app) + `ST_GeomFromGeoJSON` (DB) | Valida estrutura, fecha anéis, detecta self-intersection |
| Conversão GeoJSON↔WKT | String building manual | `ST_GeomFromGeoJSON` / `ST_AsGeoJSON` | Cuida da reordenação de eixos do SRID 4326 automaticamente |
| Index espacial | Coluna + scan completo | `SPATIAL INDEX` (R-tree) | R-tree dá range scan; B-tree em geometria só serve exact-match `[CITED]` |
| Audit before/after | Log estruturado | `write_audit(...)` existente | É DADO (`audit_log`), não linha de log (RN-012) |

**Key insight:** Geometria computacional é um campo cheio de casos de borda (precisão de ponto flutuante, polígonos que cruzam o antimeridiano, anéis não fechados). O MySQL 8 entrega isso testado e indexado. O único código espacial "próprio" justificável é a **validação defensiva de input** (tamanho/forma do polígono) antes de mandar pro banco.

## Runtime State Inventory

> Phase greenfield em termos de tabelas espaciais (cria 0005), mas ESTENDE entidades existentes — inventário relevante:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `merchants.lat`/`merchants.lng` são **Float**, NÃO POINT nativo (`[VERIFIED: apps/api/app/merchants/models.py:67-69]`). D-07 diz "POINTs já existem" — impreciso no nível de schema. | Decisão de plano: para elegibilidade por `ST_Contains` precisa de POINT em SRID 4326. Construir o POINT on-the-fly via `ST_GeomFromText('POINT(lat lng)',4326)` a partir dos Floats (sem migração de dados), OU adicionar coluna POINT gerada. **Não migrar dados de merchants nesta phase** — montar POINT na query basta. |
| Stored data | `Area.config` já é coluna **JSON** existente, escrita crua por `update_area` (`[VERIFIED: apps/api/app/areas/service.py:113]`). | Adicionar validação tipada (Pydantic `AreaConfig`) + `write_audit` para chaves sensíveis. Migração de dados: seeds de área existentes podem não ter as novas chaves → tratar default no schema (não exige migration de dados). |
| Live service config | Nenhum serviço externo guarda estado desta phase (has_external_integration:false). | None — verificado pelas flags do ROADMAP. |
| OS-registered state | Nenhum. | None — verificado (sem cron/scheduler nesta phase). |
| Secrets/env vars | `DATABASE_URL` já existe; nenhuma nova secret. | None. |
| Build artifacts | Nenhum pacote novo obrigatório (shapely é opcional). | Se adotar shapely/GeoAlchemy2: `uv lock` + reinstalar. |

## Common Pitfalls

### Pitfall 1: SPATIAL INDEX exige coluna NOT NULL, mas o polígono é OPCIONAL
**What goes wrong:** Tentar `SPATIAL INDEX(polygon)` numa coluna `POLYGON NULL` → MySQL recusa a criação do índice.
**Why it happens:** "Columns in spatial indexes must be declared `NOT NULL`" `[VERIFIED: dev.mysql.com/doc/refman/8.0/en/creating-spatial-indexes.html]`. Mas D-01 trava polígono como opcional no M1.
**How to avoid:** Três opções para o plano decidir:
1. **(recomendado M1)** Não criar SPATIAL INDEX em `neighborhoods_catalog.polygon` (poucos bairros por área no piloto Pádua → full scan barato). Documentar como TD com `urgency_class: post_launch_quarter`.
2. Tabela separada `neighborhood_polygons` (1:0..1) com `polygon POLYGON NOT NULL SRID 4326 + SPATIAL INDEX`, só para bairros que têm polígono.
3. Sentinela (polígono "mundo todo") — **rejeitar**, polui a elegibilidade.
**Warning signs:** Erro do MySQL ao rodar a migration; ou índice silenciosamente ausente em SQLite (que ignora).

### Pitfall 2: Ordem de eixos — GeoJSON `[lng,lat]` vs WKT SRID 4326 `lat lng`
**What goes wrong:** Coordenada vira o lugar errado do mapa; `ST_Contains` retorna sempre falso (ou elegibilidade de outra cidade).
**Why it happens:** GeoJSON usa `[longitude, latitude]`; MySQL com SRID 4326 usa **latitude-first** em WKT. `ST_GeomFromGeoJSON('{"type":"Point","coordinates":[102.0,0.0]}')` retorna `POINT(0 102)` — eixos trocados de propósito porque o SRS 4326 define lat-primeiro `[VERIFIED: dev.mysql.com/doc/refman/8.0/en/spatial-geojson-functions.html]`.
**How to avoid:**
- Na entrada de GeoJSON: deixar `ST_GeomFromGeoJSON` cuidar da conversão (ele respeita o SRS). Não pré-transformar.
- Ao montar POINT à mão a partir de lat/lng Float: usar `ST_GeomFromText('POINT(lat lng)', 4326)` (lat primeiro), nunca `POINT(lng lat)`.
- Padronizar um único helper em `spatial.py` e testá-lo com `@pytest.mark.mysql` (um caso conhecido dentro, um fora).
**Warning signs:** Todos os pontos caem fora de todo polígono; ou distâncias absurdas no `ST_Distance_Sphere`.

### Pitfall 3: SQLite de teste não conhece tipos/funções espaciais
**What goes wrong:** `Base.metadata.create_all` no SQLite in-memory quebra se o model declara uma coluna `Geometry` nativa; `ST_Contains` não existe no SQLite.
**Why it happens:** A suíte usa `sqlite+aiosqlite://` + `create_all` `[VERIFIED: apps/api/tests/conftest.py:72-79]`. SQLite puro não tem spatial (SpatiaLite não está instalado).
**How to avoid:** (a) tabelas espaciais como models MySQL-only ou colocar a coluna espacial com `.with_variant()` para um tipo benigno no SQLite; (b) toda asserção de ponto-em-polígono em testes `@pytest.mark.mysql` (padrão já usado em `test_models.py::test_fk_restrict_area_delete_blocked` `[VERIFIED]`); (c) lógica de piso e cobertura-por-nome em SQLite normal.
**Warning signs:** `create_all` falha localmente; ou teste espacial "passa" no SQLite sem testar nada real.

### Pitfall 4: `Area.config` perde audit em mudança sensível
**What goes wrong:** Admin muda piso/geofence/KYC level e não há trilha `before/after` — viola RN-012 / F-08 E2.
**Why it happens:** `update_area` hoje sobrescreve `config` cru sem `write_audit` `[VERIFIED: apps/api/app/areas/service.py:107-115]`.
**How to avoid:** No update de config, comparar chaves sensíveis (piso_km, piso_entrega, geofence_m, kyc_level, timeouts, politica_retorno) e chamar `write_audit(actor_id, "area.config.update", before=..., after=...)` quando mudarem.
**Warning signs:** F-08 E2 sem teste; auditoria do Gate 8 aponta config sensível sem rastro.

## Code Examples

### Ler polígono de volta como GeoJSON
```python
# Source: [VERIFIED: dev.mysql.com spatial-geojson-functions — ST_AsGeoJSON]
from sqlalchemy import text
row = (await session.execute(text(
    "SELECT name, ST_AsGeoJSON(polygon) AS gj FROM neighborhoods_catalog WHERE id = :id"
), {"id": nbhd_id})).mappings().one()
# row["gj"] é string GeoJSON (lng,lat — ST_AsGeoJSON já reordena de volta p/ o padrão GeoJSON)
```

### Inserir POLYGON validado a partir de GeoJSON (com defesa anti-DoS no app)
```python
# Source: padrão derivado — shapely valida ANTES de tocar o DB
from shapely.geometry import shape
import json

def validate_polygon_geojson(gj: dict, *, max_vertices: int = 2000) -> None:
    if gj.get("type") != "Polygon":
        raise ValueError("Esperado um Polygon GeoJSON.")
    geom = shape(gj)                      # levanta se estrutura inválida
    if not geom.is_valid:                 # self-intersection, anel aberto
        raise ValueError("Polígono inválido (auto-interseção?).")
    n = sum(len(ring.coords) for ring in [geom.exterior, *geom.interiors])
    if n > max_vertices:                  # anti-DoS: polígono gigante
        raise ValueError(f"Polígono com vértices demais ({n} > {max_vertices}).")
# Só então: ST_GeomFromGeoJSON(:gj, 2, 4326) no INSERT (Pattern 1).
```

### Validação de piso (RN-015)
```python
# Source: regra de negócio pura — testável em SQLite (sem spatial)
class PriceBelowFloorError(AppError):
    status_code = 422
    code = "price_below_floor"
    def __init__(self, *, floor: float, kind: str) -> None:
        unit = "por km" if kind == "km" else "por entrega"
        super().__init__(
            f"Preço abaixo do piso da área ({unit}): mínimo R$ {floor:.2f}."
        )  # mensagem CITA o piso (RN-015)

def assert_above_floor(price: float, *, floor_km: float, floor_delivery: float, mode: str) -> None:
    if mode == "km" and price < floor_km:
        raise PriceBelowFloorError(floor=floor_km, kind="km")
    if mode == "neighborhood" and price < floor_delivery:
        raise PriceBelowFloorError(floor=floor_delivery, kind="delivery")
```

## Validação de Piso (RN-015) — detalhe

- **Dois pisos por área:** `piso_km` (R$/km) e `piso_entrega` (R$ fixo por entrega), ambos em `Area.config`.
- **A tabela do entregador tem um `mode`** (`neighborhood` | `km`). Linha por bairro valida contra `piso_entrega`; faixa por km valida contra `piso_km`.
- **Rejeição com mensagem que cita o piso** (critério de aceite do ROADMAP): "Preço abaixo do piso da área (por km): mínimo R$ X,XX." Status 422 (RFC-7807, padrão do projeto).
- **A plataforma nunca fixa o preço:** só rejeita abaixo do piso e pode calcular uma *sugestão* (não obrigatória). Não há "preço da plataforma".
- **Validação dupla:** no submit da tabela (rejeita a linha) E, defensivamente, quando o piso da área aumentar depois (linhas já salvas abaixo do novo piso → marcar/avisar; decisão de plano se bloqueia ou só sinaliza — sugerir sinalizar + TD).

## Security & Validation Notes

> Phase sem PII nova, sem integração externa, sem pagamento (has_pii:false / has_external_integration:false / has_payments:false) → **sem Security Baseline pesado de Gate 4**. Itens abaixo são o escopo de segurança real desta phase.

1. **Validação de GeoJSON / coordenadas (anti-DoS):** polígono é input não confiável. Validar server-side ANTES do DB — tipo `Polygon`, anel fechado, sem self-intersection (`shapely.is_valid`), **limite de vértices** (ex.: 2000) e **limite de área** (rejeitar polígono "continental"). Coordenadas lat∈[-90,90], lng∈[-180,180]. Sem isso, um polígono gigante/malformado pode degradar o `ST_Contains` em massa (DoS) e poluir a elegibilidade.

2. **RBAC de área (admin edita SÓ a sua área):** reusar `AreaScoped` + `resolve_role` (Phase 2). CRUD de bairros, config, e leitura de cobertura/preço filtram `WHERE area_id = scope`; recurso de outra área → **404, não 403** (não vaza existência — padrão `areas/service.py`). F-08 E1: admin agindo fora da própria área → bloqueado pelo escopo do token (RN-001).

3. **Audit em config sensível:** mudança de `piso_km`, `piso_entrega`, `geofence_m`, `kyc_level`, `timeout_oferta_s`, `timeout_favoritos_s`, `politica_retorno_pct` → `write_audit(action="area.config.update", before=..., after=...)` (RN-012 / F-08 E2). Audit é DADO em `audit_log`, nunca linha de structlog.

4. **Validação de input numérico (ranges):** Pydantic v2 com bounds explícitos —
   `geofence_m` (ex.: 20–2000), `timeout_oferta_s` 10–60 (ADR-104), `timeout_favoritos_s` (ex.: 30–300), `politica_retorno_pct` 0–100, `piso_km`/`piso_entrega` ≥ 0, `max_concurrent` ≥ 1. Rejeitar fora do range com RFC-7807. Evita config absurda que quebra o despacho da Phase 8.

5. **Sem PII:** bairros e polígonos não são PII; coordenadas de loja já existem (Phase 4). Nada novo de LGPD nesta phase. (Confirmado pelas flags do ROADMAP: has_pii:false.)

6. **Online/offline só para `active`:** apenas entregador com KYC ok (status `active`, Phase 5) pode ficar online (D-06) — validar no endpoint de availability para não vazar disponibilidade de quem não pode operar.

**Total de itens em Security & Validation Notes: 6.**

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MySQL 5.7: SRID era "decorativo" | MySQL 8.0: SRS têm significado; 4326 = geográfico (metros) | MySQL 8.0 | `ST_Distance_Sphere` e cálculos respeitam o SRS; precisa SRID correto na coluna `[CITED]` |
| GeoAlchemy2 só PostGIS | GeoAlchemy2 ganhou suporte MySQL (issue #318/#330) | ~2021+ | Existe, mas é secundário; async+aiomysql segue pouco documentado (LOW-1) |
| Geofence por bounding box | `ST_Distance_Sphere` esférico real | 5.7.6+ | Distância em metros correta para geofence/raio |

**Deprecated/outdated:**
- `GLength`, `Contains` (sem prefixo `ST_`): funções antigas pré-padronização — usar sempre as `ST_*`.
- `ST_Distance` para geofence: é genérico; para esfera-em-metros usar `ST_Distance_Sphere`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pádua (piloto) tem poucos bairros por área → full scan sem SPATIAL INDEX é aceitável no M1 | Pitfall 1 | Se a área tiver centenas de bairros, full scan degrada elegibilidade → vira TD de índice |
| A2 | `merchants.lat/lng` Float servem para construir POINT 4326 on-the-fly sem migração de dados | Runtime State Inventory | Se precisar SPATIAL INDEX em merchants, exige coluna POINT gerada (migração) — fora do M1 |
| A3 | `mode` da pricing table assume valores `neighborhood`\|`km` (nomes em inglês, padrão do schema) | Validação de Piso | Só convenção de nomenclatura; baixo risco |
| A4 | Limite de 2000 vértices / área máxima de polígono são razoáveis para bairro urbano | Security Notes / Code Examples | Limite muito baixo rejeita bairro legítimo; ajustável — confirmar com dono no discuss |
| A5 | shapely é aceitável como nova dependência (vs validar GeoJSON só no DB) | Standard Stack | Se a equipe não quiser nova dep, validar via `ST_IsValid`/`ST_GeomFromGeoJSON` no DB (mais round-trips) |

## Open Questions

1. **SPATIAL INDEX vs polígono nullable (Pitfall 1)**
   - What we know: SPATIAL INDEX exige NOT NULL; D-01 trava polígono opcional.
   - What's unclear: tabela separada de polígonos vs sem índice no M1.
   - Recommendation: M1 sem índice (Pádua é pequena) + TD `post_launch_quarter`; reavaliar quando uma área ultrapassar ~100 bairros com polígono.

2. **GeoAlchemy2 vs `func.ST_*` nativo (LOW-1)**
   - What we know: GeoAlchemy2 é PostGIS-first; async+aiomysql+MySQL pouco documentado.
   - What's unclear: se o tipo ORM `Geometry`/`WKBElement` funciona limpo no read async com aiomysql.
   - Recommendation: M1 com `func.ST_*` nativo (sem GeoAlchemy2). Vira **task de spike** se a equipe quiser o tipo ORM.

3. **Reação a aumento de piso posterior**
   - What we know: tabelas já salvas podem ficar abaixo de um piso novo.
   - What's unclear: bloquear o entregador ou só sinalizar.
   - Recommendation: sinalizar (não bloquear retroativo) + TD; decidir no discuss.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| MySQL 8.0 (compose) | Funções `ST_*`, SPATIAL INDEX, testes `@pytest.mark.mysql` | A confirmar no compose | 8.0 (stack.md) | Sem fallback: spatial real exige MySQL |
| aiomysql | Driver async já em uso | ✓ | — | — |
| SQLite + aiosqlite | Testes de piso/cobertura-por-nome | ✓ | — | — |
| shapely | Validação de polígono no app (opcional) | ✗ (a instalar) | 2.x | Validar via `ST_IsValid`/`ST_GeomFromGeoJSON` no DB |
| GeoAlchemy2 | Tipo ORM Geometry (NÃO recomendado M1) | ✗ | — | `func.ST_*` nativo (recomendado) |

**Missing dependencies with no fallback:** nenhuma bloqueante — o caminho recomendado usa só o que já existe.
**Missing dependencies with fallback:** shapely (validação no DB), GeoAlchemy2 (func.ST_* nativo).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (`@pytest.mark.asyncio`) |
| Config file | `apps/api/pyproject.toml` (markers `mysql`, `asyncio`) |
| Quick run command | `uv run pytest apps/api/tests/<modulo> -x` |
| Full suite command | `uv run pytest && uv run ruff check .` |
| MySQL-only marker | `@pytest.mark.mysql` (skipado fora do CI MySQL — padrão Phase 5) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-003 | Bairro criado com nome (sem polígono) | unit | `uv run pytest tests/neighborhoods/test_models.py -x` | ❌ Wave 0 |
| REQ-003 | Ponto dentro/fora de polígono decide elegibilidade | mysql | `uv run pytest -m mysql tests/neighborhoods/test_spatial.py -x` | ❌ Wave 0 |
| REQ-016 | Cobertura exige os DOIS pontos; exclusão veta | unit | `uv run pytest tests/couriers/test_coverage.py -x` | ❌ Wave 0 |
| REQ-017 | Preço < piso → 422 com piso na mensagem | unit | `uv run pytest tests/couriers/test_pricing_floor.py -x` | ❌ Wave 0 |
| REQ-018 | online só para courier `active`; busy derivado | unit | `uv run pytest tests/couriers/test_availability.py -x` | ❌ Wave 0 |
| REQ-002 | config sensível alterada → audit before/after | unit | `uv run pytest tests/areas/test_config_audit.py -x` | ❌ Wave 0 |
| REQ-016 | admin/courier de outra área → 404 | unit | `uv run pytest tests/.../test_authz.py -x` | ⚠️ estender Phase 5 |

### Sampling Rate
- **Per task commit:** `uv run pytest apps/api/tests/<modulo> -x` (rápido, SQLite).
- **Per wave merge:** `uv run pytest && uv run ruff check .` (inclui `-m mysql` no CI com MySQL).
- **Phase gate:** suíte completa verde (com MySQL no CI) antes de `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tests/neighborhoods/test_models.py` — REQ-003 (bairro por nome, SQLite)
- [ ] `tests/neighborhoods/test_spatial.py` — REQ-003 ponto-em-polígono, `@pytest.mark.mysql`
- [ ] `tests/neighborhoods/conftest.py` — fixtures de bairro/polígono (WKT/GeoJSON de teste)
- [ ] `tests/couriers/test_coverage.py` — REQ-016 (include/exclude, dois pontos)
- [ ] `tests/couriers/test_pricing_floor.py` — REQ-017 (piso km/entrega)
- [ ] `tests/couriers/test_availability.py` — REQ-018 (online/offline/busy)
- [ ] `tests/areas/test_config_audit.py` — REQ-002 (audit before/after)
- [ ] Confirmar marker `mysql` registrado no `pyproject.toml` (já usado na Phase 5 → provável existir)

## Sources

### Primary (HIGH confidence)
- `[VERIFIED]` MySQL 8.0 Reference — Spatial GeoJSON Functions: ST_GeomFromGeoJSON (default SRID 4326, options, reordenação de eixos), ST_AsGeoJSON — https://dev.mysql.com/doc/refman/8.0/en/spatial-geojson-functions.html
- `[VERIFIED]` MySQL 8.0 Reference — Creating Spatial Indexes (SPATIAL INDEX exige NOT NULL; R-tree; InnoDB/MyISAM) — https://dev.mysql.com/doc/refman/8.0/en/creating-spatial-indexes.html
- `[VERIFIED]` MySQL 8.0 Reference — ST_Distance_Sphere (retorna metros; SRS geográfico) — https://dev.mysql.com/doc/refman/8.0/en/spatial-convenience-functions.html
- `[VERIFIED]` Código do projeto: `apps/api/app/db/session.py` (aiomysql), `tests/conftest.py` (SQLite in-memory + create_all), `tests/couriers/test_models.py` (`@pytest.mark.mysql`), `apps/api/app/areas/{models,service}.py` (Area.config JSON), `apps/api/app/merchants/models.py` (lat/lng Float), `apps/api/alembic/versions/0004_couriers_kyc.py` (convenções de migration)

### Secondary (MEDIUM confidence)
- `[CITED]` GeoAlchemy2 docs (Context7 `/geoalchemy/geoalchemy2`): Geometry type, ST_Contains, from_shape/WKTElement — padrões majoritariamente PostGIS/MSSQL
- `[VERIFIED]` WebSearch: SRID 4326 axis-order ([102,0] → POINT(0 102)); mydbops "Enhancing GeoSpatial Data Management with MySQL 8.0"

### Tertiary (LOW confidence)
- `[VERIFIED como incerteza]` GeoAlchemy2 + aiomysql + SQLAlchemy 2 async = combinação pouco documentada (WebSearch + GeoAlchemy2 issue #318) — base do LOW-1

## LOW Confidence Items (Regra 12 → task ou TD)

| # | Item | Confidence | Vira | Critério de aceite / decisão |
|---|------|-----------|------|------------------------------|
| LOW-1 | GeoAlchemy2 vs Geometry nativo no SQLAlchemy 2 async + aiomysql (suporte de tipos espaciais no driver na leitura) | LOW | **Task de spike OU decisão de adiar (TD)** | M1: usar `func.ST_*` nativo (sem GeoAlchemy2). Se equipe quiser o tipo ORM → spike que prova read/write de Geometry async com aiomysql, ou TD `post_launch_quarter`. |
| LOW-2 | Como testar spatial sem MySQL local (SQLite não tem `ST_*`) | LOW→resolvido | **Task** | Testes espaciais com `@pytest.mark.mysql` (padrão Phase 5 confirmado); piso/cobertura-por-nome em SQLite. Critério: `test_spatial.py` roda 1 ponto dentro + 1 fora no CI MySQL. |
| LOW-3 | Formato exato de polígono aceito no M1 (GeoJSON Polygon vs WKT vs coordenadas) | LOW | **Task** | M1 aceita GeoJSON `Polygon` (D-01 + discretion). Critério: endpoint aceita GeoJSON, valida (shapely/ST_IsValid), persiste via ST_GeomFromGeoJSON. WKT é secundário. |
| LOW-4 | SPATIAL INDEX em polígono nullable (Pitfall 1) | MEDIUM | **Task OU TD** | M1: sem índice + TD `post_launch_quarter` (A1), OU tabela `neighborhood_polygons` NOT NULL. Decidir no plan. |
| LOW-5 | Reação a aumento de piso retroativo | LOW | **TD ou decisão no discuss** | Sinalizar (não bloquear) + TD; confirmar com dono. |

## Metadata

**Confidence breakdown:**
- MySQL spatial (funções, SRID, índice): HIGH — docs oficiais MySQL 8.0 verificadas.
- Modelagem (cobertura/preço/config): HIGH — entidades.md + código existente + RN-003/015.
- Validação de piso: HIGH — RN-015 + padrão de erro RFC-7807 do projeto.
- Integração espacial em SQLAlchemy 2 async + aiomysql: MEDIUM/LOW — combinação pouco documentada (LOW-1).
- Estratégia de teste: HIGH — padrão `@pytest.mark.mysql` já estabelecido na Phase 5.

**Research date:** 2026-06-10
**Valid until:** ~2026-07-10 (MySQL spatial é estável; reavaliar só se mudar versão do MySQL ou adotar GeoAlchemy2)
