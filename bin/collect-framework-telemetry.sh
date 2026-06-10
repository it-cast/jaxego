#!/usr/bin/env bash
# bin/collect-framework-telemetry.sh
#
# Coleta métricas DO PRÓPRIO FRAMEWORK (não do projeto) — para responder
# "a v0.9.5 vale o que promete?" com dado, não raciocínio.
#
# Diferença para collect-metrics.sh:
#   collect-metrics.sh  → mede o PROJETO (duração, commits, bugs da feature)
#   este script         → mede o FRAMEWORK (gate 8, dispatcher, /gsd:go, skills novas)
#
# Uso:
#   bin/collect-framework-telemetry.sh            # snapshot acumulado do projeto atual
#   bin/collect-framework-telemetry.sh --export   # gera JSON anonimizado em /tmp
#
# Output:
#   .planning/FRAMEWORK-TELEMETRY.md  (append de snapshot datado)
#   /tmp/gsd-framework-telemetry-<ts>.json (se --export)
#
# Advisory. Nunca bloqueia. Falha silenciosa se artefatos ausentes.

set -u
cd "$( git rev-parse --show-toplevel 2>/dev/null || pwd )"

EXPORT=0
[[ "${1:-}" == "--export" ]] && EXPORT=1

PLANNING=".planning"
OUT="$PLANNING/FRAMEWORK-TELEMETRY.md"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

[[ -d "$PLANNING" ]] || { echo "Sem .planning/ — nada a medir."; exit 0; }

# ---------- Métrica 1: Gate 8 (Senior Quality Bar) ----------
# Quantos FAIL-BLOCK e FAIL-DEBT por phase (lê QUALITY-BAR.md das phases)
qb_files=$(find "$PLANNING/phases" -name "*QUALITY-BAR.md" 2>/dev/null)
qb_phases=$(printf '%s\n' "$qb_files" | grep -c '[^[:space:]]' || true); qb_phases=${qb_phases:-0}
if [[ -n "$qb_files" ]]; then
  qb_failblock=$(grep -rh "FAIL-BLOCK" $qb_files 2>/dev/null | grep -c . || true)
  qb_faildebt=$(grep -rh "FAIL-DEBT" $qb_files 2>/dev/null | grep -c . || true)
else
  qb_failblock=0; qb_faildebt=0
fi
qb_failblock=$(printf '%s' "${qb_failblock:-0}" | tr -d '[:space:]')
qb_faildebt=$(printf '%s' "${qb_faildebt:-0}" | tr -d '[:space:]')

# ---------- Métrica 2: Wave-dispatcher (paralelismo de execução) ----------
# Lê EXECUTION-LOG.md procurando os relatórios do dispatcher
exec_logs=$(find "$PLANNING/phases" -name "*EXECUTION-LOG.md" 2>/dev/null)
if [[ -n "$exec_logs" ]]; then
  disp_parallel=$(grep -rh "Modo: paralelo" $exec_logs 2>/dev/null | grep -c . || true)
  disp_serial=$(grep -rh "Modo: serial" $exec_logs 2>/dev/null | grep -c . || true)
  disp_conflicts=$(grep -rhoE "Conflitos: [0-9]+" $exec_logs 2>/dev/null | grep -oE "[0-9]+" | paste -sd+ - 2>/dev/null | bc 2>/dev/null || true)
else
  disp_parallel=0; disp_serial=0; disp_conflicts=0
fi
disp_parallel=$(printf '%s' "${disp_parallel:-0}" | tr -d '[:space:]')
disp_serial=$(printf '%s' "${disp_serial:-0}" | tr -d '[:space:]')
disp_conflicts=$(printf '%s' "${disp_conflicts:-0}" | tr -d '[:space:]')
disp_total=$((disp_parallel + disp_serial))
disp_downgrade_pct="n/a"
if [[ $disp_total -gt 0 ]]; then
  disp_downgrade_pct=$(python3 -c "print(f'{$disp_serial/$disp_total*100:.0f}%')" 2>/dev/null || echo "n/a")
fi

# ---------- Métrica 2b (v0.9.6): enforcement por script ----------
# Gate 8 por código: roda verify quality-bar em cada phase com QUALITY-BAR.md
# e conta quantas passariam/bloqueariam HOJE (lê o estado real, não auto-relato).
GSD_TOOLS=".claude/get-shit-done/bin/gsd-tools.cjs"
g8_pass=0; g8_block=0
if [[ -f "$GSD_TOOLS" && -n "$qb_files" ]]; then
  while IFS= read -r qbf; do
    [[ -z "$qbf" ]] && continue
    pnum=$(basename "$(dirname "$qbf")" | grep -oE '^[0-9]+' || true)
    [[ -z "$pnum" ]] && continue
    if node "$GSD_TOOLS" verify quality-bar "$pnum" 2>/dev/null | grep -q '"passed": true'; then
      g8_pass=$((g8_pass+1))
    else
      g8_block=$((g8_block+1))
    fi
  done <<< "$qb_files"
