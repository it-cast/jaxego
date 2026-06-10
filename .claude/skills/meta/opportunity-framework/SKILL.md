---
name: opportunity-framework
category: meta
description: Identificar, avaliar e priorizar oportunidades de feature/produto. Cobre 5 frameworks (RICE, ICE, Impact-Effort, Kano, Value-Complexity) com fórmulas, exemplos calculados, templates de scoring, anti-patterns e como integrar com ROADMAP. Resolve "tudo é prioridade" e priorização por opinião.
---

# Opportunity Framework — Priorização de Oportunidades

> "Tudo é prioridade" = nada é prioridade. Esta skill estrutura o processo de escolher o que vai e o que fica para depois.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-bootstrap` ao definir ROADMAP inicial | Decisão fundadora |
| `/gsd-discuss-phase` quando há múltiplas opções | Escolher entre alternativas |
| Início de cada milestone | Revisão de prioridades |
| Quando humano disser "vamos fazer X, Y, Z" | Sem critério explícito |
| Após `meta/journey-map` identificar oportunidades | Priorizar entre N opções |
| Pivot de produto | Repriorizar tudo |

## 2. Quando NÃO usar

- Phase obrigatória por compliance (LGPD, fiscal)
- Bug fix crítico (não é "oportunidade", é manutenção)
- Phase já priorizada por OKR/contrato

---

## 3. Os 5 frameworks (escolher 1 por contexto)

### 3.1 Impact × Effort (default mais usado)

```
            Alto Impacto
                │
    QUICK WIN   │   BIG BET
    (faça já)   │   (avalie ROI)
                │
────────────────┼────────────────
                │
    LIXEIRA     │   ESTRATÉGICO
    (descarte)  │   (planeje fase)
                │
            Baixo Impacto
   ←──Baixo Esforço     Alto Esforço──→
```

**Como aplicar:**

1. Listar oportunidades (10-30)
2. Para cada uma: estimar impacto (baixo/médio/alto) e esforço (baixo/médio/alto)
3. Plotar na matriz
4. Priorizar nesta ordem:
   1. Quick wins (resolva agora)
   2. Big bets (próximas phases)
   3. Estratégicos (milestones futuros, com ADR)
   4. Lixeira (descartar formalmente)

**Exemplo:**

| Oportunidade | Impacto | Esforço | Quadrante |
|---|---|---|---|
| Tooltips contextuais | Médio | Baixo | **Quick win** |
| Modo async para simulação | Alto | Médio | **Big bet** |
| Dark mode | Baixo | Médio | Lixeira ou backlog |
| Refazer arquitetura completa | Alto | Alto | Estratégico (próximo milestone) |
| Logo novo | Baixo | Alto | Lixeira |

### 3.2 RICE Score (quando precisa quantificar)

```
RICE = (Reach × Impact × Confidence) / Effort
```

**Componentes:**

- **Reach**: usuários atingidos por mês (números reais)
- **Impact**: 0.25 (mínimo), 0.5 (baixo), 1 (médio), 2 (alto), 3 (massivo)
- **Confidence**: 50% (palpite), 80% (dado sólido), 100% (certeza absoluta)
- **Effort**: pessoa-mês (1 dev × 1 mês = 1)

**Exemplo (Áugure):**

```
Oportunidade: "Reduzir tempo de simulação de 15 para 5min"

Reach: 1000 usuários ativos/mês
Impact: 2 (alto - resolve fundo do poço)
Confidence: 80% (dado de churn confirma)
Effort: 0.5 pessoa-mês (1 dev × 2 semanas)

RICE = (1000 × 2 × 0.80) / 0.5 = 3200
```

**Como interpretar:**

- RICE muito alto (>5000) — top priority
- RICE médio (1000-5000) — backlog priorizado
- RICE baixo (<1000) — descartar ou revisar premissas

**Tabela exemplo Áugure:**

| Oportunidade | Reach | Impact | Conf% | Effort | RICE |
|---|---|---|---|---|---|
| Reduzir tempo simulação | 1000 | 2 | 80 | 0.5 | **3200** |
| Tooltips contextuais | 1000 | 1 | 90 | 0.1 | **9000** |
| Calibração pública | 1000 | 1 | 60 | 0.3 | **2000** |
| Dark mode | 500 | 0.25 | 100 | 0.2 | **625** |
| Integração com Mercado Pago | 200 | 1 | 100 | 1 | **200** |

**Decisão:** próximo milestone entrega top 3 (tooltips, reduzir tempo, calibração).

### 3.3 ICE Score (mais rápido, brainstorm)

```
ICE = Impact × Confidence × Ease
```

Cada componente 1-10. Bom para brainstorming inicial.

```
Oportunidade: "Adicionar dark mode"
Impact: 4 (algumas pessoas pedem, mas não muda métrica)
Confidence: 9 (sabemos exatamente como fazer)
Ease: 7 (1 sprint)

