---
name: jobs-to-be-done
category: meta
description: Mapear Jobs-to-Be-Done com 3 dimensões (funcional, emocional, social), processo completo de descoberta via switch interview, outcome-driven innovation com opportunity scores quantificados, templates copy-paste e 5 exemplos completos em domínios diferentes. Resolve "vamos construir feature X" sem justificativa de motivação real do usuário.
---

# Jobs-to-Be-Done — JTBD

> "As pessoas não querem uma broca de 1/4 de polegada. Querem um buraco de 1/4 de polegada. Mas mais profundo: querem pendurar uma foto da família. Mais profundo ainda: querem se sentir em casa."

JTBD reframa decisões de produto. Antes de "vamos construir feature X", pergunte: que job o usuário está contratando o produto para fazer?

Esta skill não é teoria. É processo operacional para extrair, validar, priorizar e usar JTBDs em decisões reais de phase.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-bootstrap` | Cada feature MVP precisa de JTBD claro |
| `/gsd-discuss-phase` em feature nova | Justificar o JOB antes de planejar |
| Pivot de produto | Re-entender que jobs novos vs antigos |
| Pricing decision | Pricing reflete valor do job, não custo |
| Phase de redesign | Job mudou, ou só execução está ruim? |

## 2. Quando NÃO usar

| Não usar quando | Use em vez disso |
|---|---|
| Bug fix | `systematic-debugging` |
| Refactor técnico interno | ADR + `quality/observability-production` |
| Phase de infra (CI/CD) | `domain/docker-production-ready` |
| Mudança regulatória | LGPD, fiscal — implementar |
| Phase já justificada por dado | A/B test result, retention data |

## 3. Anatomia de um JTBD

### 3.1 Fórmula canônica

```
Quando [SITUAÇÃO específica e concreta],
quero [MOTIVAÇÃO universal],
para [OUTCOME mensurável].
```

**Exemplo correto (Áugure):**

```
Quando [tenho ideia de negócio nova mas R$ 50k para investir e família dependendo do resultado],
quero [validar viabilidade contra dados reais antes de tomar decisão],
para [decidir investir ou abandonar com confiança calibrada, sem chute].
```

**Exemplo errado:**

```
❌ Quando [quero criar relatório],
   quero [usar nosso produto],
   para [ter relatório].
```

(Circular. Não revela motivação.)

### 3.2 As 3 dimensões obrigatórias

#### Funcional

> O que objetivamente precisa ser feito?

| Domínio | Job funcional |
|---|---|
| Áugure | "Validar se ideia de negócio tem mercado antes de gastar capital" |
| Uber | "Ir do ponto A ao ponto B sem dirigir" |
| iFood | "Comer comida pronta sem sair de casa nem cozinhar" |
| Stripe | "Receber pagamento online sem implementar gateway próprio" |
| Slack | "Comunicar com colegas sem usar email para tudo" |

#### Emocional

> Como o usuário quer se sentir durante e depois?

| Domínio | Job emocional |
|---|---|
| Áugure | "Confiante para defender decisão na frente da esposa/sócio" |
| Uber | "Seguro de chegar a tempo, sem ansiedade de táxi" |
| iFood | "Sem culpa de pedir comida (mereço, estou cansado)" |
| Stripe | "Profissional, como empresa de verdade, mesmo sendo solo" |
| Slack | "Conectado ao time, mesmo trabalhando remoto" |

#### Social

> Como o usuário quer ser visto pelos outros?

| Domínio | Job social |
|---|---|
| Áugure | "Empreendedor que decide com dado, não no chute" |
| Uber | "Pessoa eficiente que valoriza tempo" |
| iFood | "Pai/mãe ocupado que cuida da família com soluções modernas" |
| Stripe | "Founder técnico que conhece as ferramentas certas" |
| Slack | "Profissional moderno (não geração email)" |

### 3.3 Por que as 3 dimensões importam

- Só funcional → comoditizável (concorrente faz mais barato)
- Funcional + emocional → retenção razoável
- As 3 → defensável, justifica preço premium

---

## 4. Processo de descoberta

### 4.1 Passo 1 — Entrevistar (não inventar)

JTBD não vem da cabeça do fundador. Vem de entrevista profunda com usuário.

**Estrutura mínima de entrevista (60-90 min, gravada):**

#### Bloco 1 — Contexto (10 min)
- Me conta sobre seu trabalho/situação no dia a dia.
- Quando foi a última vez que você [situação relevante]?
- Me conta esse momento específico, com detalhes.

#### Bloco 2 — Switch interview (Bob Moesta) (30 min)

Sequência:
1. Quando foi a primeira vez que você pensou que precisava de [solução]?
2. O que estava acontecendo na sua vida naquela época?
3. O que você usava antes? Por que não funcionava mais?
4. Quando você decidiu trocar — qual foi o gatilho? Que dia foi?
5. Você considerou outras opções? Quais?
6. Por que descartou as outras?
7. Como foi a primeira semana usando [nova solução]?
8. Em que momento você teve certeza de que era a escolha certa?

#### Bloco 3 — Outcomes (15 min)
- Quando [solução] funciona perfeitamente, o que acontece?
- Como você mediria sucesso?
- Em escala 1-10, quão satisfeito você está? Por que não 10?

#### Bloco 4 — Anti-uso (10 min)
- Quando você NÃO usa [solução]?
- Tem alguma situação onde prefere [alternativa]?
- O que faria você abandonar?

### 4.2 Passo 2 — Sintetizar (5+ entrevistas)

Para cada entrevista, anotar:

```yaml
entrevistado: "Bruna - dona de atacarejo SP"
job_funcional_inferido: "Saber se está dando lucro real"
job_emocional_inferido: "Tranquilidade. Hoje vive com peso de não saber"
job_social_inferido: "Ser respeitada como empresária séria"

