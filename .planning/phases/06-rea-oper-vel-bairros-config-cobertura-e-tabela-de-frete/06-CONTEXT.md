# Phase 6: Área operável — bairros, config, cobertura e tabela de frete - Context

**Gathered:** 2026-06-10 (modo --auto, decisões recomendadas)
**Status:** Ready for planning

<domain>
## Phase Boundary

Torna a **área operável**: o admin de área cura o **catálogo de bairros** (nome + polígono opcional, inclui informais) e configura as **regras locais** (nível de KYC exigido, piso de frete por km/entrega, raio de geofence, timeouts de despacho, política de retorno); o entregador define sua **cobertura** (bairros onde atende — vale para coleta E entrega, RN-003) e sua **tabela de frete** (por bairro OU por km, respeitando o piso da área — RN-015), e alterna **online/offline/busy**. Internamente tudo vira polígono espacial (POINT/POLYGON no MySQL 8), e a elegibilidade por ponto-em-polígono fica pronta para o despacho. **Não** entrega despacho/ofertas (Phase 8), nem criação de entregas (Phase 7) — só deixa a área e os entregadores prontos para operar.
</domain>

<decisions>
## Implementation Decisions

### Catálogo de bairros (ADR-006)
- **D-01:** `neighborhoods_catalog` por área, curado pelo admin local: nome + polígono OPCIONAL (GeoJSON/WKT → tipo espacial MySQL). Inclui bairros informais. Modo default da área = `neighborhood` (interior). Internamente tudo vira polígono; bairro sem polígono ainda funciona por nome (polígono trava expansão a cidades grandes mas é opcional no M1). [auto] travado por ADR-006.
- **D-02:** CRUD de bairros no painel do admin de área (tela 21), escopado por área (RBAC + AreaScoped). [auto].

### Config da área (F-08)
- **D-03:** Admin de área configura: nível de validação exigido (simples/completa — alimenta a Phase 5), piso de frete (por km e por entrega), raio de geofence (m), timeouts de despacho (oferta default 20s, janela favoritos default 60s — ADR-104/ADR-007), política de retorno (% sobre a corrida). Tudo em `areas` (estende a entidade da Phase 2). Mudanças sensíveis → audit_log. [auto] (F-08 passo 3, entidades Área).

### Cobertura do entregador (RN-003)
- **D-04:** `courier_coverage_areas` — bairros do catálogo onde o entregador atende, com exclusões. Vale para coleta E entrega (RN-003). Elegibilidade exige cobertura nos DOIS pontos; exclusões vetam nos dois. [auto] travado por RN-003/ADR-006.

### Tabela de frete do entregador (RN-015)
- **D-05:** `courier_pricing_tables` — linhas por bairro OU faixas por km, com % de retorno. Respeita PISO da área (rejeita preço abaixo do piso com mensagem citando o piso). A plataforma NUNCA fixa o preço — só impõe piso e calcula sugestão. [auto] travado por RN-015.

### Online/offline/busy
- **D-06:** Entregador alterna online/offline; `busy` é derivado da carga (entregas ativas vs máx simultâneas). Só entregador `active` (KYC ok, Phase 5) pode ficar online. Estado de disponibilidade pronto para o despacho (Phase 8) consumir. [auto] (entidades couriers, REQ-018).

### Espacial (MySQL 8)
- **D-07:** Usar tipos espaciais nativos do MySQL 8 (POINT, POLYGON, SRID 4326) + índices espaciais; elegibilidade por `ST_Contains`/`ST_Within` (ponto-em-polígono). POINTs já existem em merchants/áreas; geofence usa raio (ST_Distance_Sphere) quando não há polígono. [auto] (stack.md, ADR-006, RN-005 geofence).

### Claude's Discretion
- Formato de entrada de polígono no admin (desenhar no mapa vs colar GeoJSON — M1 pode aceitar GeoJSON/coordenadas; desenho no mapa é nice-to-have).
- Estrutura exata das tabelas de cobertura/preço e índices espaciais.
- Como representar "por km" vs "por bairro" no schema de pricing.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Fluxo e regras
- `projeto/regras-negocio/fluxos.md` §F-08 (`:156-171`) — gestão da área pelo admin
- `projeto/regras-negocio/regras.md` — RN-003 (cobertura coleta E entrega), RN-015 (piso, entregador define preço), RN-005 (geofence)
- `projeto/regras-negocio/entidades.md` §Lado da oferta (courier_coverage_areas, courier_pricing_tables, neighborhoods_catalog), §Núcleo multi-área (Área — campos de config)
- `.planning/DECISIONS.md` — ADR-006 (cobertura por bairro/polígono), ADR-104/ADR-007 (timeouts)

### UI
- `projeto/wireframes/10-entregador-cobertura-precos.html`, `17-admin-area-dashboard.html`, `18-admin-area-entregadores.html`, `21-admin-area-config.html`
- Design system + componentes Phase 3/4/5 (apps/web)

### Backend a reusar
- `apps/api/app/areas/` (entidade Área + escopo — estender com config), `apps/api/app/couriers/` (Phase 5 — estender com cobertura/preço/disponibilidade), AreaScoped, audit_log
- Stack espacial: MySQL 8 spatial (`stack.md:13`)

### Requisitos
- `.planning/REQUIREMENTS.md` — REQ-003, REQ-016, REQ-017, REQ-018, REQ-002 (UI config), REQ-044 (parcial)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 2: entidade Área (estender com config: kyc_level, piso, geofence, timeouts, política retorno), AreaScoped, audit_log.
- Phase 5: couriers (estender com online/offline/busy, max_concurrent), painel admin de área.
- Phase 3/4/5: design system, data-tables, forms, mapa (MapLibre/OSM tiles — pode reaproveitar o que vier na Phase 9, mas aqui só visualização simples de bairro/polígono se necessário).

### Established Patterns
- `/v1` API, RFC-7807, AreaScoped, audit em ações sensíveis. aware UTC (TD-010).
- MySQL 8 spatial: POINT/POLYGON SRID 4326, índices espaciais, ST_Contains/ST_Within/ST_Distance_Sphere.

### Integration Points
- Cobertura + preço + disponibilidade + config alimentam o DESPACHO (Phase 8). Catálogo de bairros é usado por merchants (endereço→bairro) e couriers (cobertura).
- has_external_integration:false, has_payments:false, has_pii:false → sem Gate 4/5 pesados; foco em validação de input espacial e RBAC de área.
</code_context>

<specifics>
## Specific Ideas

- Piso da área é um GUARD-RAIL, não um preço: a plataforma nunca fixa o frete (RN-015). Rejeitar preço abaixo do piso com mensagem que cita o piso.
- Cobertura nos DOIS pontos (coleta E entrega) é a regra que evita recusa pós-aceite explodir (ADR-006).
- Polígono é opcional no M1 (bairro por nome funciona); polígono destrava cidades de geografia irregular.
- Testes espaciais: ponto dentro/fora de polígono decide elegibilidade (critério de aceite).
</specifics>

<deferred>
## Deferred Ideas

- Despacho/ofertas/cascata (consome cobertura+disponibilidade) — Phase 8.
- Criação de entregas (usa bairro do catálogo) — Phase 7.
- Mapa interativo de tracking (MapLibre) — Phase 9 (DEC-002).
- Desenho de polígono no mapa pelo admin — nice-to-have pós-M1 (M1 aceita GeoJSON/coordenadas).
</deferred>

---

*Phase: 06-rea-oper-vel-bairros-config-cobertura-e-tabela-de-frete*
*Context gathered: 2026-06-10*