ICE = 4 × 9 × 7 = 252
```

```
Oportunidade: "Refazer onboarding"
Impact: 9 (afeta toda nova entrada)
Confidence: 6 (palpite educado)
Ease: 4 (2-3 sprints)

ICE = 9 × 6 × 4 = 216
```

ICE diferente de RICE porque NÃO considera reach. Bom quando todas as oportunidades atingem mesmo público.

### 3.4 Kano Model (para B2C + features qualitativas)

Categoriza features em 5 tipos:

```
SATISFAÇÃO ALTA
       ↑
       │
  Performance ←─────────── Excitement
       │
       │
  Must-have ────────────── Indifferent
       │                    Reverse
       ↓
SATISFAÇÃO BAIXA
       ←──────── DESEMPENHO ─────────→
```

| Tipo | Definição | Exemplo (smartphone) |
|---|---|---|
| **Must-have** | Espera-se que tenha. Ausência frustra | Botão de ligar funcionar |
| **Performance** | Quanto melhor, mais satisfação | Bateria dura mais |
| **Excitement** | Inesperado e delicia | Face ID em 2017 |
| **Indifferent** | Não importa | Cor da embalagem |
| **Reverse** | Algumas pessoas odeiam | Pop-ups |

**Como aplicar:**

1. Survey n>30 com 2 perguntas por feature:
   - Como você se sente SE o produto TIVER essa feature? (gosto / não importa / espero / aceito sem gostar / odeio)
   - Como você se sente SE o produto NÃO tiver? (mesmas opções)

2. Categorizar feature por matriz Kano

3. Priorizar:
   - Must-have: implementar todos (sem isso, produto morre)
   - Performance: quanto mais, melhor (mas com diminishing returns)
   - Excitement: 1-2 por release (delicia mas não escala)
   - Indifferent + Reverse: descartar

### 3.5 Value vs Complexity (para tech debt)

Para refactor / tech debt:

```
            Alto Valor
                │
    DO IT NOW   │   PLAN CAREFULLY
                │
────────────────┼────────────────
                │
    QUICK FIX   │   AVOID
    (se sobrar) │   (não vale)
                │
            Baixo Valor
   ←──Baixa Complexidade   Alta──→
```

**Exemplo:**

| Tech debt | Valor | Complexidade | Decisão |
|---|---|---|---|
| Atualizar deps minor | Médio | Baixa | Quick fix |
| Migrar de Webpack para Vite | Médio | Média | Plan carefully |
| Reescrever auth com Auth0 | Alto | Alta | Plan carefully |
| Refatorar componente legado isolado | Baixo | Baixa | Quick fix se sobrar |
| Migração Angular 16 → 19 | Alto | Alta | Plan carefully |
| Padronizar nomes de variáveis | Baixo | Alta | Avoid |

---

## 4. Processo completo de priorização

### 4.1 Passo 1 — Brainstorm divergente

10-30 oportunidades em uma sentada. Sem julgar ainda.

**Fontes:**
- Journey map (oportunidades extraídas)
- Heuristic eval (problemas)
- User feedback (NPS, suporte, reviews)
- Competitor analysis (gaps a fechar)
- Equipe interna (ideias frescas)

**Exemplo (Áugure):**

```
1. Reduzir tempo de simulação
2. Tooltips contextuais
3. Modo offline
4. Dark mode
5. Calibração pública
6. Integração Mercado Pago
7. Templates pré-prontos
8. Comparar 2+ ideias lado a lado
9. Compartilhar relatório por link
10. Modo executive summary (resumo curto)
11. White-label para consultores
12. API para integrações
13. App mobile nativo
14. Notifications email para milestones
15. Tutorial em vídeo
16. Marketplace de templates
17. Gamificação (badges, streaks)
18. Suporte por chat
19. Multi-idioma (inglês primeiro)
20. PDF preview antes de gerar
```

### 4.2 Passo 2 — Aplicar framework escolhido

Para cada oportunidade:
- Estimar (rapidamente, não perfeição)
- Justificar score brevemente

**Exemplo (RICE):**

```yaml
oportunidade: "Modo executive summary"
reach: 1000  # todos os usuários
impact: 2    # alto - resolve para Carlos (P-002) que não lê 70 páginas
confidence: 70  # palpite educado, não testado
effort: 0.3  # 1 dev × 6 semanas (revisar formato, gerar, testar)
RICE: 4666