outcomes_desejados:
  - "Saber lucro líquido por mês: alta importância, baixa satisfação"
  - "Ver tendência mensal: alta importância, baixa satisfação"
  - "Comparar com mês anterior: alta importância, média satisfação"

trigger_de_compra: "Marido brigou pq ela não sabia se loja dava lucro"

alternativas_consideradas:
  - "Excel" → descartada porque "não consigo manter atualizado"
  - "Contador" → descartada porque "só vejo dado 60 dias depois"
  - "Sistema banco" → descartada porque "é genérico, não entende meu negócio"
```

### 4.3 Passo 3 — Padrões

Após 5+ entrevistas, agrupar:

```
Pattern A: "Saber lucro real"
  - 4/5 entrevistadas mencionaram
  - Sempre conectado a peso emocional
  - Sempre conectado a outro stakeholder (marido, sócio)

Pattern B: "Decidir investir"
  - 2/5
  - Conectado a momento específico (nova ideia)

Pattern C: "Mostrar para banco/investidor"
  - 1/5
  - Não é universal
```

**Regra:** se padrão aparece em <60% das entrevistas, não é job principal.

### 4.4 Passo 4 — Formular o JTBD canônico

```yaml
job_id: "JTBD-001-saber-lucro-real"
nome_curto: "Saber se está dando lucro de verdade"
trigger_situacional: |
  Empresária de comércio físico, 5+ anos no negócio, R$ 30-100k/mês,
  sem time financeiro, marca em caderno ou Excel básico,
  marido/sócio cobra "afinal está dando dinheiro?"

job_funcional: |
  Calcular lucro líquido real (após impostos, custos fixos, salários, fornecedor)
  com dado atualizado em <3 dias.

job_emocional: |
  Tranquilidade. Sair de "será que está dando certo?" para "sei que estou em X% de margem".

job_social: |
  Ser vista pelo marido/sócio/família como empresária que controla o negócio.

outcomes_desejados:
  - id: "O1"
    metric: "Tempo entre evento financeiro e ver no lucro"
    importancia: 9.5
    satisfacao_atual: 2.1
    nivel_de_oportunidade: 16.9
  - id: "O2"
    metric: "Confiança no número (% certeza)"
    importancia: 9.0
    satisfacao_atual: 5.5
    nivel_de_oportunidade: 12.5
  - id: "O3"
    metric: "Esforço para manter atualizado (h/semana)"
    importancia: 9.2
    satisfacao_atual: 2.0
    nivel_de_oportunidade: 16.4

competidores_no_job:
  diretos: []
  indiretos: ["Conta Azul", "Bling", "Olist"]
  substitutos: ["Excel próprio", "Contador externo", "Caderninho"]
  nao_consumo: "Ignorar a pergunta e tocar negócio no feeling"

