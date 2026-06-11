---
phase: 9
phase_name: Execução, comprovação, tracking público e notificações
milestone: MS-03
date: 2026-06-10
auto_generated: true
pending_review: true
---

# Retrospectiva — Phase 9: Execução, comprovação, tracking público e notificações

## Dados objetivos (capturados automaticamente)
- Tasks: 19 (T-01..T-19) — a maior phase do projeto
- Plan revisions: 0 (gate 3 PASS 1ª iteração — 25/25 skills)
- Verification retries: 1 fix ao vivo (revision id 0008 longo demais)
- Gates bypassados: 0
- Tech debt adicionado: TD-019 (tiles OSM), TD-020 (background polling)
- Skills citadas: 25 (matriz UI + offline-first + push + file-upload + trust-safety + performance-web-vitals + ionic + visual-regression + senior-quality-bar)
- Commits: ~18 (f952df5..0c67b5a)
- Testes: 326 backend not-mysql + 5 mysql + 121 frontend
- Libs: piexif (dev), maplibre-gl

## Auto-observações
- O **achado crítico do research** (comprovação PRESERVA EXIF GPS, oposto do KYC que faz strip) evitou um bug sério: reusar o reprocess do KYC cegamente teria destruído o GPS antes da validação de geofence. Research que lê o código existente paga.
- Mapa MapLibre LAZY (chunk separado 231KB, fora do main 163KB) → LCP é a timeline, não o mapa. performance-web-vitals aplicada.
- Tracking público sem auth com serializer que minimiza PII por estado (RN-013) — endereço só após COLETADA.
- **A verificação ao vivo pegou mais um bug de deploy:** revision id da 0008 (34 chars) estourava alembic_version VARCHAR(32) — DDL aplicava mas stamp falhava. Mock/SQLite nunca pegaria (SQLite não tem o limite). 3º bug de migration pego ao vivo no projeto (0006 downgrade FK, 0008 revision id).
- DEC-002 (mapa ao vivo, decisão do dono no início) entregue: delivery_locations + polling + MapLibre.

## Qualitativo (preencher manualmente — edite este arquivo)

### 1. O que funcionou bem?
[AUTO: preencher depois] — Hipótese: research leu o código (EXIF KYC vs comprovação); mapa lazy; gate 3 PASS de primeira numa phase de 19 tasks.

### 2. O que atrapalhou?
[AUTO: preencher depois] — Hipótese: revision id longo só pega em MySQL; phase enorme.

### 3. O que faltou (skill, contexto, ferramenta)?
[AUTO: preencher depois] — Considerar: lint de revision id ≤32 chars; rodar @mysql + alembic no CI; device real para EXIF do Capacitor.

### 4. Claude entendeu o que você queria? (1-5)
[AUTO: preencher depois]

### 5. Qualidade do código entregue? (1-5)
[AUTO: preencher depois]
