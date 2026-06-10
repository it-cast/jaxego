---
name: journey-map
category: meta
description: Mapear jornada end-to-end do usuário com estágios, touchpoints, emoções, dores e oportunidades. Inclui templates por tipo de produto (B2C, B2B, e-commerce, mobile), técnicas de coleta de dados, plotagem de curva emocional, integração com JTBD e persona, e como oportunidades viram phases. Resolve "vamos otimizar feature X" sem entender contexto da jornada inteira.
---

# Journey Map — Mapa de Jornada do Usuário

> Journey map mostra o filme, não só a foto. Útil quando você está construindo uma feature mas a experiência depende de coisas antes e depois dela.

Esta skill define como **mapear a jornada de uma persona contratando um JTBD específico**, com profundidade que orienta decisões reais.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-discuss-phase` em phase de onboarding | Onboarding é jornada, não tela isolada |
| `/gsd-discuss-phase` em phase de checkout | Checkout atravessa múltiplas etapas |
| `/gsd-bootstrap` se produto tem fluxo crítico não-trivial | Definir estágios desde o início |
| Antes de phases de growth/retention | Identificar onde curva cai |
| Antes de redesign | Mapear pontos de fricção atuais |
| Após `meta/jobs-to-be-done` | Cada JTBD vira jornada |

## 2. Quando NÃO usar

- Phase backend sem UX visível
- Bug fix isolado
- Phase de polish/refactor visual sem mudar fluxo
- Feature isolada que não atravessa estágios

---

## 3. Anatomia de uma journey

### 3.1 Componentes obrigatórios

| Componente | Pergunta | Exemplo (Áugure) |
|---|---|---|
| **Persona** | Quem está percorrendo? | Bruna (P-001) |
| **JTBD** | Que job ela contratou? | "Validar ideia em <7 dias" |
| **Início** | Onde começa? | Conversa com marido cobrando lucro |
| **Fim** | Onde termina? | Decisão tomada de investir/abandonar |
| **Estágios** | Etapas no meio | 7-9 estágios típico |
| **Touchpoints** | Onde acontece? | Google, landing, app, email |
| **Pensamentos** | O que passa pela cabeça? | "Será que entendo?" |
| **Emoções** | Como se sente? | Curva entre -3 e +3 |
| **Dores** | Pior fricção em cada estágio? | Confuso por preço |
| **Oportunidades** | O que pode melhorar? | Calculadora interativa |

### 3.2 Estrutura visual completa

```
ESTÁGIO 1   ESTÁGIO 2   ESTÁGIO 3   ESTÁGIO 4   ESTÁGIO 5
Descoberta  Avaliação   Cadastro    Primeiro    Conversão
                                    uso

AÇÃO        AÇÃO        AÇÃO        AÇÃO        AÇÃO
[verbo]     [verbo]     [verbo]     [verbo]     [verbo]

PENSAMENTO  PENSAMENTO  PENSAMENTO  PENSAMENTO  PENSAMENTO
"..."       "..."       "..."       "..."       "..."

EMOÇÃO      EMOÇÃO      EMOÇÃO      EMOÇÃO      EMOÇÃO
😐 +1       🙂 +2       😐 +1       😟 -2       😊 +3

TOUCHPOINT  TOUCHPOINT  TOUCHPOINT  TOUCHPOINT  TOUCHPOINT
Google ad   Site        App         App         App + email

DOR         DOR         DOR         DOR         DOR
Genérico    Pricing     Form longo  Sem onboard Sem trial
demais      complexo

OPORTUN.    OPORTUN.    OPORTUN.    OPORTUN.    OPORTUN.
Targeted    Calc        3 campos    Tour        Trial 7d
ad
```

---

## 4. Estágios típicos por contexto

### 4.1 SaaS B2B (5-7 estágios)

```
1. Identificação do problema
   "Tenho dor X, preciso resolver"

2. Pesquisa de soluções
   Google, blogs, recomendação de pares

3. Avaliação inicial
   Visita site, lê pricing, compara

4. Demo / Free trial
   Cria conta, testa, vê valor (ou não)

5. Decisão de compra
   Apresenta para time/líder, aprova budget

6. Implementação / Onboarding
   Configura, integra, treina time