evidencia: "5 entrevistas (Bruna, Carlos, Renata, José, Marisa) — todos 4-5/5 mencionaram"
```

---

## 5. Outcome-Driven Innovation (Bob Ulwick)

JTBD sozinho fica abstrato. Outcomes são mensuráveis.

### 5.1 Como extrair outcomes

Estrutura: `[Minimizar | Maximizar] o(a) [unidade] de(do) [objeto] enquanto [contexto]`.

**Exemplos para "saber lucro real":**

```
✓ Minimizar TEMPO entre venda e ver impacto no lucro mensal
✓ Maximizar PROBABILIDADE de identificar produtos com margem negativa
✓ Minimizar ESFORÇO de manter dado atualizado por dia
✓ Maximizar CONFIANÇA na precisão do número de lucro mensal
✓ Minimizar TEMPO para gerar relatório para mostrar ao sócio
✓ Maximizar FREQUÊNCIA com que confere número (ideal: diário em 30s)
✓ Minimizar CHANCE de erro humano na entrada de dado
✓ Maximizar VISIBILIDADE da tendência mês-a-mês
✓ Minimizar CUSTO mensal de ter essa visibilidade
✓ Maximizar PROBABILIDADE de identificar fraude/erro de funcionário
```

### 5.2 Opportunity Score

Pesquisa quantitativa (50+ respondentes do segmento):

- **Importância (1-10):** quão importante isso é?
- **Satisfação (1-10):** quão bem soluções atuais entregam?

**Fórmula:**

```
Opportunity Score = Importância + max(0, Importância - Satisfação)
```

| Score | Significado | Ação |
|---|---|---|
| **>15** | Underserved (oportunidade massiva) | Phase imediata |
| **10-15** | Underserved leve | Phase próximas |
| **<10** | Já bem atendido OU pouco importante | Não priorizar |

### 5.3 Anti-pattern de outcome

❌ "Boa experiência de usuário" — abstração, não outcome
✅ "Minimizar tempo de carregamento da home <1s"

❌ "Fácil de usar" — opinativo
✅ "Maximizar % de usuários que completam onboarding sem ajuda"

❌ "Confiável" — não mensurável
✅ "Minimizar tempo de downtime mensal abaixo de 30 min"

---

## 6. Templates copy-paste

### 6.1 Discovery inicial

```markdown
# JTBD Discovery — [nome do produto]

## Contexto
- Persona alvo: [específica]
- Domínio: [setor, geografia]
- Stage: [pré-MVP / MVP / Produto / Pivot]

## Entrevistas
| # | Nome | Data | Persona match? | Notas |
|---|---|---|---|---|
| 1 | Bruna | 2026-04-10 | ✓ | Atacarejo, 5 anos |
| 2 | Carlos | 2026-04-12 | ✓ | Restaurante, 8 anos |

## Padrões (>60%)

### JTBD-001: [nome]

**Quando** [situação]
**Quero** [motivação]
**Para** [outcome]

Dimensões:
- Funcional: ___
- Emocional: ___
- Social: ___

Outcomes priorizados (top 5):
1. [outcome] — score N
2. ...

Competidores:
- Diretos: ___
- Indiretos: ___
- Substitutos: ___

Evidência: [N/total entrevistadas]
```

### 6.2 Validação de feature contra JTBD

```markdown
# Validação — Phase [N]: [nome]

## JTBD que esta phase atende
- Job: [JTBD-XXX]
- Outcomes específicos: [O1, O3, O7]

## Como melhora cada outcome
| Outcome | Melhoria | Métrica de sucesso |
|---|---|---|
| O1 (tempo evento → lucro) | De 60d para 1d | Time-to-update |
| O3 (esforço atualização) | De 10h/sem para 0.5h/sem | Auto-import % |

## Validação cruzada
- [ ] Phase atende ≥1 outcome com score >12?
- [ ] Phase NÃO degrada outcome com score >12?
- [ ] Phase atende as 3 dimensões?
- [ ] Existe alternativa mais barata? Justificar.

## Riscos
- [ ] ___
- Mitigação: ___
```

### 6.3 Pitch interno

```markdown
# Pitch — Phase [N]

**Job:** Quando [...], quero [...], para [...].
**Persona afetada:** [Bruna — 42% da base]
**Outcome principal:** [reduzir tempo de 60d para 1d]
**Score atual:** 16.9 (massive opportunity)

**O que vamos construir:** [3 frases]
**O que NÃO vamos construir:** [3 frases — escopo cirúrgico]

**Métrica de sucesso pós-release:**
- Time-to-update: <24h em P95
- % usuários ativos checando lucro semanal: >40%

**Risco:** [1 risco real]
**Mitigação:** [como detectar e responder]
```

---

## 7. Anti-patterns com correção lado a lado

### Anti-pattern 1: Job descreve a solução

```
❌ ERRADO:
Quando [quero criar relatório de vendas],
quero [usar o módulo de relatórios],
para [ver as vendas].

