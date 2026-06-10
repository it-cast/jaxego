---
name: productivity-estimation
category: meta
description: Calcular projeção solo-dev vs tempo real e gerar relatório de ganho de produtividade ao fechar milestone.
---

# Productivity Estimation — projeção e cálculo de ganho

> Skill consultada ao fechar milestone para calcular **ganho de produtividade** real do framework.
>
> Fórmula central: `ganho = estimativa_solo_dev_horas / tempo_real_horas`
>
> Exemplo Áugure v1.0: 24 semanas × 40h = 960h estimado vs 28h real = **34x** mais rápido.

---

## 1. Quando esta skill é consultada

- No `/gsd-milestone-summary` ao fechar milestone
- No `/gsd-bootstrap` para registrar projeção inicial em `specs/project.yaml`
- Quando humano pede "qual o ganho de produtividade desse projeto?"

---

## 2. Campos canônicos no `specs/project.yaml`

```yaml
project:
  # ... outros campos ...

  # Para cálculo de produtividade
  estimated_solo_dev_weeks: 24-30   # range estimado por humano (palpite informado)
  hours_per_week_assumed: 40        # default 40h/semana de trabalho dedicado
  # Resultado: 960-1200h estimadas para MVP solo dev sem framework
```

**Defaults razoáveis** se humano não preenche:

| Tipo de projeto | Solo-dev estimado |
|-----------------|-------------------|
| MVP simples (CRUD, 1 user type) | 8-12 semanas |
| MVP médio (auth, payment, admin) | 16-24 semanas |
| MVP complexo (multi-tenant, integrações, mobile + web) | 24-30 semanas |
| Plataforma B2B/SaaS completa | 30-50 semanas |
| Marketplace (2 lados, billing, webhooks) | 36-60 semanas |

---

## 3. Cálculo do ganho de produtividade

### 3.1 Tempo real trabalhado

Soma de `duration_hours` em todas as entradas de `.planning/METRICS.md` do milestone:

```bash
total_hours_real=$(awk '
  /^- phase:/ { in_entry=1 }
  /^  duration_hours:/ && in_entry {
    gsub(/[^0-9.]/, "", $2)
    sum += $2
    in_entry=0
  }
  END { print sum }
' .planning/METRICS.md)
```

### 3.2 Estimativa solo-dev

```bash
estimated_weeks=$(yq '.project.estimated_solo_dev_weeks' specs/project.yaml)
hours_per_week=$(yq '.project.hours_per_week_assumed' specs/project.yaml)

# Se range (ex: "24-30"), pega média
if [[ "$estimated_weeks" == *"-"* ]]; then
  low=${estimated_weeks%-*}
  high=${estimated_weeks#*-}
  estimated_weeks=$(( (low + high) / 2 ))
fi

estimated_hours=$((estimated_weeks * hours_per_week))
```

### 3.3 Ganho

```bash
ratio=$(echo "scale=1; $estimated_hours / $total_hours_real" | bc)
percent_saved=$(echo "scale=1; (1 - $total_hours_real / $estimated_hours) * 100" | bc)
```

---

## 4. Formato do relatório (em pt-BR)

```markdown
## 📊 Ganho de Produtividade — Milestone {milestone}

| Métrica | Valor |
|---------|-------|
| Tempo real trabalhado | {hours}h |
| Estimativa solo-dev (sem framework) | {estimated_weeks} semanas × {hpw}h/sem = {estimated_hours}h |
| **Ganho de produtividade** | **{ratio}x mais rápido** |
| Tempo poupado | {saved_hours}h ({percent_saved}%) |
| Phases concluídas | {N} |
| Tempo médio por phase | {avg_hours}h |

### Comparativo concreto

Se este projeto tivesse sido feito sem o gsd-framework:
- Estimativa: ~{estimated_weeks} semanas trabalhando solo
- Realidade: {total_hours_real}h ({equivalent_days} dias úteis a 8h/dia)

### Caveat honesto

A estimativa "solo-dev" é palpite humano calibrado, não dado controlado. Para validação rigorosa,
seria necessário rodar projeto similar sem framework como controle. O número aqui serve como
**proxy de magnitude**, não como métrica científica.
```

---

## 5. Anti-patterns a evitar

❌ **Não inflar estimativa solo-dev** para parecer mais produtivo. Estimativa deve ser palpite honesto pré-projeto.

❌ **Não contar tempo de descoberta + bootstrap** como "tempo de desenvolvimento". Esses são custos do framework.

❌ **Não somar tempo de Claude pensando** com tempo de humano trabalhando. `duration_hours` é wall-clock, inclui ambos.

❌ **Não comparar projetos heterogêneos.** Comparar v1.0 de projeto A com v1.0 de projeto B só faz sentido se complexidades batem.

✅ **Sempre exibir caveat** sobre a natureza de palpite da estimativa.

✅ **Capturar `estimated_solo_dev_weeks` no início** (no `/gsd-bootstrap`), antes de saber o resultado, para evitar viés retroativo.

---

## 6. Integração com `/gsd-milestone-summary`

O comando `/gsd-milestone-summary <milestone>` deve incluir esta seção no `SUMMARY.md` gerado.

Estrutura:

```markdown
# Milestone {milestone} — Sumário

## Visão geral
... (sumário existente) ...

## 📊 Ganho de Produtividade
... (formato da seção 4 acima) ...

## Phases concluídas
... (lista) ...
```