7. Adoção e renovação
   Uso recorrente, ROI percebido, renova
```

### 4.2 B2C / Consumer app (5-8 estágios)

```
1. Descoberta
   Vê em rede social, indicação, busca

2. Curiosidade
   Visita store ou site, lê reviews

3. Download / Cadastro
   Instala, cria conta

4. Onboarding
   Primeiros 5 minutos críticos

5. Aha moment
   Primeira experiência com valor real

6. Hábito
   Uso recorrente (D7, D30)

7. Advocacy
   Compartilha, recomenda

8. Lealdade / Recompra
   Compra recorrente ou paga assinatura
```

### 4.3 E-commerce (6-9 estágios)

```
1. Necessidade
   "Preciso de X"

2. Pesquisa
   Google, marketplace, comparação

3. Avaliação
   Reviews, fotos, especificações

4. Decisão
   Adiciona ao carrinho

5. Checkout
   Endereço, pagamento, confirmação

6. Aguardar entrega
   Tracking, ansiedade

7. Recebimento
   Embalagem, primeira impressão

8. Uso
   Funciona como esperado?

9. Recompra ou desistência
   Volta ao site? Compartilha?
```

### 4.4 Mobile app (5-7 estágios)

```
1. Awareness
   Ad, indicação, lista app store

2. Download decision
   Tela de produto na store

3. First open
   Primeira vez no app

4. Onboarding
   Primeiros 30 segundos críticos

5. Core action
   Faz a primeira ação que entrega valor

6. Retention (D1, D7, D30)
   Volta? Quando? Por que?

7. Power user / Churn
   Usa diariamente OU desinstala
```

### 4.5 Áugure — caso real

```
1. Trigger (problema)
   Empresário tem ideia, marido cobra "vai dar certo?"

2. Pesquisa
   Google: "como validar ideia de negócio"

3. Descoberta
   Encontra Áugure (ad, blog, indicação)

4. Avaliação
   Visita landing, vê pricing, vê depoimentos

5. Cadastro
   Cria conta, plano grátis

6. Setup da simulação
   Insere dados da ideia (nicho, capital, geografia)

7. Espera
   Aguarda 15 min processando

8. Recebimento do relatório
   Lê relatório (70 páginas)

9. Decisão
   Investe / abandona / pede mais info

10. Compartilhamento
    Mostra para sócio/família/banco
```

---

## 5. Curva emocional

### 5.1 Como plotar

Eixo X = estágios. Eixo Y = emoção (-3 a +3).

```
+3 ┤                                                        ★
+2 ┤                                              ●         ●
+1 ┤        ●                              ●
 0 ┤                ●                                
-1 ┤                        ●                        
-2 ┤                                ●                       
-3 ┤
   └─────────────────────────────────────────────────────────
    Trig  Pesq  Desc  Aval  Cad   Setup Espera Relat Decisão
```

### 5.2 Vocabulário emocional específico

NÃO use "ruim" ou "ok". Use palavras específicas:

**Negativas:**
- Confusão (não entende algo)
- Frustração (tentou e falhou)
- Ansiedade (incerteza sobre resultado)
- Cansaço (esforço excessivo)
- Decepção (esperava mais)
- Medo (consequência negativa possível)
- Impaciência (espera longa)

**Positivas:**
- Curiosidade (quer saber mais)
- Esperança (pode ser solução)
- Alívio (problema resolvido)
- Surpresa positiva (melhor que esperado)
- Confiança (vai dar certo)
- Orgulho (sucesso atribuído a si)
- Conexão (sente parte de algo)

### 5.3 Onde a curva CAI = oportunidade

**Pontos críticos para identificar:**

1. **Quedas grandes entre estágios consecutivos** (>2 pontos)
   → Fricção crítica nesse trecho

2. **Estágios no fundo do poço por 2+ etapas**
   → Sequência de problemas, abandono provável

3. **Curva nunca sobe**
   → Produto morto, redesign necessário

4. **Curva sobe demais cedo, depois cai**
   → Hype enganoso, frustração tardia

5. **Curva oscilante**
   → Inconsistência de experiência

### 5.4 Onde a curva SOBE = manter

Não otimize o que está bom. Identifique e preserve.

---

## 6. Processo de criação completo

### 6.1 Passo 1 — Definir escopo

Não tente mapear "tudo". Defina:

```yaml
journey_scope:
  persona: "Bruna (P-001)"           # uma persona, não múltiplas
  jtbd: "JTBD-001 — Saber lucro real" # um job
  inicio: "Marido cobra sobre lucro"  # gatilho específico
  fim: "Decisão tomada com confiança" # outcome desejado
  duracao_aprox: "1-2 semanas"        # tempo total da jornada
  contexto: "Empresária PME, comércio físico"