✅ CORRETO:
Quando [reuni com sócio na sexta para revisar a semana],
quero [chegar com número confiável de vendas e margem],
para [discutir decisões com base em dado, não em achismo].
```

### Anti-pattern 2: Persona genérica no trigger

```
❌ ERRADO:
Quando [usuário quer fazer compra],
quero [completar checkout rápido],
para [ter o produto].

✅ CORRETO:
Quando [Bruna está no caixa atendendo cliente com pressa, fila de 4 atrás],
quero [registrar venda no celular sem digitar 5 campos],
para [não perder cliente nem deixar fila parada].
```

### Anti-pattern 3: Job sem dimensão emocional

```
❌ ERRADO:
Job funcional: "Pagar fornecedor"
(sem emocional, sem social)

✅ CORRETO:
Funcional: "Pagar fornecedor com prazo certo"
Emocional: "Sem ansiedade de boleto que vence sábado"
Social: "Como empresária organizada, não amadora que esquece pagamento"
```

### Anti-pattern 4: Outcome opinativo

```
❌ ERRADO:
Outcome: "Boa UX"
Outcome: "Ser fácil"
Outcome: "Ter design bonito"

✅ CORRETO:
Outcome: "Minimizar # cliques entre abrir app e ver saldo"
Outcome: "Maximizar % usuários que completam onboarding em <2min"
Outcome: "Manter NPS >50 entre usuários ativos no último mês"
```

### Anti-pattern 5: Job inventado sem entrevista

❌ Fundador escreve job sozinho na pranchetinha
✅ Job sai de 5+ entrevistas, validado em 50+ respondentes

### Anti-pattern 6: Pular anti-job

```
✅ Áugure NÃO é:
- Ferramenta de gestão financeira (Conta Azul faz)
- Marketplace de oportunidades
- Plataforma de educação empreendedora

✅ Áugure É:
- Validação rápida de viabilidade com simulação
```

---

## 8. Exemplos completos de JTBDs (5 domínios)

### Exemplo 1 — Áugure (B2B SaaS, validação)

```yaml
JTBD-001-validar-ideia-rapido:
  trigger: |
    Empresário R$ 50-500k disponível, ideia nova,
    família dependendo do resultado,
    pressão "fazer logo antes que concorrente faça".

  funcional: |
    Decidir investir/abandonar em <1 semana com dado calibrado
    sobre tamanho de mercado, concorrência, viabilidade financeira.

  emocional: |
    Confiança calibrada (não certeza falsa, mas range de probabilidade).
    Tranquilidade para defender decisão na frente da família.

  social: |
    Empreendedor moderno que decide com dado.
    Diferente do "empresário do feeling".

  outcomes_top_5:
    - "Tempo até resposta calibrada (target: <7 dias)"
    - "Confiança subjetiva (target: 7+/10)"
    - "Custo da validação (target: <R$ 500)"
    - "Cobertura de cenários (target: 5+ cenários)"
    - "Capacidade de explicar decisão (target: relatório copy-paste-ready)"

  defensabilidade:
    - Foco brasileiro (LGPD, CNPJ, CFOP)
    - Calibração pública (Brier score visível)
    - Tempo: 15 min vs semanas
    - Preço: R$ 99/mês vs R$ 5k consultoria
```

### Exemplo 2 — iFood (B2C, food delivery)

```yaml
JTBD-002-comer-sem-cozinhar:
  trigger: |
    Profissional CLT, 19h-21h, voltou cansado,
    geladeira com ingredientes mas sem energia para cozinhar,
    fome real.

  funcional: |
    Receber comida pronta em <60min, sem sair de casa,
    com variedade e preço transparente.

  emocional: |
    Sem culpa ("merecido após dia de trabalho").
    Antecipação prazerosa enquanto chega.
    Conforto de "tô cuidando de mim".

  social: |
    Profissional moderno que valoriza tempo > culpa.
    Sinal de produtividade, não preguiça.

  outcomes_top_5:
    - "Tempo pedido → comida na mesa (target: <45min)"
    - "Variedade em 5km (target: >50 restaurantes)"
    - "Confiabilidade do prazo"
    - "Transparência do preço total"
    - "Descobrir comida nova relevante"