fi
# Partition determinístico: quantas waves usaram gsd-tools partition (logs citam)
part_uses=$(grep -rh "gsd-tools.*partition\|parallel_viable" $exec_logs 2>/dev/null | grep -c . || true)
part_uses=$(printf '%s' "${part_uses:-0}" | tr -d '[:space:]')

# ---------- Métrica 3: /gsd:go (entrada única) ----------
# Conta no histórico de sessão / git commits referência a go vs comandos granulares
go_uses=$(grep -rh "gsd:go\|/gsd-go\|workflow: go" "$PLANNING" 2>/dev/null | grep -c . || true); go_uses=${go_uses:-0}

# ---------- Métrica 4: Aplicação das skills v0.9.5 ----------
# Skills novas citadas em PLAN vs detectadas como aplicadas (heurística por import/keyword)
new_skills=("fastapi-production-patterns" "github-actions-ci" "data-tables-ux" "search-filter-ux" "parallel-orchestration" "senior-quality-bar")
skill_report=""
for sk in "${new_skills[@]}"; do
  cited=$(grep -rh "$sk" $PLANNING/phases/*/PLAN.md 2>/dev/null | grep -c . || true)
  cited=$(printf '%s' "${cited:-0}" | tr -d '[:space:]')
  skill_report="${skill_report}  ${sk}: citada_em_${cited}_planos\n"
done

# ---------- Snapshot ----------
SNAP=$(cat <<EOF

## Snapshot $TS

\`\`\`yaml
gate8_senior_quality_bar:
  phases_avaliadas: $qb_phases
  fail_block_total: $qb_failblock      # quanto a barra BLOQUEOU (valor entregue)
  fail_debt_total: $qb_faildebt        # quanto virou dívida consciente

gate8_enforcement_script:           # v0.9.6 — estado REAL hoje, via gsd-tools verify quality-bar
  phases_que_passariam: $g8_pass
  phases_bloqueadas_hoje: $g8_block   # >0 ao fechar milestone = dívida não contabilizada ou FAIL-BLOCK aberto

wave_dispatcher:
  execucoes_paralelas: $disp_parallel
  particoes_via_codigo: $part_uses    # v0.9.6 — waves particionadas por gsd-tools partition (determinístico)
  execucoes_serial: $disp_serial
  taxa_rebaixamento_serial: $disp_downgrade_pct   # alto = heurística conservadora ou phases monocamada
  conflitos_de_lease: $disp_conflicts             # >0 = planner não declarou implícitos

gsd_go:
  referencias_uso: $go_uses

skills_v095_aplicacao:
$(echo -e "$skill_report")

interpretacao_humana:
  gate8_vale_a_pena: "<FILL — fail_block pegou algo que teria ido a produção? sim/não/exemplo>"
  paralelismo_compensou: "<FILL — wall-clock real foi menor que serial? valeu o custo de tokens?>"
  go_reduziu_friccao: "<FILL — você usou /gsd:go ou voltou aos comandos granulares? por quê?>"
  skills_novas_uteis: "<FILL — alguma skill nova mudou uma decisão de código? qual?>"
\`\`\`
EOF
)

if [[ ! -f "$OUT" ]]; then
  cat > "$OUT" <<HDR
# Framework Telemetry — medição do próprio gsd-framework

> Distinto de METRICS.md (que mede o projeto). Este arquivo mede se o **framework**
> entrega o que promete: Gate 8 bloqueia o que importa? Paralelismo compensa?
> /gsd:go reduz fricção? Skills novas são aplicadas?
>
> Os campos \`<FILL>\` em "interpretacao_humana" são o que fecha o gap de field data.
> Sem eles, temos números; com eles, temos validação.
>
> Exporte anonimizado com: bin/collect-framework-telemetry.sh --export
HDR
fi

echo "$SNAP" >> "$OUT"
echo "✓ Snapshot de framework-telemetry adicionado em $OUT"
echo "  Preencha os campos interpretacao_humana — são eles que validam a v0.9.5."

# ---------- Export anonimizado ----------
if [[ $EXPORT -eq 1 ]]; then
  JOUT="/tmp/gsd-framework-telemetry-$(date +%Y%m%d-%H%M%S).json"
  python3 - "$qb_phases" "$qb_failblock" "$qb_faildebt" "$disp_parallel" "$disp_serial" "$disp_conflicts" "$go_uses" "$g8_pass" "$g8_block" "$part_uses" "$JOUT" <<'PYEOF'
import json, sys
keys=["qb_phases","qb_failblock","qb_faildebt","disp_parallel","disp_serial","disp_conflicts","go_uses","gate8_script_pass","gate8_script_block","partition_uses"]
vals=sys.argv[1:11]
out=sys.argv[11]
data={"framework_version":"0.9.6","metrics":{k:int(v) for k,v in zip(keys,vals)}}
open(out,"w").write(json.dumps(data,indent=2))
print(f"✓ Export anonimizado: {out}")
PYEOF
fi
