# RECONCILIATION — Phase 6: Área operável (bairros, config, cobertura e tabela de frete)

**Data:** 2026-06-10
**Método:** 5 PLANs/UI-SPEC/RESEARCH (prometido) × código real + verificação ao vivo contra MySQL 8

---

## Prometido vs. Entregue

| Área | Prometido | Real | Status |
|---|---|---|---|
| Schema espacial | migration 0005: neighborhoods_catalog (POLYGON nullable SRID 4326), courier_coverage_areas, courier_pricing_tables, couriers+online/max_concurrent | `0005_area_operable` | ✅ **verificada ao vivo (aplica + reversível)** |
| Espacial nativo | ST_* via SQL Core (não GeoAlchemy2), helper de eixo lat-first | `app/neighborhoods/spatial.py` | ✅ |
| Catálogo de bairros (ADR-006) | CRUD admin, polígono opcional GeoJSON validado (shapely+ST_GeomFromGeoJSON), AreaScoped 404 | service + router /v1/neighborhoods | ✅ |
| Config da área (F-08) | AreaConfig Pydantic tipada (kyc_level/piso/geofence/timeouts/retorno) + audit before/after | substitui JSON cru | ✅ |
| Cobertura (RN-003) | coleta E entrega, exclusões | courier_coverage_areas | ✅ |
| Tabela de frete (RN-015) | bairro OU km, % retorno, valida PISO citando o piso | service + validação | ✅ |
| Online/offline/busy | só active liga; busy derivado | couriers + rotas self-only | ✅ |
| Elegibilidade ponto-em-polígono | ST_Contains decide elegibilidade | point_in_polygon | ✅ **verificado ao vivo: dentro→ELEGÍVEL, fora→não; + 2 testes asseverando** |
| Frontend | admin tela 21 (config + catálogo + jx-data-table); entregador tela 10 (cobertura+preços+toggle) | implementado | ✅ |

---

## Verificação ao vivo (MySQL 8 real)
| Check | Resultado |
|---|---|
| `alembic upgrade head` (0001→0005) + reversibilidade | ✅ aplica e reverte |
| Coluna polygon | ✅ POLYGON SRID 4326 |
| ST_Contains ponto-em-polígono | ✅ dentro (Pádua)→1 ELEGÍVEL, fora (Rio)→0 não elegível |
| `pytest -m mysql` (incl. 2 spatial reais) | ✅ spatial 2 passed (após remover skip) |
| `pytest -m "not mysql"` (backend) | ✅ 206 passed |
| Frontend (ng build/lint/test) | ✅ 160.96 kB gzip, lint limpo, 65 testes, zero hardcode |

---

## Critérios de aceite do ROADMAP
| Critério | Resultado |
|---|---|
| Ponto dentro/fora de polígono decide elegibilidade | ✅ verificado ao vivo + 2 testes regressão (`5b8c273`) |
| Preço abaixo do piso → rejeição citando o piso (RN-015) | ✅ (SQLite + UI) |
| Cobertura coleta E entrega (RN-003) | ✅ |
| Wireframe-contract 10, 17, 18, 21 | ✅ (17/18 migrados para jx-data-table) |

---

## Desvios (auto-fixados)
1. **Rule 1 (bug):** `DELETE /v1/neighborhoods/{id}` (204) com `-> None` quebrava criação do app (`response_model` inferido) → `response_model=None` explícito.
2. **Rule 2 (segurança):** rotas do entregador usam self-only (`Courier.user_id == token` + area scope → 404) em vez de `require_role("courier")` — o role "courier" não existe no `resolve_role`; a sugestão literal deixaria as rotas inseguras/inacessíveis.
3. Test quality: 2 testes espaciais removidos do skip → asseveram contra MySQL (`5b8c273`).

## Gates
| Gate | Status |
|---|---|
| Gate 2 (UI-SPEC) | ✅ zero token novo, 4 componentes (jx-data-table etc.) |
| Gate 3 (Skills) | ✅ PASS após +senior-quality-bar (FLAG→PASS) |
| Gate 4 | N/A (sem PII/risco alto) — `## Security & Validation Notes` cobrem validação espacial/RBAC/audit |
| Gate 5 (Integration) | N/A (integration_check:false) |
| Gate 6 (Reconciliation) | ✅ este documento |
| Gate 7 (tests+lint) | ✅ 206+spatial backend, 65 frontend, ruff/pyright/ng lint limpos |
| Gate 8 (senior-quality-bar) | ✅ sem N+1 (queries em lote), binds parametrizados no SQL espacial, RBAC 404, validação anti-DoS de GeoJSON |

## Pendências / follow-up (não-bloqueantes)
- **TD-017:** SPATIAL INDEX não criado (polígono nullable exige NOT NULL) — M1 sem índice espacial; reavaliar >100 bairros/área (post_launch_quarter).
- **TD-018:** aumento de piso retroativo só sinaliza, não bloqueia tabelas existentes (post_launch_quarter).
- SUG-008/009 registradas.