```

### 6.2 Passo 2 — Coletar dados

Combinar 3 fontes mínimas:

**1. Entrevistas qualitativas (5+)** — usar técnicas de `meta/jobs-to-be-done` seção 4

**2. Analytics quantitativos** — funnel, drop-off rates, time spent

**3. Suporte/feedback** — tickets, NPS comments, app store reviews

### 6.3 Passo 3 — Listar estágios

5-9 estágios. Use templates da seção 4 como ponto de partida.

```yaml
stages:
  - id: "S1"
    name: "Trigger - cobrança do marido"
  - id: "S2"
    name: "Pesquisa Google"
  - id: "S3"
    name: "Descoberta do Áugure"
  - id: "S4"
    name: "Avaliação landing/pricing"
  - id: "S5"
    name: "Cadastro grátis"
  - id: "S6"
    name: "Setup da simulação"
  - id: "S7"
    name: "Espera (15 min)"
  - id: "S8"
    name: "Recebimento do relatório"
  - id: "S9"
    name: "Decisão final"
```

### 6.4 Passo 4 — Para cada estágio, preencher 7 campos

```yaml
stage:
  id: "S6"
  name: "Setup da simulação"

  acao: |
    Bruna abre dashboard, encontra botão "Nova simulação".
    Vê wizard de 5 passos: nicho, capital, geografia, prazo, concorrentes.
    Preenche cada campo, alguns hesitando.

  pensamento:
    - "Vai me pedir muito dado?"
    - "Não sei direito o que é 'TAM' que apareceu"
    - "Vão julgar minha ideia?"

  emocao:
    valencia: -1                  # -3 a +3
    palavra: "ansiedade leve"
    motivo: "Não tem certeza se vai conseguir preencher tudo certo"

  touchpoint: "App web"

  duracao_aprox: "8-12 minutos"

  dor:
    - id: "D6.1"
      problema: "Campo 'TAM' usa jargão sem explicação"
      severidade: 7              # 1-10
    - id: "D6.2"
      problema: "Wizard não permite voltar para corrigir"
      severidade: 5

  oportunidade:
    - id: "O6.1"
      ideia: "Tooltip explicando TAM com exemplo do nicho"
      effort: "S"
      impact: "M"
    - id: "O6.2"
      ideia: "Botão Voltar habilitado em qualquer step"
      effort: "S"
      impact: "L"
```

### 6.5 Passo 5 — Plotar curva emocional

Em cada estágio, registrar valência. Plotar.

### 6.6 Passo 6 — Priorizar oportunidades

Para cada `O*` identificado:

```yaml
oportunidade_priorizada:
  id: "O6.1"
  estagio: "S6 - Setup"
  ideia: "Tooltip explicando TAM"
  ICE_score:
    impact: 8        # 1-10 — quão impactante seria fix
    confidence: 9    # 1-10 — quão certo somos do fix
    ease: 9          # 1-10 — quão fácil implementar
    total: 648       # impact * confidence * ease
  RICE_score:
    reach: 1000      # usuários atingidos/mês
    impact: 2        # 0.25, 0.5, 1, 2, 3
    confidence: 90   # %
    effort: 0.1      # pessoa-mês
    score: 18000
  prioridade: "1 (top)"
```

### 6.7 Passo 7 — Mapear oportunidades para phases

Cada oportunidade prioritária → candidato a phase no ROADMAP.md.

```yaml
phase_candidates:
  - de_journey: "O6.1"
    phase_proposal: "Phase 7: Tooltips contextuais no wizard"
    justification: "Reduz ansiedade em S6, melhora conclusão"

  - de_journey: "O7.1"
    phase_proposal: "Phase 8: Modo async para simulações longas"
    justification: "Resolve fundo do poço em S7 (espera 15min)"

  - de_journey: "O3.2"
    phase_proposal: "Phase 9: Comparativo com concorrentes"
    justification: "Aumenta confiança em S3 (descoberta)"
