---
phase: 6
phase_name: Área operável — bairros, config, cobertura e tabela de frete
milestone: MS-02
date: 2026-06-10
auto_generated: true
pending_review: true
---

# Retrospectiva — Phase 6: Área operável

## Dados objetivos (capturados automaticamente)
- Plans: 5 (06-01..06-05) · Tasks: 12
- Plan revisions: 0 (gate 3 FLAG por senior-quality-bar → corrigido → PASS)
- Verification retries: 1 (testes espaciais skip → asseveram contra MySQL)
- Gates bypassados: 0
- Tech debt adicionado: TD-017 (spatial index nullable), TD-018 (piso retroativo)
- Skills citadas: 15+ (matriz UI + saas-dashboard + data-tables + mysql-schema-design spatial + senior-quality-bar)
- Commits: ~20 (07da40c..5b8c273)
- Testes: 206 backend not-mysql + spatial mysql + 65 frontend
- Libs: shapely

## Auto-observações
- Decisão técnica importante do research: **ST_* nativo via SQL Core, não GeoAlchemy2** (async+aiomysql mal suportado) — acertou; spatial funcionou limpo.
- Research pegou imprecisões de schema antes do código: merchants.lat/lng Float (não POINT), Area.config JSON cru sem validação/audit, gotcha de eixo lat/lng — todas endereçadas.
- Multi-plan (5 planos) com zero overlap de arquivos por wave funcionou bem para organizar back/front.
- **Lição recorrente:** o executor deixou testes espaciais como pytest.skip; a verificação ao vivo expôs isso e os testes viraram asserções reais. Reforça: "teste marcado mysql que só faz skip" não protege contra regressão.
- Bons catches do executor: bug do 204 response_model; auth self-only em vez de role inexistente.

## Qualitativo (preencher manualmente — edite este arquivo)

### 1. O que funcionou bem?
[AUTO: preencher depois] — Hipótese: research antecipou gotchas de schema/espacial; multi-plan paralelo; ST_* nativo.

### 2. O que atrapalhou?
[AUTO: preencher depois] — Hipótese: spatial só testável em MySQL; testes skip que não asseveram.

### 3. O que faltou (skill, contexto, ferramenta)?
[AUTO: preencher depois] — Considerar: rodar -m mysql no dev loop para spatial; política de spatial index com volume.

### 4. Claude entendeu o que você queria? (1-5)
[AUTO: preencher depois]

### 5. Qualidade do código entregue? (1-5)
[AUTO: preencher depois]
