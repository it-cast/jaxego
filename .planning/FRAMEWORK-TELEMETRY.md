# Framework Telemetry — medição do próprio gsd-framework

> Distinto de METRICS.md (que mede o projeto). Este arquivo mede se o **framework**
> entrega o que promete: Gate 8 bloqueia o que importa? Paralelismo compensa?
> /gsd:go reduz fricção? Skills novas são aplicadas?
>
> Os campos `<FILL>` em "interpretacao_humana" são o que fecha o gap de field data.
> Sem eles, temos números; com eles, temos validação.
>
> Exporte anonimizado com: bin/collect-framework-telemetry.sh --export

## Snapshot 2026-06-10T18:01:01Z

```yaml
gate8_senior_quality_bar:
  phases_avaliadas: 0
  fail_block_total: 0      # quanto a barra BLOQUEOU (valor entregue)
  fail_debt_total: 0        # quanto virou dívida consciente

gate8_enforcement_script:           # v0.9.6 — estado REAL hoje, via gsd-tools verify quality-bar
  phases_que_passariam: 0
  phases_bloqueadas_hoje: 0   # >0 ao fechar milestone = dívida não contabilizada ou FAIL-BLOCK aberto

wave_dispatcher:
  execucoes_paralelas: 0
  particoes_via_codigo: 0    # v0.9.6 — waves particionadas por gsd-tools partition (determinístico)
  execucoes_serial: 0
  taxa_rebaixamento_serial: n/a   # alto = heurística conservadora ou phases monocamada
  conflitos_de_lease: 0             # >0 = planner não declarou implícitos

gsd_go:
  referencias_uso: 0

skills_v095_aplicacao:
  fastapi-production-patterns: citada_em_15_planos
  github-actions-ci: citada_em_3_planos
  data-tables-ux: citada_em_2_planos
  search-filter-ux: citada_em_1_planos
  parallel-orchestration: citada_em_0_planos
  senior-quality-bar: citada_em_14_planos

interpretacao_humana:
  gate8_vale_a_pena: "<FILL — fail_block pegou algo que teria ido a produção? sim/não/exemplo>"
  paralelismo_compensou: "<FILL — wall-clock real foi menor que serial? valeu o custo de tokens?>"
  go_reduziu_friccao: "<FILL — você usou /gsd:go ou voltou aos comandos granulares? por quê?>"
  skills_novas_uteis: "<FILL — alguma skill nova mudou uma decisão de código? qual?>"
```

## Snapshot 2026-06-10T20:32:10Z

```yaml
gate8_senior_quality_bar:
  phases_avaliadas: 0
  fail_block_total: 0      # quanto a barra BLOQUEOU (valor entregue)
  fail_debt_total: 0        # quanto virou dívida consciente

gate8_enforcement_script:           # v0.9.6 — estado REAL hoje, via gsd-tools verify quality-bar
  phases_que_passariam: 0
  phases_bloqueadas_hoje: 0   # >0 ao fechar milestone = dívida não contabilizada ou FAIL-BLOCK aberto

wave_dispatcher:
  execucoes_paralelas: 0
  particoes_via_codigo: 0    # v0.9.6 — waves particionadas por gsd-tools partition (determinístico)
  execucoes_serial: 0
  taxa_rebaixamento_serial: n/a   # alto = heurística conservadora ou phases monocamada
  conflitos_de_lease: 0             # >0 = planner não declarou implícitos

gsd_go:
  referencias_uso: 2

skills_v095_aplicacao:
  fastapi-production-patterns: citada_em_18_planos
  github-actions-ci: citada_em_3_planos
  data-tables-ux: citada_em_5_planos
  search-filter-ux: citada_em_1_planos
  parallel-orchestration: citada_em_0_planos
  senior-quality-bar: citada_em_18_planos

interpretacao_humana:
  gate8_vale_a_pena: "<FILL — fail_block pegou algo que teria ido a produção? sim/não/exemplo>"
  paralelismo_compensou: "<FILL — wall-clock real foi menor que serial? valeu o custo de tokens?>"
  go_reduziu_friccao: "<FILL — você usou /gsd:go ou voltou aos comandos granulares? por quê?>"
  skills_novas_uteis: "<FILL — alguma skill nova mudou uma decisão de código? qual?>"
```