```

---

## 7. Templates copy-paste

### 7.1 Journey map em formato YAML (completo)

```yaml
journey:
  meta:
    title: "Validar ideia de negócio - Bruna"
    persona_id: "P-001"
    jtbd_id: "JTBD-001"
    created: "2026-04-29"
    last_updated: "2026-04-29"
    sources:
      - "5 entrevistas qualitativas"
      - "Analytics funnel março/abril 2026"
      - "20 tickets de suporte"

  context:
    persona_short: "Bruna - empresária PME comércio físico"
    job_short: "Validar ideia de novo produto/expansão"
    start_trigger: "Marido cobra sobre lucro do negócio atual"
    end_outcome: "Decisão de investir ou abandonar tomada com confiança"
    total_duration: "1-2 semanas"

  stages:
    - id: "S1"
      name: "Trigger - cobrança do marido"
      action: "Conversa noturna em casa após dia de trabalho"
      thought: "Será que tô fazendo certo? Vou perder dinheiro?"
      emotion:
        valence: -2
        word: "ansiedade"
      touchpoint: "Casa - conversa familiar"
      duration: "15-30 min"
      pains:
        - "Sente cobrança sem ter resposta"
      opportunities:
        - "N/A - estágio fora do controle do produto"

    - id: "S2"
      name: "Pesquisa no Google"
      action: "Busca 'como validar ideia de negócio', 'vai dar certo investir em X'"
      thought: "Existe ferramenta pra isso? Quanto custa?"
      emotion:
        valence: 0
        word: "esperança cautelosa"
      touchpoint: "Google search"
      duration: "20-40 min"
      pains:
        - "Resultados de blog genéricos sem ferramenta concreta"
        - "Concorrentes americanos não servem para BR"
      opportunities:
        - id: "O2.1"
          idea: "SEO para queries específicas BR"
          impact: 7
          effort: 3

    - id: "S3"
      name: "Descoberta do Áugure"
      action: "Clica em ad ou resultado orgânico, chega no site"
      thought: "Parece interessante, mas será que serve pra mim?"
      emotion:
        valence: +1
        word: "curiosidade"
      touchpoint: "Landing page"
      duration: "5-10 min"
      pains:
        - "Hero genérico não fala da Bruna específica"
        - "Pricing não está visível"
      opportunities:
        - id: "O3.1"
          idea: "Hero com depoimento de Bruna real (case study)"
          impact: 8
          effort: 2
        - id: "O3.2"
          idea: "Pricing visível na página principal"
          impact: 7
          effort: 1

    # ... (continua para cada estágio)

  emotional_curve:
    - { stage: "S1", valence: -2 }
    - { stage: "S2", valence: 0 }
    - { stage: "S3", valence: +1 }
    - { stage: "S4", valence: +2 }
    - { stage: "S5", valence: +2 }
    - { stage: "S6", valence: -1 }
    - { stage: "S7", valence: -2 }
    - { stage: "S8", valence: +3 }
    - { stage: "S9", valence: +2 }

  critical_insights:
    - "Curva cai em S6-S7 (setup + espera) — abandono provável"
    - "S2 está plana — perda de oportunidade pré-onboarding"
    - "S8 é pico — preservar valor do relatório"

  prioritized_opportunities:
    - rank: 1
      opportunity_id: "O7.1"
      phase_candidate: "Modo async com email"
      reasoning: "Resolve fundo do poço (S7), redução de churn estimada 15%"

    - rank: 2
      opportunity_id: "O6.1"
      phase_candidate: "Tooltips contextuais no wizard"
      reasoning: "Reduz ansiedade em S6, aumenta conclusão"

    - rank: 3
      opportunity_id: "O3.2"
      phase_candidate: "Pricing transparente"
      reasoning: "Aumenta confiança em S3"
```

### 7.2 Journey map em formato visual (ASCII)

```markdown
# Journey Map: Bruna validando ideia (JTBD-001)

## Curva emocional