justificativa: |
  Carlos é persona secundária mas representa 30% da base.
  Ele compra mas raramente lê o relatório completo.
  Resumo executivo aumentaria valor percebido para ele.
  Confidence 70% porque é hipótese, não testada com dado.
```

### 4.3 Passo 3 — Priorizar (top N, cortar pela metade)

**Mostrar matriz/lista ordenada. Cortar pela metade.** Half = lixo.

```
Top 20 oportunidades (por RICE descendente):
1. Tooltips (9000) ← TOP
2. Modo executive summary (4666) ← TOP
3. Reduzir tempo simulação (3200) ← TOP
4. Calibração pública (2000) ← TOP
5. Templates pré-prontos (1800) ← TOP
6. Compartilhar por link (1500) ← TOP
7. PDF preview (1200) ← TOP
8. Comparar 2 ideias (900) ← cortar
9. Tutorial vídeo (800) ← cortar
10. Notifications email (700) ← cortar
11. Dark mode (625) ← cortar
12. Multi-idioma (500) ← cortar
... (resto fora)
```

**Decisão:** próximo milestone entrega top 3-7. Resto vai para backlog ou descarta.

### 4.4 Passo 4 — Documentar decisão

Salvar em `.planning/OPPORTUNITY-MATRIX.md`. Revisar a cada milestone.

```markdown
# Opportunity Matrix — Milestone v1.1

## Framework usado
RICE Score

## Contexto
- Persona primária: Bruna (P-001, 70%)
- Persona secundária: Carlos (P-002, 30%)
- Capacity disponível: 8 sprint pessoa-mês

## Top 5 priorizadas (cabem no milestone)

### 1. Tooltips contextuais (RICE: 9000)
- Stage do journey: S6 (Setup)
- Effort: 0.1 pessoa-mês
- Phase candidata: Phase 7

### 2. Modo executive summary (RICE: 4666)
- Persona: Carlos primário
- Effort: 0.3 pessoa-mês
- Phase candidata: Phase 8

### 3. Reduzir tempo simulação (RICE: 3200)
- Stage do journey: S7 (Espera)
- Effort: 0.5 pessoa-mês
- Phase candidata: Phase 9

[...]

## Descartadas (e por quê)

### Dark mode (RICE: 625)
- Razão: baixo impact em métrica norte
- Revisitar: v1.3

### Multi-idioma (RICE: 500)
- Razão: foco BR primeiro
- Revisitar: depois de PMF
```

### 4.5 Passo 5 — Revisitar a cada milestone

```
A cada início de milestone:
1. Mover concluídas para "DELIVERED"
2. Re-scorear baseado em dado novo (Confidence muda com analytics)
3. Adicionar novas (do journey/feedback)
4. Cortar pela metade
5. Top N vira novo milestone
```

---

## 5. Templates copy-paste

### 5.1 Template RICE (planilha)

```yaml
opportunity:
  id: "OPP-001"
  name: "Reduzir tempo de simulação"
  description: |
    Otimizar pipeline de simulação para reduzir de 15min para 5min.
    Envolve cache de dados de mercado + paralelização de cenários.

  rice:
    reach: 1000          # usuários ativos/mês
    reach_evidence: "Analytics março/abril 2026"

    impact: 2            # 0.25 / 0.5 / 1 / 2 / 3
    impact_justification: |
      Resolve fundo do poço em S7 (Espera 15min).
      Curva emocional cai para -2 nesse estágio.

    confidence: 80       # %
    confidence_evidence: |
      18 tickets de suporte mencionando "demora demais".
      NPS comments destacam impaciência.

    effort: 0.5          # pessoa-mês
    effort_estimate_source: "Tech lead estima 2 semanas para 1 dev"

  rice_score: 3200       # (1000 × 2 × 0.8) / 0.5

  rank: 3                # após ordenar todas
  decision: "INCLUDE"    # INCLUDE / DEFER / DESCARD

  next_step: "Phase 9 do Milestone v1.1"