## Snapshot 2026-06-10T21:14:05Z

```yaml
gate8_senior_quality_bar:
  phases_avaliadas: 0
  fail_block_total: 0      # quanto a barra BLOQUEOU (valor entregue)
  fail_debt_total: 0        # quanto virou dívida consciente

gate8_enforcement_script:           # v0.9.6 — estado REAL hoje, via gsd-tools verify quality-bar
  phases_que_passariam: 0
  phases_bloqueadas_hoje: 0   # >0 ao fechar milestone = dívida não contabilizada ou FAIL-BLOCK aberto

wave_dispatcher:
  execucoes_paralelas: 0
  particoes_via_codigo: 0    # v0.9.6 — waves particionadas por gsd-tools partition (determinístico)
  execucoes_serial: 0
  taxa_rebaixamento_serial: n/a   # alto = heurística conservadora ou phases monocamada
  conflitos_de_lease: 0             # >0 = planner não declarou implícitos

gsd_go:
  referencias_uso: 3

skills_v095_aplicacao:
  fastapi-production-patterns: citada_em_18_planos
  github-actions-ci: citada_em_3_planos
  data-tables-ux: citada_em_5_planos
  search-filter-ux: citada_em_1_planos
  parallel-orchestration: citada_em_0_planos
  senior-quality-bar: citada_em_18_planos

interpretacao_humana:
  gate8_vale_a_pena: "<FILL — fail_block pegou algo que teria ido a produção? sim/não/exemplo>"
  paralelismo_compensou: "<FILL — wall-clock real foi menor que serial? valeu o custo de tokens?>"
  go_reduziu_friccao: "<FILL — você usou /gsd:go ou voltou aos comandos granulares? por quê?>"
  skills_novas_uteis: "<FILL — alguma skill nova mudou uma decisão de código? qual?>"
```

## Snapshot 2026-06-10T23:06:36Z

```yaml
gate8_senior_quality_bar:
  phases_avaliadas: 0
  fail_block_total: 0      # quanto a barra BLOQUEOU (valor entregue)
  fail_debt_total: 0        # quanto virou dívida consciente

gate8_enforcement_script:           # v0.9.6 — estado REAL hoje, via gsd-tools verify quality-bar
  phases_que_passariam: 0
  phases_bloqueadas_hoje: 0   # >0 ao fechar milestone = dívida não contabilizada ou FAIL-BLOCK aberto

wave_dispatcher:
  execucoes_paralelas: 0
  particoes_via_codigo: 0    # v0.9.6 — waves particionadas por gsd-tools partition (determinístico)
  execucoes_serial: 0
  taxa_rebaixamento_serial: n/a   # alto = heurística conservadora ou phases monocamada
  conflitos_de_lease: 0             # >0 = planner não declarou implícitos

gsd_go:
  referencias_uso: 4

skills_v095_aplicacao:
  fastapi-production-patterns: citada_em_22_planos
  github-actions-ci: citada_em_3_planos
  data-tables-ux: citada_em_7_planos
  search-filter-ux: citada_em_2_planos
  parallel-orchestration: citada_em_0_planos
  senior-quality-bar: citada_em_25_planos

interpretacao_humana:
  gate8_vale_a_pena: "<FILL — fail_block pegou algo que teria ido a produção? sim/não/exemplo>"
  paralelismo_compensou: "<FILL — wall-clock real foi menor que serial? valeu o custo de tokens?>"
  go_reduziu_friccao: "<FILL — você usou /gsd:go ou voltou aos comandos granulares? por quê?>"
  skills_novas_uteis: "<FILL — alguma skill nova mudou uma decisão de código? qual?>"
```