```
+3                                                  ★
+2                                       ●  ●           ●
+1                          ●
 0                ●
-1                                                 
-2     ●                              ●         
-3
       S1   S2   S3   S4   S5   S6   S7   S8   S9
       Trig Pesq Desc Aval Cad  Set  Esp  Rel  Dec
```

## Detalhe por estágio

### S1 — Trigger (-2 ansiedade)

**Action:** Conversa familiar noturna
**Thought:** "Vai dar certo?"
**Pain:** Sem resposta
**Opportunity:** N/A (fora do produto)

### S2 — Pesquisa Google (0 esperança cautelosa)

**Action:** Busca soluções
**Thought:** "Existe ferramenta?"
**Pain:** Resultados genéricos americanos
**Opportunity:** SEO BR (O2.1)

### S3 — Descoberta (+1 curiosidade)

**Action:** Visita landing
**Thought:** "Será que serve?"
**Pain:** Hero genérico
**Opportunity:** Hero personalizado (O3.1)

### S6 — Setup (-1 ansiedade leve)

**Action:** Preenche wizard
**Thought:** "Não sei o que é TAM"
**Pain:** Jargão sem explicação
**Opportunity:** Tooltips (O6.1)

### S7 — Espera (-2 impaciência)

**Action:** Aguarda 15 min
**Thought:** "Travou? Devo fechar?"
**Pain:** Sem feedback durante processo
**Opportunity:** Modo async + email (O7.1)

### S8 — Relatório (+3 alívio + surpresa)

**Action:** Lê 70 páginas
**Thought:** "Era isso que eu precisava!"
**Pain:** Nenhuma significativa
**Opportunity:** Preservar e amplificar (compartilhamento fácil)
```

### 7.3 Prompt para Claude executar journey map

```
"Crie um journey map seguindo .claude/skills/meta/journey-map/SKILL.md.

Persona: [P-XXX]
JTBD: [JTBD-XXX]
Início: [trigger]
Fim: [outcome desejado]

Para cada estágio (5-9 estágios):
1. Action (verbo concreto)
2. Thought (citação primeira pessoa)
3. Emotion (valence -3 a +3 + palavra específica)
4. Touchpoint
5. Duration
6. Pains (com severidade 1-10)
7. Opportunities (com impact + effort)

Use dados disponíveis em:
- docs/personas/persona-[X].md
- docs/jtbd/jtbd-[X].md
- analytics em [path]
- entrevistas em [path]

Compile em .planning/journeys/journey-[persona]-[jtbd].yaml.
Plote curva emocional ASCII.
Liste top 5 oportunidades priorizadas para virar phases."
```

---

## 8. Ferramentas de visualização

### 8.1 Para criar visualmente

- **Miro** — collaborative, templates de journey map
- **Mural** — similar ao Miro
- **FigJam** (Figma) — colaboração em tempo real
- **Whimsical** — clean, simples
- **Smaply** — específico para journey/persona/empathy

### 8.2 Para versionar (recomendado)

YAML em git → `.planning/journeys/journey-*.yaml`

Vantagens:
- Versionado
- Diffable
- Pode ser parsed por scripts
- Não depende de tool externo

### 8.3 Renderizar YAML em visual

Script Python simples para gerar SVG ou ASCII a partir do YAML. Exemplo no zip do framework: `bin/render-journey.py`.

---

## 9. Anti-patterns com correção

### Anti-pattern 1: Journey de "todos os usuários"

```
❌ ERRADO:
"Journey do usuário do app"
(genérico, não orienta decisão)

✅ CORRETO:
"Journey de Bruna (P-001) contratando JTBD-001 (validar ideia)"
(específico, baseado em pesquisa real)
```

### Anti-pattern 2: Journey muito granular

```
❌ ERRADO:
30 estágios cobrindo cada clique:
"Click no botão login → digita email → click no campo senha → digita senha → ..."

✅ CORRETO:
5-9 estágios cobrindo MOMENTOS:
"Cadastro" (todos os cliques juntos)
```

Granular vira fluxograma de tela, não journey.

### Anti-pattern 3: Emoções vagas

```
❌ ERRADO:
"Stage 3: emoção = ruim"
"Stage 4: emoção = ok"