```

### Exemplo 3 — Slack (B2B, comunicação)

```yaml
JTBD-003-comunicar-time-async:
  trigger: |
    Time distribuído (5-50), decisões em <24h,
    email lento, reunião custa caro.

  funcional: |
    Enviar mensagem e ter resposta em <2h business hours,
    contexto preservado, threads organizadas, busca funcional.

  emocional: |
    Conectado ao time mesmo de longe.
    Sem ansiedade "será que viu?" (ack visual).
    "Tô no fluxo do time."

  social: |
    Profissional moderno (não geração email).
    Time produtivo (usa ferramenta certa).

  outcomes_top_5:
    - "Tempo médio até primeira resposta (<2h business hours)"
    - "Buscar conversa antiga (full-text + filtros)"
    - "Reduzir email interno (target: <5 emails/dia)"
    - "Threads organizadas"
    - "Notificações relevantes"
```

### Exemplo 4 — Stripe (B2B, payments)

```yaml
JTBD-004-receber-pagamento-online:
  trigger: |
    Founder técnico, produto digital ou marketplace,
    cobrar R$ 100-100k/mês, primeiro mês vendendo,
    sem time de pagamentos / fiscal / fraude.

  funcional: |
    Aceitar pagamento online (cartão, PIX, boleto) com 1 dia de implementação,
    fee transparente, settlement em D+30, dashboard transações.

  emocional: |
    Profissional ("agora aceito pagamento, virei empresa de verdade").
    Sem medo de fraude (Stripe protege).
    Confiança em scaling.

  social: |
    Founder que escolhe ferramentas modernas.
    Não usa "PagSeguro do João" (gambiarra).

  outcomes_top_5:
    - "Tempo até primeiro pagamento (target: <1 dia)"
    - "Fee transparente"
    - "Documentação que dev usa sem suporte (target: 90%)"
    - "Webhook confiável (>99.9% delivery)"
    - "Compliance fiscal automático (NF-e gerada)"
```

### Exemplo 5 — Notion (docs/wiki)

```yaml
JTBD-005-organizar-conhecimento:
  trigger: |
    Pessoa ou time pequeno (<20),
    info espalhada em Google Docs, Slack, email, papel,
    cresce caos a cada projeto novo.

  funcional: |
    Centralizar docs, links, tarefas, anotações em um lugar,
    com hierarquia + busca + colaboração simultânea.

  emocional: |
    Controle ("sei onde tá tudo").
    Calma ("não vou perder nada").
    Orgulho do "second brain" organizado.

  social: |
    Knowledge worker moderno.
    Diferente de quem usa "Word + email" (anos 2000).

  outcomes_top_5:
    - "Tempo para encontrar info (<30s)"
    - "Linkar conceitos (bidirecional)"
    - "Trabalhar simultaneamente"
    - "Funcionar offline e sync"
    - "Templates reutilizáveis"
```

---

## 9. Como JTBD vira input para outras skills

### 9.1 → `meta/user-persona`

```
JTBD: "Saber lucro real"
→ Persona primária: "Bruna - empresária PME comércio físico"
→ Persona secundária: "Carlos - empresário PME serviços"
→ Anti-persona: "Pedro - empreendedor tech (Conta Azul atende ele)"
```

### 9.2 → `meta/journey-map`

```
JTBD: "Validar ideia em <7 dias"
→ Journey:
   1. Tem ideia (gatilho)
   2. Pesquisa Google "validar ideia de negócio"
   3. Encontra Áugure
   4. Avalia (free trial, pricing)
   5. Onboarding
   6. Insere parâmetros
   7. Aguarda processamento
   8. Recebe relatório
   9. Decide investir/abandonar
   10. Compartilha decisão
```

### 9.3 → `meta/opportunity-framework`

```
Outcome com score 16.9 → RICE de feature relacionada vai ser alto
Outcome com score 8.0 → não vira phase agora
```

### 9.4 → PLAN.md de phase

Toda phase declara:

```markdown
## Phase 3 — Importação automática de extrato

### JTBD que atende
- Job: JTBD-001-saber-lucro-real
- Outcomes: O1 (tempo até atualização), O3 (esforço de atualização)
- Persona primária: Bruna do Atacarejo
```

### 9.5 → `/gsd-milestone-summary`

```markdown
## Resultado do Milestone v1.1

### Outcome O1 — Tempo evento → lucro
- Antes: 60 dias (com contador)
- Depois: 24h (com import automático)
- Score: 16.9 → 8.0 (massive → served)

