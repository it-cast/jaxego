---
name: north-star-vision
category: meta
description: Articular visão norte de produto (north star) que alinha o time e inspira decisões de design estratégicas. Inclui north-star metric.
---

# North Star Vision — Visão Norte

> Em projeto sem norte, toda decisão vira debate. Com norte, debate vira "isso nos aproxima ou afasta da estrela?"

## Quando esta skill é obrigatória

- `/gsd-bootstrap` em projeto novo (uma vez)
- Quando time discorda sobre prioridades sem critério objetivo
- Antes de discussão de pricing ou positioning

## North Star tem 2 partes

### Parte 1: Vision Statement (qualitativo, inspirador)

```
[VERBO INSPIRADOR] [PERSONA ESPECÍFICA] [JOB CRÍTICO]
em [TIME-FRAME AMBICIOSO] de modo que [OUTCOME TRANSFORMADOR].
```

Exemplo (Áugure):

> Permitir que **empresários PME brasileiros** **validem ideias de negócio com calibração pública** em **15 minutos** de modo que **decidam investir capital com confiança baseada em dado, não em chute**.

### Parte 2: North Star Metric (quantitativo, mensurável)

UMA métrica que captura valor entregue ao usuário. Não é vanity metric.

**Critérios da north-star metric:**
- Mede valor real para o usuário (não para o negócio diretamente)
- Aumentar essa métrica = produto está cumprindo sua visão
- Decompõe em sub-métricas operacionais
- É medida com frequência (semanal/mensal)

**Exemplos por tipo de produto:**

| Produto | North-star metric ruim | North-star metric boa |
|---|---|---|
| Spotify | Usuários ativos | Tempo total de música escutada |
| Airbnb | Reservas/mês | Noites reservadas |
| Slack | Mensagens enviadas | Daily active teams (>2 mensagens/dia) |
| Áugure | Simulações rodadas | Empresários que tomaram decisão investir/abandonar baseada em relatório |

## Processo

### 1. Articular vision statement

Workshop de 2-4 horas com fundadores. Tentar 5-10 versões. Cortar palavras genéricas:

❌ "Revolucionar a forma como empresas..."
✅ "Validar ideia de negócio em 15 minutos para PME brasileira"

### 2. Identificar north-star metric

3-5 candidatos. Para cada um, perguntar:
- Se essa métrica subir 10x, isso significa que estamos cumprindo a visão? (sim/não)
- Conseguimos medir essa métrica todo mês? (sim/não)
- A métrica pode ser hackeada sem entregar valor real? (sim/não — se sim, descarte)

Escolher 1.

### 3. Decompor north-star em input metrics

Exemplo Áugure:

```
North star: Empresários que tomaram decisão de investir/abandonar com base em relatório

Input metrics (drivers):
├── # de simulações concluídas/mês
├── % de simulações que viraram relatório lido
├── % de relatórios lidos que tiveram retorno positivo no NPS
└── # de empresários que voltaram para 2ª simulação
```

Cada input metric vira meta operacional.

### 4. Documentar e tornar visível

- Salvar em `docs/NORTH-STAR.md`
- Citar em `specs/project.yaml` no campo `north_star`
- Mostrar em todo `/gsd-progress` e `/gsd-milestone-summary`

## Anti-patterns

❌ Vision genérica "ser referência em..."
❌ Métrica que infla sem valor (ex: pageviews, signups)
❌ Múltiplas north-stars (= zero)
❌ Métrica vaga sem fórmula
❌ Definir e nunca medir

## Integração

- Vai em `specs/project.yaml > north_star` (capturado no /gsd-bootstrap)
- Citado em todo `/gsd-milestone-summary`
- Conecta com `meta/productivity-estimation` para mostrar progresso real