✅ CORRETO:
"Stage 3: ansiedade (-2) - 'será que vou conseguir entender?'"
"Stage 4: confiança (+1) - 'agora sei o que fazer'"
```

### Anti-pattern 4: Journey sem oportunidades

```
❌ ERRADO:
Mapa lindo, 9 estágios detalhados, ZERO oportunidades extraídas.
Journey vira decoração.

✅ CORRETO:
Cada estágio com pain + opportunity. Top 5 viram phase candidates.
```

### Anti-pattern 5: Journey fictício

```
❌ ERRADO:
Time se reúne e inventa journey "do que acha".

✅ CORRETO:
Journey vem de:
- 5+ entrevistas com pessoas reais
- Analytics quantitativo
- Tickets de suporte
- Reviews da app store
```

### Anti-pattern 6: Journey nunca atualizado

```
❌ ERRADO:
Journey criado no bootstrap, nunca mais revisitado.
2 anos depois, comportamento real é diferente.

✅ CORRETO:
Journey revisado a cada 6 meses ou quando dado revela divergência.
ADR documenta mudanças significativas.
```

### Anti-pattern 7: Múltiplos journeys da mesma persona/job

```
❌ ERRADO:
"Journey 1: Bruna validando ideia"
"Journey 2: Bruna validando ideia 2"
(dois journeys diferentes para mesma combinação)

✅ CORRETO:
1 journey por (persona, JTBD). Se há variantes, são "branches" no mesmo journey.
```

---

## 10. Como journey vira input para outras coisas

### 10.1 → ROADMAP.md

Top 5 oportunidades viram phase candidates:

```markdown
## Phases candidatas (extraídas de Journey Map)

### Phase 7 — Modo async para simulações longas
**Origem:** Journey JTBD-001, estágio S7 (Espera)
**Pain:** Curva cai para -2, abandono provável
**Estimativa:** 3 sprints
**Impacto esperado:** +15% conclusão de simulação
```

### 10.2 → PLAN.md de phase

Cada phase declara qual oportunidade do journey atende:

```markdown
## Phase 7 — Modo async

### Origem
- Journey: JTBD-001 (Bruna validando ideia)
- Stage: S7 (Espera 15min)
- Pain: P7.1 (sem feedback durante processamento)
- Opportunity: O7.1 (modo async + email)
- Curva emocional atual: -2 → target: 0
```

### 10.3 → Verification

Verificar se curva foi movida:

```markdown
## Verification — Phase 7 (Modo async)

### Métricas pós-fix
- Abandono em S7: 22% → 8% ✓
- NPS comments mencionando "espera": 18 → 3 ✓
- Curva emocional re-medida em S7: -2 → +1 ✓
```

### 10.4 → Heuristic evaluation

Heuristic 1 (visibilidade) avaliada considerando S7 do journey.

---

## 11. Casos práticos por contexto

### 11.1 Onboarding journey (mobile app B2C)

**Estágios típicos:**
1. Download (decisão na store)
2. First open (primeiros 3 segundos)
3. Permission asks (location, notifications)
4. Account creation (form ou social)
5. Tutorial / tour
6. First action (core action do produto)
7. Aha moment

**Pontos críticos:**
- S2 → S3: maioria abandona se permissions vêm cedo demais
- S4: form longo = drop-off massivo
- S6 → S7: aha moment precisa vir em <60s do first open

**Oportunidades comuns:**
- Pular permissions iniciais (pedir só quando necessário)
- Social login antes de form manual
- Skip tutorial (deixar opcional)
- First action que entrega valor imediato

### 11.2 Checkout journey (e-commerce)

**Estágios típicos:**
1. Cart review
2. Shipping address
3. Shipping method selection
4. Payment method
5. Review order
6. Confirmation

**Pontos críticos:**
- S1: surpresa com frete cara = abandono massivo
- S2: form longo desanima
- S4: muitas opções de pagamento confunde
- S5: surpresa com taxas/impostos = volta atrás

**Oportunidades comuns:**
- Frete calculado no carrinho (S1)
- Endereço auto-completar via CEP (S2)
- Default smart de pagamento (último usado) (S4)
- Total final desde S1 (transparência)

### 11.3 SaaS B2B (free trial → paid)

**Estágios:**
1. Discovery (busca, indicação, ad)
2. Trial signup
3. Onboarding setup
4. First successful use
5. Team invitation
6. Mid-trial reminder
7. Decision point (paid?)
8. Paid conversion ou churn

**Pontos críticos:**
- S3: setup complexo perde 40% dos trials
- S4 → S5: trial individual não vira team trial
- S6 → S7: sem reminder, esquece de pagar

### 11.4 Áugure — Journey completa documentada

(Vide seção 7.1 — exemplo full)

---

## 12. Checklist de validação

```
ESCOPO:
□ Persona única definida (não "usuários em geral")?
□ JTBD único definido (não "uso geral do produto")?
□ Início e fim explícitos?