### Outcome O3 — Esforço de atualização
- Antes: 10h/semana (Excel)
- Depois: 0.5h/semana (review)
- Score: 16.4 → 5.0 (massive → overserved)
```

---

## 10. Checklist de validação de JTBD

```
[ ] Tem fórmula completa (Quando/Quero/Para)?
[ ] Trigger situacional é específico?
[ ] Job funcional é mensurável e observável?
[ ] Job emocional descreve estado, não atributo?
[ ] Job social descreve identidade projetada?
[ ] 10+ outcomes listados?
[ ] Top 5 outcomes têm Importance e Satisfaction?
[ ] ≥2 outcomes com score >12?
[ ] Competidores em 4 categorias?
[ ] Anti-jobs definidos?
[ ] Evidência: 5+ entrevistas?
[ ] Persona primária identificada?
[ ] Trigger de compra (switch moment) capturado?
[ ] Defensabilidade clara?
```

Se <12 checks, JTBD é palpite. Volte para entrevistas.

---

## 11. Erros comuns de implementação

### Erro 1: JTBD na parede mas não no PLAN.md
JTBD vira ornamento. **Fix:** template de PLAN.md tem campo obrigatório "JTBD atendido".

### Erro 2: JTBDs múltiplos conflitantes
Produto tenta atender 5 ao mesmo tempo. **Fix:** 1 primário (60% foco), 1-2 secundários (20-30%), resto = anti-jobs.

### Erro 3: JTBD vira moving target
Cada milestone redefine. **Fix:** muda só com 10+ entrevistas novas. Mudança = ADR formal.

### Erro 4: Outcome de vanity metric
"Número de usuários ativos" — não diz nada sobre job entregue. **Fix:** outcome mede entrega de valor para usuário.

### Erro 5: Confundir JTBD com persona
"O job da Bruna" — Bruna não tem job, ela contrata produtos. **Fix:** JTBD é universal, persona é específica.

---

## 12. Frameworks adjacentes

| Framework | Quando usar | Skill |
|---|---|---|
| JTBD (Christensen) | Qual problema o produto resolve | esta |
| Outcome-Driven Innovation (Ulwick) | Quantificar oportunidade | esta (seção 5) |
| Switch Interview (Moesta) | Como entrevistar | esta (seção 4.1) |
| Value Proposition Canvas | Pains/gains do segmento | complementar com user-persona |
| Lean/Business Model Canvas | Modelo de negócio | usar no /gsd-bootstrap |
| OKRs | Medir progresso | usar com north-star-vision |
| HEART (Google) | Métricas de UX | em milestone-audit |

---

## 13. Como validar aplicação real (não só citação)

**Sinais de aplicação real:**
✅ PLAN.md tem seção "JTBD atendido" com job_id existente
✅ Cita 1+ outcome específico com score
✅ Success criteria = melhoria mensurável de outcome
✅ Verification testa se outcome foi movido

**Sinais de citação ornamental:**
❌ "Esta phase usa JTBD" sem job_id específico
❌ Sem outcomes ligados
❌ Success criteria genérico
❌ Verification = "código funciona"

Em sessão Claude:

```
"Antes de executar phase N, abra .claude/skills/meta/jobs-to-be-done/SKILL.md.
Confirme:
1. Qual JTBD esta phase atende (job_id específico)?
2. Quais outcomes esta phase melhora (com scores antes/depois)?
3. Como vamos medir a melhoria pós-release?
Não comece a codar até eu confirmar."
```

---

## 14. Integração com fluxo gsd

```
gsd-bootstrap → 5 entrevistas → sintetizar JTBDs
                                      ↓
              quantificar outcomes (50+ resp)
                                      ↓
              Top 3 JTBDs no project.yaml
                                      ↓
              ROADMAP por outcome score
                                      ↓
              cada phase atende ≥1 outcome
                                      ↓
              plan-checker valida JTBD citado
                                      ↓
              verify mede outcome movido
                                      ↓
              milestone summary: outcomes antes/depois
```

---

## 15. Referências

- **Clayton Christensen** — "Competing Against Luck" (2016) — base teórica
- **Bob Moesta** — "Demand-Side Sales 101" (2020) — switch interview
- **Tony Ulwick** — "Jobs To Be Done: Theory to Practice" (2016) — outcome-driven innovation
- **Alan Klement** — "When Coffee and Kale Compete" (2016) — JTBD para early-stage
- **JTBD.info** — site canônico com cases

---

**Última atualização:** v0.7.0 (densificação)
**Densidade:** 15 seções, 5 exemplos completos, anti-patterns com correção, 3 templates copy-paste, checklist de 14 itens