```

### 5.2 Template Impact-Effort (rápido)

```markdown
# Quick Prioritization — [milestone]

## Quick wins (alto impacto, baixo esforço) — FAZER JÁ
1. [Nome] — [1 frase justificativa]
2. ...

## Big bets (alto impacto, alto esforço) — PRÓXIMA
1. [Nome] — [justificativa]
2. ...

## Estratégicos (alto valor, alta complexidade) — MILESTONE+
1. [Nome] — [justificativa] — [requer ADR]
2. ...

## Descartadas (baixo valor) — NÃO FAZER
1. [Nome] — [razão]
2. ...
```

### 5.3 Prompt para Claude priorizar

```
"Aplique RICE score em todas as oportunidades de
.planning/journeys/journey-bruna-jtbd-001.yaml.

Para cada oportunidade extraída do journey:
1. Estimar Reach (usar analytics em [path] se disponível)
2. Estimar Impact (0.25, 0.5, 1, 2, 3) com justificativa
3. Estimar Confidence (%) com evidência
4. Estimar Effort (pessoa-mês)
5. Calcular RICE

Ordenar por RICE descendente.
Cortar pela metade.
Top 5 viram phase candidates.

Salvar em .planning/OPPORTUNITY-MATRIX.md."
```

---

## 6. Casos práticos

### 6.1 Áugure v1.1 (priorização real)

**Contexto:**
- v1.0 entregue (5 phases)
- 87 usuários ativos
- Top 3 frustrações do NPS: "demora", "wizard confuso", "não consigo comparar"

**Aplicação RICE:**

| Oportunidade | R | I | C% | E | RICE | Rank |
|---|---|---|---|---|---|---|
| Tooltips wizard | 87 | 1 | 90 | 0.1 | 783 | 4 |
| Reduzir tempo (15→5min) | 87 | 2 | 80 | 0.5 | 278 | 7 |
| Comparar 2 ideias | 87 | 2 | 70 | 0.4 | 304 | 6 |
| Templates pré-prontos | 87 | 1 | 80 | 0.2 | 348 | 5 |
| Modo async + email | 87 | 3 | 90 | 0.3 | **783** | 1 |
| Calibração pública | 87 | 2 | 60 | 0.3 | 348 | 5 |
| Compartilhar por link | 87 | 1 | 90 | 0.1 | 783 | 1 |

**Decisão:** v1.1 entrega top 3-4 (modo async, compartilhar, tooltips, comparar).

### 6.2 SaaS B2B (priorização entre features)

**Contexto:**
- 500 trial signups/mês
- Conversão trial→paid: 8% (target: 15%)
- Top blocker: setup complexo

**Aplicação RICE:**

| Feature | R | I | C% | E | RICE |
|---|---|---|---|---|---|
| Onboarding 30s | 500 | 3 | 80 | 1 | 1200 |
| Templates de setup | 500 | 2 | 90 | 0.5 | 1800 |
| Webinar onboarding | 500 | 1 | 70 | 0.3 | 1166 |
| White-glove setup (paid) | 100 | 3 | 60 | 0.5 | 360 |

**Decisão:** templates (1800) primeiro, onboarding 30s (1200) depois.

---

## 7. Anti-patterns com correção

### Anti-pattern 1: Priorizar por opinião

```
❌ ERRADO:
"Acho que dark mode é importante."
"Pessoal pediu muito feature X."

✅ CORRETO:
"Dark mode tem RICE 625 (baixo).
 Feature X tem RICE 3200 (alto).
 Implementamos feature X primeiro."
```

### Anti-pattern 2: Pular brainstorm divergente

```
❌ ERRADO:
"Vamos discutir entre essas 3 ideias."

✅ CORRETO:
"Vamos listar 20 oportunidades primeiro, depois priorizar."
```

Sem divergência, prioriza no que veio à cabeça (não no melhor).

### Anti-pattern 3: Confidence sempre 100%

```
❌ ERRADO:
"Tenho certeza que dark mode vai ser hit."
Confidence: 100%