DADOS:
□ Vem de 5+ entrevistas qualitativas?
□ Analytics quantitativos consultados?
□ Tickets de suporte / reviews considerados?

ESTÁGIOS:
□ Entre 5 e 9 estágios?
□ Cada estágio tem 7 campos preenchidos?
□ Estágios cobrem moment-to-moment, não cliques?

EMOÇÕES:
□ Cada estágio tem valence (-3 a +3)?
□ Cada estágio tem palavra específica (não "ruim")?
□ Curva plotada visualmente?

PAINS:
□ Cada estágio identifica pelo menos 1 pain?
□ Pains têm severity (1-10)?

OPORTUNIDADES:
□ Cada estágio tem pelo menos 1 opportunity?
□ Top 5 oportunidades priorizadas (RICE/ICE)?
□ Oportunidades viram phase candidates no ROADMAP?

DOCUMENTAÇÃO:
□ Salvo em .planning/journeys/?
□ YAML versionado em git?
□ Linkado em PLAN.md das phases derivadas?

MANUTENÇÃO:
□ Última atualização <6 meses?
□ Plano de revisão definido?
```

Se <13 checks, journey é incompleto.

---

## 13. Erros comuns

### Erro 1: Journey criado e abandonado
Journey vira pôster decorativo. **Fix:** templates de PLAN.md exigem citação do journey + estágio + opportunity.

### Erro 2: Journey ≠ User Flow
User flow é fluxograma técnico (clique → tela → ação). Journey é experiência humana (com emoções, contexto, vida).

### Erro 3: Mapear sem persona
Sem persona definida, journey vira genérico. **Fix:** journey segue persona do `meta/user-persona`.

### Erro 4: Pular curva emocional
"Lista de estágios" sem emoções não é journey, é diagrama. **Fix:** valence + palavra obrigatórios.

### Erro 5: Granularidade errada
Muito granular (30 estágios) ou muito amplo (3 estágios). **Fix:** 5-9 estágios por moment-to-moment.

---

## 14. Frameworks adjacentes

| Framework | Quando usar |
|---|---|
| **Customer Journey Map** | Esta skill — experiência completa |
| **User Flow** | Para cada estágio, detalhar cliques |
| **Service Blueprint** | Adiciona backstage (operacional) ao journey |
| **Empathy Map** | Zoom em estágio específico (sentimentos profundos) |
| **JTBD** | Define que job percorre o journey |
| **Persona** | Define quem percorre |

Use journey + JTBD + persona como trinca.

---

## 15. Como integra com fluxo gsd

### 15.1 → `meta/user-persona` (input)
Journey é da persona X.

### 15.2 → `meta/jobs-to-be-done` (input)
Journey representa execução do JTBD Y.

### 15.3 → `meta/opportunity-framework` (output)
Top oportunidades viram input para priorização.

### 15.4 → `quality/heuristic-evaluation`
Heuristic eval considera estágio do journey.

### 15.5 → ROADMAP.md
Phases nascem de oportunidades do journey.

### 15.6 → `/gsd-milestone-summary`
Reportar movimento de curva emocional pós-milestone.

---

## 16. Referências

- **Kim Erwin** — "Communicating the New" (journey mapping crítico)
- **Marc Stickdorn** — "This is Service Design Doing" (service blueprints)
- **NN/g (Nielsen Norman Group)** — extensive journey mapping resources
- **Adaptive Path** — pioneer of journey mapping methodology
- **Marty Cagan** — "Inspired" (journeys em product management)

---

**Última atualização:** v0.7.1 (densificação batch 2)
**Densidade:** 16 seções, 5 templates por contexto, exemplo completo Áugure, anti-patterns com correção, checklist de 18 itens
