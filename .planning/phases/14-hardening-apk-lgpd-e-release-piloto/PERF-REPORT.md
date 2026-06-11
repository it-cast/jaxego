# Phase 14 — Relatório de Performance (REQ-050)

**Data:** 2026-06-11 (autopilot) · **Status:** orçamento configurado; validação runtime no CI

## Orçamento (config.json `performance_budget` + tooling/ci/lighthouserc.json)
| Métrica | Alvo | Onde é medido |
|---|---|---|
| LCP | < 2500 ms (4G) | Lighthouse CI (`lighthouserc.json`) |
| INP | < 200 ms | Lighthouse CI |
| CLS | < 0.1 | Lighthouse CI |
| First paint | < 1500 ms | Lighthouse CI |
| Bundle main (gzip) | < 400 KB | build + bundlesize |
| Bundle vendor (gzip) | < 800 KB | build |
| p95 criar-entrega / aceitar-oferta | < 200 ms | load test sintético (runner) |

## Estado medido localmente (build de produção)
- Build de produção do `apps/web` **verde** (jobs anteriores). Chunks lazy confirmados (mapa MapLibre
  fora do main desde a Phase 9; tela 22 ~6.7 KB transfer; telas de governança lazy).
- Warning conhecido de bundle do `maplibre-gl` é **pré-existente** e isolado em rota lazy (não entra no
  caminho crítico/LCP, que é a timeline — decisão da Phase 9).

## Validação runtime (CI / runner)
- Lighthouse CI e bundlesize rodam no job `web` do `.github/workflows/ci.yml` (Phase 14). LCP/INP/CLS
  reais e p95 sob carga **exigem runner/ambiente** — não reproduzíveis no dev local Windows.
- **Pendência (checklist UAT):** rodar o pipeline `web` num PR/tag e anexar o relatório Lighthouse +
  resultado do load test de p95. Violação → TD com urgency_class.

## TD
- **TD-14-03** (`pre_launch_medium`): anexar relatório Lighthouse + p95 reais de um run de CI antes do
  go-live (validação runtime do orçamento de performance).