✅ CORRETO:
"Dark mode é hipótese (não testado). Confidence: 50%."
```

Confidence 100% sem evidência = sinal de não estar pensando.

### Anti-pattern 4: Score sem justificativa

```
❌ ERRADO:
| Feature | Impact |
| Dark mode | 8 |

✅ CORRETO:
| Feature | Impact | Justificativa |
| Dark mode | 0.5 | "10 menções no NPS, mas não muda North Star Metric" |
```

### Anti-pattern 5: Matriz nunca revisitada

```
❌ ERRADO:
Matriz criada em janeiro, nunca revisitada.
Em junho, contexto é diferente.

✅ CORRETO:
Revisar a cada milestone (4-8 semanas).
Re-scorear com Confidence atualizada.
```

### Anti-pattern 6: Não cortar pela metade

```
❌ ERRADO:
"Vamos fazer todas as 20 oportunidades."

✅ CORRETO:
"Top 5 cabem no milestone. Resto: backlog priorizado."
```

### Anti-pattern 7: Effort em horas (não pessoa-mês)

```
❌ ERRADO:
Effort: 80 horas

✅ CORRETO:
Effort: 0.5 pessoa-mês
(80h ≈ 2 semanas ≈ 0.5 pessoa-mês)
```

Pessoa-mês é unidade canônica para RICE.

---

## 8. Quando combinar frameworks

| Situação | Combine |
|---|---|
| MVP (poucos dados) | Impact-Effort + ICE |
| Produto estabelecido (muitos dados) | RICE + Kano |
| Refactor / tech debt | Value-Complexity |
| Pivot | Kano + journey reanalysis |
| B2B enterprise | RICE + customer feedback weighted |

---

## 9. Checklist de validação

```
PROCESSO:
□ Brainstorm divergente (15+ oportunidades)?
□ Framework escolhido apropriadamente?
□ Cada oportunidade tem score?
□ Score tem justificativa breve?

QUANTITATIVO (se RICE):
□ Reach baseado em dado real (não palpite)?
□ Impact em escala canônica (0.25/0.5/1/2/3)?
□ Confidence com evidência?
□ Effort em pessoa-mês?

PRIORIZAÇÃO:
□ Lista ordenada por score?
□ Top N escolhidos para milestone?
□ Resto categorizado (backlog/descarte)?
□ Cortou pela metade?

DOCUMENTAÇÃO:
□ Salvo em .planning/OPPORTUNITY-MATRIX.md?
□ Linkado em ROADMAP.md?
□ Plan-checker reconhece?

REVISÃO:
□ Plano de revisão (a cada milestone)?
□ Versionado em git?
```

Se <12 checks, priorização é palpite.

---

## 10. Como integra com outras skills

### 10.1 → `meta/jobs-to-be-done`
JTBD identifica jobs. Opportunities atendem outcomes desses jobs.

### 10.2 → `meta/journey-map`
Journey identifica oportunidades. Framework prioriza entre elas.

### 10.3 → `meta/north-star-vision`
Impact medido contra movimento da north-star metric.

### 10.4 → ROADMAP.md
Top oportunidades viram phase candidates.

### 10.5 → `/gsd-milestone-summary`
Reportar quais oportunidades foram entregues no milestone.

---

## 11. Erros comuns

### Erro 1: Priorizar sem dado
RICE sem analytics = palpite com fórmula.
**Fix:** sem dado, use Impact-Effort qualitativo (não pretenda quantitativo falso).

### Erro 2: Pular re-scoring
Confidence muda quando dado chega. Score que não muda = ignorando aprendizado.

### Erro 3: Effort otimista
Devs sempre subestimam (planning fallacy). Multiplique por 1.5x.

### Erro 4: "Vou fazer tudo"
Sem cortar pela metade, milestone vira espaguete. Foco é cortar.

---

## 12. Referências

- **Sean McBride (Intercom)** — RICE framework original
- **Sean Ellis** — ICE framework
- **Noriaki Kano** — Kano Model paper (1984)
- **Marty Cagan** — "Inspired" (priorização em produto)
- **Jeff Patton** — "User Story Mapping" (priorização visual)

---

**Última atualização:** v0.7.1 (densificação batch 2)
**Densidade:** 12 seções, 5 frameworks com fórmulas, exemplos calculados (Áugure, SaaS B2B), templates copy-paste, anti-patterns com correção, checklist de 14 itens
