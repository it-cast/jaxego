# /gsd-metrics — fechar fase com captura de dados

## Quando invocar

Ao final de uma fase (gate 7 passou, feature em produção). Antes de começar a próxima fase.

## Inputs

- `phase_id`: string curta (ex: `phase-12-orders-api`, `phase-03-push-setup`)
- Opcional: já ter `.planning/PLAN.md` e `.planning/STATE.md` do ciclo

## O que o workflow faz

1. **Valida pré-condições**
   - `.planning/PLAN.md` existe
   - Todas as tasks marcadas como completadas (`- [x]`) OU há justificativa escrita em `STATE.md` para as não completadas
   - Gate 7 está passado no `STATE.md` (ou bypass documentado com `--reason`)

2. **Gera retrospectiva**
   - Copia `.planning/RETROSPECTIVE.md.template` para `.planning/retros/<phase_id>.md`
   - Substitui `{{ phase_id }}`, `{{ closed_at }}`, `{{ duration_days }}` com dados reais
   - **Pausa** — espera humano preencher os `<FILL>`

3. **Após retrospectiva preenchida**
   - Roda `bin/collect-metrics.sh <phase_id>`
   - Anexa rascunho no `.planning/METRICS.md`
   - Abre o arquivo para o humano conferir e preencher os campos qualitativos (copiando da retrospectiva)

4. **Commit atômico**
   - `git add .planning/METRICS.md .planning/retros/<phase_id>.md`
   - Mensagem padrão: `metrics: close <phase_id>`

5. **Exporta telemetria (opcional)**
   - Pergunta se o humano quer exportar a entrada em formato anonimizado
   - Se sim, roda `bin/export-telemetry.sh <phase_id>`
   - Lembra humano de revisar manualmente antes de compartilhar

## Fluxo conversacional

```
Humano: /gsd-metrics phase-12-orders-api

Claude: Fechando phase-12-orders-api. Validando pré-condições...
  ✓ PLAN.md existe
  ✓ 7/7 tasks completadas
  ✓ Gate 7 passado

Gerando retrospectiva em .planning/retros/phase-12-orders-api.md...
Preencha os <FILL> quando puder (leva ~15 min). Quando terminar, me chame de volta.

---

[tempo depois]

Humano: retro preenchida

Claude: Vou coletar as métricas automáticas agora.
  [roda bin/collect-metrics.sh]
  ✓ Rascunho anexado em .planning/METRICS.md

Abra o arquivo e preencha os 3 campos qualitativos (what_worked/hurt/missing) 
copiando da retrospectiva + os 2 scores (1-5). Quando terminar, me avise.

---

Humano: feito

Claude: Fazendo commit...
  [git add + commit]
  ✓ "metrics: close phase-12-orders-api"

Quer exportar telemetria anonimizada desta fase? (util para compartilhar com autor do framework)
  [ ] Sim — exportar para /tmp/gsd-telemetry-<ts>.json
  [ ] Não — apenas manter local
```

## Política anti-teatro

Este workflow **pausa** deliberadamente em dois pontos (retro + campos qualitativos).
Não existe "fechar fase automaticamente" — a ausência de fricção aqui levaria a métricas vazias
("what_worked: n/a, what_hurt: n/a") que não informam nada.

A fricção de 15 minutos é o preço de dados que valem alguma coisa. Se não vale 15 min no fim
de uma fase de dias/semanas, a métrica que seria gerada também não vale nada.

## Quando dispensar

- Fases triviais (< 4h de trabalho, 1-2 tasks, mudança mecânica) — skip inteiro, documentar em STATE.md
- Hotfix emergencial — roda retrospectiva depois (dentro de 48h); métrica fica marcada `was_hotfix: true`

## Integração

- **Dashboard consolidado:** `/gsd-metrics-dashboard` (workflow separado, roda análise em cima de `.planning/METRICS.md` e mostra tendências — ex: "taxa de fix_iterations caiu de 2.4 para 0.8 nas últimas 5 fases")
- **Export em lote:** `bin/export-telemetry.sh` sem argumento exporta todas as entradas

## Checklist para este workflow

- [ ] `.planning/PLAN.md` existe
- [ ] Tasks completadas ou justificadas
- [ ] Gate 7 passado ou bypass documentado
- [ ] Retrospectiva gerada e preenchida
- [ ] Rascunho em METRICS.md revisado e campos qualitativos preenchidos
- [ ] Commit realizado
- [ ] Decisão sobre export de telemetria tomada
