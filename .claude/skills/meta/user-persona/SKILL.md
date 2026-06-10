---
name: user-persona
category: meta
description: Criar personas acionáveis a partir de pesquisa real (não inventadas). Templates para entrevista, síntese, validação e ativação. Distingue persona-decoração de persona-instrumento. Inclui anti-personas, persona priorization matrix e como personas alimentam JTBD, journey-map e PLAN.md.
---

# User Persona — Persona de Usuário

> Persona não é "Maria, 35 anos, gosta de café". Persona é instrumento: quando time discorda sobre feature X, pergunta "a Persona Bruna usaria isso?".

Esta skill define como **fazer personas que orientam decisão**, não personas que viram pôster decorativo.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-bootstrap` em projeto com usuário externo | Toda decisão de UI/UX precisa ancorar em persona |
| `/gsd-discuss-phase` quando phase atende >1 persona | Decidir prioridade, trade-offs |
| Pivot ou mudança de mercado | Persona velha não serve mais |
| Após 6 meses sem revisar | Dado de uso real diverge do que pensava |
| Antes de pricing decision | Pricing reflete capacidade de pagar da persona |

## 2. Quando NÃO usar

- Bug fix interno (não afeta usuário externo)
- Refactor técnico sem mudança de UX
- Phase de infra
- Produto B2B onde único usuário é o decisor de compra (use `meta/jobs-to-be-done` direto)

## 3. Persona acionável vs persona ornamental

### 3.1 Comparação lado a lado

| Persona ornamental (descartável) | Persona acionável (instrumento) |
|---|---|
| "Mulher 25-45 anos urbana classe B" | "Empresária dona de loja física com 2-5 funcionários, fatura R$ 30-100k/mês, vendeu por WhatsApp na pandemia, agora quer crescer mas não tem time de marketing" |
| "Gosta de tecnologia" | "Usa WhatsApp Business diariamente mas Instagram só 2x/semana. Tentou ifood pro mas achou caro" |
| "Quer praticidade" | "Não tem 30 minutos para configurar nada — se travar, abandona em 5 minutos" |
| "Tem ensino superior" | "Cursou 2 anos de Administração, parou para abrir o negócio. Lê Estadão e Folha. Não consome conteúdo de tech." |
| "Renda de R$ 5-15k" | "Renda familiar R$ 8-15k, tira pró-labore variável conforme caixa, 60% do investimento na empresa vem de capital próprio (não financiamento)" |

### 3.2 Teste de utilidade

Para cada persona, perguntar: "Se eu mostrar feature X para essa persona, ela diria YES, NO ou MEH?"

Se você não consegue responder com confiança, persona é ornamental.

---

## 4. Estrutura mínima de persona

```yaml
persona:
  # ─── Identificação ───
  id: "P-001"
  name: "Bruna do Atacarejo"           # nome com mnemonic, não Maria genérica
  archetype: "Empresária de comércio físico em transição digital"
  category: "primary"                   # primary | secondary | anti

  # ─── Demografia (mínimo necessário) ───
  demographics:
    age_range: "32-45"
    location: "Cidades 50-300k habitantes, periferia metropolitana"
    education: "Ensino médio completo, alguma faculdade não terminada"
    income_personal: "R$ 3-8k/mês (pró-labore variável)"
    income_household: "R$ 8-15k/mês"
    family: "Casada, 2 filhos adolescentes, marido CLT"

  # ─── Contexto profissional ───
  professional_context:
    role: "Dona / única gestora"
    business_type: "Atacarejo de produtos de limpeza"
    business_size: "2 funcionários (uma vendedora + um repositor)"
    business_revenue: "R$ 30-100k/mês"
    business_age: "5-12 anos"
    digital_maturity_score: 3.5         # 1-10 (1 = analógico, 10 = digital nativo)

  # ─── Stack atual ───
  current_tools:
    primary:
      - "WhatsApp Business" (uso diário)
      - "Excel básico" (controle de estoque)
      - "PDV físico simples" (caixa)
    secondary:
      - "Instagram pessoal e do negócio" (2x/semana)
      - "Google" (busca)
    avoided:
      - "ERPs grandes (TOTVS, Conta Azul)" — caro, complexo
      - "Notion, Airtable" — não conhece
      - "Apps de finanças pessoais" — desconfia ("e se vazar?")

  # ─── Goals em ordem de prioridade ───
  goals_in_priority_order:
    - id: "G1"
      goal: "Aumentar vendas sem contratar mais gente"
      time_horizon: "6-12 meses"
    - id: "G2"
      goal: "Saber se está dando lucro de verdade (não ilusão de caixa)"
      time_horizon: "Imediato"
    - id: "G3"
      goal: "Não depender só do bairro (alcançar mais cidades)"
      time_horizon: "12-24 meses"
    - id: "G4"
      goal: "Reduzir tempo gasto em tarefas operacionais"
      time_horizon: "3-6 meses"
    - id: "G5"
      goal: "Ter sucessão clara para os filhos (negócio não morre com ela)"
      time_horizon: "10+ anos"

  # ─── Frustrações ordenadas ───
  frustrations_in_priority_order:
    - id: "F1"
      frustration: "Nunca sabe se o lucro é real ou ilusão"
      pain_intensity: 9                  # 1-10
      frequency: "diária"
    - id: "F2"
      frustration: "Marca apenas no caderno, perde controle"
      pain_intensity: 7
      frequency: "semanal"
    - id: "F3"
      frustration: "Concorrentes online estão tomando clientes"
      pain_intensity: 8
      frequency: "constante"
    - id: "F4"
      frustration: "Não tem tempo para aprender ferramenta nova"
      pain_intensity: 7
      frequency: "constante"

  # ─── Padrões comportamentais ───
  behavioral_patterns:
    decision_making:
      - "Toma decisão emocional, depois racionaliza"
      - "Confia mais em indicação de outro empresário do que em ad"
      - "Pesquisa por 3-7 dias antes de comprar produto digital"
    digital_behavior:
      - "Abandona produto se travar nos primeiros 5 minutos"
      - "Chama os filhos adolescentes para 'ajudar com tecnologia'"
      - "Prefere vídeo (YouTube) a artigo escrito"
      - "Usa celular >70% do tempo (não desktop)"
    communication:
      - "WhatsApp é canal principal (não email)"
      - "Liga para o suporte se travar (não abre ticket)"
      - "Boca a boca é canal de marketing principal"

  # ─── Use cases dentro do app ───
  use_cases_in_app:
    primary: "Conferir vendas do dia em 30 segundos"
    secondary: "Mandar lista de produtos para clientes recorrentes"
    tertiary: "Ver quem deve para ela"
    not_used: "Configurações avançadas, integrações com APIs, exportar para Excel"

  # ─── Citações reais (de entrevistas) ───
  verbatim_quotes:
    - quote: "Eu tô vendendo, mas não sei se tô lucrando."
      context: "Sobre frustração F1"
    - quote: "Se demorar mais de 5 minutos pra eu entender, eu desisto e volto pro caderno."
      context: "Sobre comportamento digital"
    - quote: "Confio quando minha amiga Renata me indicou. Senão, não."
      context: "Sobre decision making"

  # ─── Anti-persona (quem NÃO é) ───
  anti_persona:
    - "NÃO é dev/PJ tech (Pedro o founder de SaaS NÃO é Bruna)"
    - "NÃO tem time de marketing"
    - "NÃO vai aprender atalhos de teclado"
    - "NÃO entende jargão financeiro (EBITDA, churn)"
    - "NÃO usa Mac"
    - "NÃO mexe com cripto"

  # ─── Métricas que importam pra ela ───
  success_metrics_for_her:
    - "R$ no fim do mês maior que mês passado"
    - "Tempo gasto em planilha menor"
    - "Filhos ainda confiam que ela sabe gerir o negócio"

  # ─── Sources ───
  sources:
    interviews_count: 8
    interviews_dates: "2026-04-05 a 2026-04-22"
    quantitative_validation: "n=87, IBGE filtro PME comércio físico"
    last_updated: "2026-04-29"
```

---

## 5. Processo de criação

### 5.1 Passo 1 — Decidir se persona é necessária

Não toda situação pede persona. Validar:

- [ ] Produto tem usuário externo identificável? (B2C, B2B com >1 user role)
- [ ] Decisões de UI/UX precisam ser feitas? (não só backend)
- [ ] Há mais de um perfil potencial competindo?
- [ ] Time precisa alinhar entendimento?

Se <3 sim, persona é overkill. Use `meta/jobs-to-be-done` direto.

### 5.2 Passo 2 — Coletar dado real

Mínimo obrigatório:
- **5+ entrevistas qualitativas profundas** (60-90 min cada)
- **1 análise quantitativa** (analytics, survey n>50)
- **3+ observações em campo** (se possível visitar local de uso)

**Checklist da entrevista:**

```
□ Gravada (com consentimento)
□ Transcrita ou com notas detalhadas
□ Pessoa real do segmento (não amigo do fundador)
□ Cobre contexto + problema + alternativas + outcome
□ Pelo menos 3 citações verbatim capturadas
```

### 5.3 Passo 3 — Síntese (encontrar padrões, não estereótipos)

#### 3.1 Coding qualitativo

Para cada entrevista, atribuir tags:

```
Bruna:
  - business_type: comércio físico
  - digital_maturity: baixa
  - decision_speed: lenta (3-7 dias)
  - main_frustration: lucro invisível
  - communication_channel: WhatsApp
  - ...

Carlos:
  - business_type: serviços B2B
  - digital_maturity: média
  - decision_speed: média
  - main_frustration: cobrança lenta
  - communication_channel: email + WhatsApp
  - ...
```

#### 3.2 Encontrar clusters

Após 5+ entrevistas, agrupar por similaridade comportamental (não demográfica).

```
Cluster 1: "Comerciante físico de baixa maturidade digital" (4 entrevistadas)
  - Bruna, Marisa, Renata, José
  - Comportamento: abandona em 5min, confia em indicação, usa celular

Cluster 2: "Prestador de serviço B2B" (2 entrevistados)
  - Carlos, Felipe
  - Comportamento: diferente (usa email, decide em <2 dias, mais técnico)
```

**Regra:** cluster precisa ter ≥3 pessoas para virar persona. Cluster com 1-2 = caso isolado, não persona.

#### 3.3 Para cada cluster, formular persona

Aplicar template da seção 4. Mínimo: nome com mnemonic + arquétipo + 5 campos preenchidos.

### 5.4 Passo 4 — Hierarquizar

Numa pesquisa típica, surgem 2-5 personas potenciais. **Hierarquize:**

| Categoria | % do volume | Implicação |
|---|---|---|
| **Persona primária** | 60-70% | UI/UX é projetada para ela. Trade-offs vão a favor dela. |
| **Persona secundária** | 20-30% | Não pode ser excluída, mas em conflito perde |
| **Persona "anti"** | 5-10% | Deixar EXPLÍCITO quem NÃO é atendido. Evita scope creep |

**Regra:** Mais de 5 personas? Você está fragmentando demais. Volte e cluster melhor.

### 5.5 Passo 5 — Validar quantitativamente

Personas qualitativas (5 entrevistas) viram **hipótese**.

Para virar **fato**, validar com survey n>50:

```
Survey:
  1. Você se identifica como "Empresária de comércio físico"? (sim/não)
  2. Sua maior frustração no negócio é "saber se está dando lucro"? (sim/não)
  3. Você usaria solução que custa R$ 99/mês para resolver isso? (sim/não)
  4. ...
```

Se <60% confirmam o perfil hipotético, persona não é representativa. Volte para entrevista.

### 5.6 Passo 6 — Documentar e disseminar

```
docs/
├── personas/
│   ├── INDEX.md              # lista de personas
│   ├── persona-bruna.md      # primary
│   ├── persona-carlos.md     # secondary
│   └── anti-persona-pedro.md # explicit out
```

Cada PLAN.md cita persona afetada. Cada `/gsd-bootstrap` revisa lista.

---

## 6. Templates copy-paste

### 6.1 Roteiro de entrevista (60-90 min)

```markdown
# Entrevista — [Nome] — [Data]

## Bloco 1 — Contexto (10 min)

- Me conta sobre seu trabalho/negócio.
- Como é um dia típico?
- Quem está envolvido (sócios, funcionários, família)?

## Bloco 2 — Problema (20 min)

- Qual a maior dificuldade do dia a dia?
- Me conta a última vez que isso aconteceu.
- Como você lida hoje?
- O que tentou antes?

## Bloco 3 — Decisão (20 min)

- Como você decidiu experimentar [produto similar]?
- Quem mais influenciou a decisão?
- O que considerou e descartou?
- O que faria você abandonar [solução atual]?

## Bloco 4 — Comportamento digital (15 min)

- Quais apps você usa todo dia?
- O que considera "fácil" e "difícil" em apps?
- Onde busca informação quando trava?
- Você prefere vídeo, texto, ou ligar para alguém?

## Bloco 5 — Aspirações (10 min)

- Onde quer estar daqui a 2 anos?
- O que está te impedindo?
- Como mediria sucesso?

## Bloco 6 — Sondagem livre (10-15 min)

- O que eu deveria ter perguntado e não perguntei?
- Tem algo que eu precise entender melhor?
```

### 6.2 Persona summary (1-pager para parede)

```markdown
# Bruna do Atacarejo (P-001) — primary persona

> "Eu tô vendendo, mas não sei se tô lucrando."

**Quem é:** Empresária 32-45 anos, comércio físico, R$ 30-100k/mês, sem time financeiro.

**Dor principal:** Lucro invisível — Excel não funciona, contador chega tarde demais.

**Goal:** Ter número confiável de lucro mensal em <3 dias.

**Comportamento:**
- Mobile-first (>70% celular)
- Abandona se travar em 5 min
- Confia em indicação, não ad
- WhatsApp é canal principal

**Anti-persona:** Pedro (founder tech) — Conta Azul atende ele.

**Use case primário:** Conferir vendas do dia em 30s.

**Capacidade de pagar:** R$ 50-150/mês.

---

**Aplicação:**
✅ Phase atende Bruna se: simplifica, é mobile-first, mostra resultado em <3 dias.
❌ Phase NÃO atende Bruna se: pede integração com ERP, exige config 30+ min, é desktop-only.
```

### 6.3 Persona priorization matrix

Quando há múltiplas personas e precisa decidir prioridade:

```markdown
# Matriz de Priorização de Personas

## Critérios

1. **Volume:** quantos usuários estão neste perfil?
2. **Willingness to pay:** quão dispostos a pagar?
3. **Strategic fit:** alinha com vision do produto?
4. **Reach:** facilidade de alcançar (canal, custo de aquisição)?
5. **Defensibility:** se atendermos bem, criamos moat?

## Scoring (1-5 cada)

| Persona | Volume | WTP | Fit | Reach | Defense | Total |
|---|---|---|---|---|---|---|
| Bruna (Atacarejo) | 5 | 3 | 5 | 4 | 4 | **21** |
| Carlos (Serviços) | 3 | 4 | 4 | 3 | 3 | 17 |
| Pedro (Tech founder) | 2 | 5 | 2 | 5 | 2 | 16 |
| João (Restaurante) | 4 | 2 | 3 | 2 | 2 | 13 |

## Decisão

- **Primary:** Bruna (21) → 70% de foco
- **Secondary:** Carlos (17) → 25% de foco
- **Tertiary:** Pedro (16) → 5% (não bloqueia se não atende)
- **Anti-persona:** João (não viável agora, custo de servir > willingness to pay)
```

### 6.4 Validation card para feature

Antes de aprovar phase, rodar:

```markdown
# Validação contra Personas — Phase [N]

## Persona primária afetada
- [ ] Bruna (P-001)? **Sim / Não**

## Verificações
- [ ] Feature atende goal G1, G2 ou G3 da Bruna? **Qual:** ___
- [ ] Feature respeita comportamento digital (mobile-first, <5min de fricção)?
- [ ] Feature usa linguagem da Bruna (não jargão)?
- [ ] Feature tem path "para iniciante" (sem assumir maturidade digital alta)?
- [ ] Feature NÃO entra em conflito com anti-persona?

## Trade-off (se afeta múltiplas personas)
- Bruna ganha: ___
- Carlos perde: ___
- Justificativa para favorecer Bruna: ___
```

---

## 7. Anti-patterns com correção

### Anti-pattern 1: Persona inventada sem entrevista

```
❌ ERRADO:
Time se reúne, escreve persona "do que acha que é o usuário".

✅ CORRETO:
Time conduz 5+ entrevistas com pessoas reais do segmento.
Persona sai dos padrões observados, não da imaginação.
```

### Anti-pattern 2: Persona só com demografia

```
❌ ERRADO:
"Maria, 35 anos, classe B, mora em SP, casada, 2 filhos."

✅ CORRETO:
"Bruna, dona de atacarejo, abandona apps em 5min, prefere WhatsApp,
confia em indicação de outra empresária, gasta R$ 50-150/mês em apps."
```

Demografia sozinha não orienta decisão. Comportamento sim.

### Anti-pattern 3: Persona única quando há múltiplos públicos

```
❌ ERRADO:
"Nossa persona é 'pequenos empresários'."
(Cobre comércio + serviços + tech + agronegócio = ninguém)

✅ CORRETO:
"Persona primária: Bruna (comércio físico). Persona secundária: Carlos (serviços B2B).
Anti-persona: Pedro (tech founder) — Conta Azul atende."
```

### Anti-pattern 4: Mais de 5 personas

```
❌ ERRADO:
"Temos 8 personas: Maria, Pedro, João, Ana, Carlos, Renata, José, Felipe."
(Vira lista, não orienta)

✅ CORRETO:
Cluster melhor. 5+ personas = está fragmentando.
Reagrupar por comportamento similar.
```

### Anti-pattern 5: Pular anti-persona

```
❌ ERRADO:
"Nosso produto é para empreendedores em geral."
(Tenta servir todo mundo, não serve ninguém)

✅ CORRETO:
"Servimos: Bruna (comércio físico) e Carlos (serviços).
NÃO servimos: Pedro (tech founder), João (restaurante), Ana (e-commerce nativo)."
```

### Anti-pattern 6: Persona estática

```
❌ ERRADO:
Persona criada em 2024 nunca foi revisada.
Comportamento real do usuário em 2026 é diferente.

✅ CORRETO:
Revisar persona a cada 6 meses ou quando dado de uso real
divergir significativamente do esperado.
```

### Anti-pattern 7: Persona genérica copiada da internet

```
❌ ERRADO:
Persona "millennial urbano" copiada de blog de marketing.

✅ CORRETO:
Persona específica do SEU produto, baseada em entrevistas com SEUS usuários.
```

---

## 8. Personas para 5 domínios diferentes

### Exemplo 1 — Áugure (B2B SaaS)

**Bruna do Atacarejo (P-001) — primary**
- Vide template completo na seção 4

**Carlos do Engenheiro (P-002) — secondary**
```yaml
archetype: "Empresário de serviços B2B"
demographics:
  age_range: "35-50"
  education: "Ensino superior completo"
  income_household: "R$ 15-30k/mês"
business:
  type: "Engenharia consultiva"
  size: "5-15 funcionários"
  revenue: "R$ 100-500k/mês"
  digital_maturity: 6
behavior:
  - "Decide em 1-2 dias (não 7)"
  - "Pesquisa por análise (não indicação)"
  - "Email é canal principal"
  - "Usa LinkedIn"
goals:
  - "Aumentar margem em projetos"
  - "Reduzir prazo de cobrança"
frustrations:
  - "Cliente atrasa pagamento"
  - "Não tem visibilidade de pipeline"
willingness_to_pay: "R$ 200-500/mês"
```

**Pedro do SaaS Founder (P-003) — anti-persona**
```yaml
why_not_target:
  - "Já tem ferramentas próprias (Stripe, Conta Azul)"
  - "Considera Áugure 'simples demais'"
  - "Usaria mas não pagaria nosso preço (acha caro)"
  - "Custo de servir > willingness to pay"
explicit_decision: "NÃO desenhar features para ele"
```

### Exemplo 2 — iFood (B2C marketplace)

**Joana do Apartamento (primary)**
- 28-38 anos, profissional CLT
- Renda R$ 5-12k
- Mora sozinha ou com parceiro, sem filhos
- Pede 2-4x por semana, 19h-21h
- Spend mensal: R$ 250-600
- Critérios: prazo, variedade, preço total transparente
- Anti-persona: estudante (sensibilidade a preço >> qualidade)

**Fernando do Pai-Mãe (secondary)**
- 32-45 anos, casado, 1-3 filhos
- Renda familiar R$ 15-40k
- Pede sexta-feira (jantar família) e domingo (almoço)
- Spend mensal: R$ 400-1500
- Critérios: variedade para família, segurança alimentar, promoções
- Diferenças vs Joana: pedidos maiores, mais exigente com qualidade, usa cupom

### Exemplo 3 — Slack (B2B)

**Tech Lead Renata (primary)**
- 28-40 anos, eng software
- Empresa 20-200 pessoas
- Decisor de compra de tools de dev
- Comportamento: testa free, vira advocate, traz time
- WTP: $8-15/user/mês
- Anti-persona: empresa Fortune 500 (longo ciclo, vendas enterprise)

**HR/Comms (secondary)**
- 30-50 anos, RH ou comunicação interna
- Empresa 50-500 pessoas
- Decisor para uso amplo (não só dev)
- Comportamento: avalia compliance, integração, suporte
- WTP: $5-10/user/mês

### Exemplo 4 — Stripe (B2B infra)

**Founder Técnico (primary)**
- 25-40 anos, dev fundador
- Produto digital ou marketplace
- Faz integração ele mesmo
- WTP: 2.9% + $0.30 por transação (padrão)
- Anti-persona: enterprise com time de payments próprio (vai usar Adyen, Worldpay)

### Exemplo 5 — Notion (B2C+B2B)

**Knowledge Worker Solo (primary)**
- 25-40 anos, freelancer/contractor
- Profissão: design, writing, consulting
- Usa para "second brain" pessoal
- WTP: $0-15/mês
- Anti-persona: time grande de eng (vai usar Confluence)

---

## 9. Como persona vira input para outras skills

### 9.1 → `meta/jobs-to-be-done`

Persona define QUEM. JTBD define QUE JOB ela contrata.

```
Persona: Bruna (P-001)
↓
JTBD-001: "Saber lucro real"
JTBD-002: "Atender cliente físico em <30s no caixa"
JTBD-003: "Decidir abrir filial ou não"
```

Uma persona contrata múltiplos JTBDs ao longo do tempo.

### 9.2 → `meta/journey-map`

Cada persona tem journey próprio.

```
Journey de Bruna:
Trigger: marido cobrou sobre lucro
↓
Pesquisa "como saber lucro de pequena empresa"
↓
Acha Áugure no Google
↓
Hesita ("será que entendo?")
↓
Vê depoimento de outra empresária
↓
Free trial 7 dias
↓
Onboarding (precisa funcionar em 5min)
↓
Conferiu primeiro relatório
↓
Aha moment: "agora sei!"
↓
Conversion para paid
↓
Aderência (verifica diariamente)
```

### 9.3 → PLAN.md de phase

Toda phase declara persona afetada:

```markdown
## Phase 4 — Mobile dashboard simplificado

### Persona afetada
- Primary: Bruna (P-001)
- Secondary: Carlos (P-002)
- Anti-persona: Pedro (P-003) — não desenhar para ele

### Como atende cada persona
- Bruna: dashboard fica em mobile-first, simplificado, abre em <2s
- Carlos: pode usar mas tem path "modo avançado" (não default)
- Pedro: NÃO atendido (decisão consciente)
```

### 9.4 → `quality/heuristic-evaluation`

Audit de UX é feito CONTRA a persona, não contra "user genérico".

```
Heuristic 6 (Reconhecimento ao invés de memorização):
  Para Bruna (digital_maturity=3.5): CRÍTICO. Não pode exigir memorizar nada.
  Para Pedro (digital_maturity=8): tolerável usar atalhos.
```

### 9.5 → Pricing decision

Persona define WTP máximo.

```
Bruna WTP: R$ 50-150/mês
Carlos WTP: R$ 200-500/mês

Conclusão: pricing tier 1 = R$ 99/mês (Bruna), tier 2 = R$ 299/mês (Carlos)
```

---

## 10. Checklist de validação

```
□ Persona tem nome com mnemonic (não Maria genérica)?
□ Demografia está conectada a comportamento (não isolada)?
□ Tem 5+ goals priorizados?
□ Tem 5+ frustrations com pain_intensity?
□ Tem padrões comportamentais OBSERVADOS (não inferidos)?
□ Tem 3+ citações verbatim de entrevistas reais?
□ Tem stack atual mapeada (tools usadas e evitadas)?
□ Tem use cases claros (primary/secondary/tertiary/not_used)?
□ Tem anti-persona definida?
□ Tem WTP estimada?
□ Validada quantitativamente (n>50)?
□ Tem succession metrics (como ELA mede sucesso)?
□ Foi atualizada nos últimos 6 meses?
□ Está categorizada (primary/secondary/anti)?
□ Está em docs/personas/ versionada em git?
```

Se <12 checks, persona é hipótese. Mais entrevistas + survey antes de assumir.

---

## 11. Erros comuns de implementação

### Erro 1: Persona na parede mas não no PLAN
Igual JTBD. Vira ornamento. **Fix:** template de PLAN tem campo "Persona afetada".

### Erro 2: Mudar persona toda semana
Time perde norte. **Fix:** mudança = ADR formal + 5+ entrevistas novas evidenciando.

### Erro 3: Designer cria persona sozinho
Persona é DO TIME, não do designer. **Fix:** workshop com fundadores, dev, suporte.

### Erro 4: Persona com foto stock
"Maria, 35 anos" + foto Shutterstock. Vira piada interna. **Fix:** sem foto. Use ilustração mnemônica ou só nome+arquétipo.

### Erro 5: Sem anti-persona explícita
Sem definir quem NÃO atender, scope creep destrói o produto. **Fix:** anti-persona é obrigatória.

### Erro 6: Persona sem WTP
Decisões de pricing ficam no chute. **Fix:** WTP é campo obrigatório, validado em entrevista.

---

## 12. Como validar aplicação real (não só citação)

**Sinais de aplicação real:**
✅ PLAN.md tem campo "Persona afetada" preenchido com persona_id
✅ Justificativa de design cita comportamento da persona ("Bruna abandona em 5min, então...")
✅ Mockups têm linguagem da persona, não corporativa
✅ Verification testa com pessoa REAL desse perfil (UAT direcionado)

**Sinais de citação ornamental:**
❌ "Esta phase atende a persona" sem persona_id
❌ Justificativa vaga ("usuários valorizam isso")
❌ Linguagem técnica/corporativa quando persona é Bruna
❌ Verification = "código funciona"

---

## 13. Persona evolution roadmap

Personas mudam com:
- Crescimento do produto (adquire novos perfis)
- Mudanças de mercado (recessão muda WTP)
- Aprendizados de uso (analytics revela comportamento real)
- Pivots

**Frequência de revisão:**

| Stage do produto | Frequência |
|---|---|
| Pré-MVP | Cada 2-4 semanas |
| MVP | Cada 6-8 semanas |
| Produto estável | Cada 6 meses |
| Pivot/big change | Imediato |

**Como revisar:**
1. Olhar dado quantitativo (analytics, surveys)
2. Comparar com persona atual
3. Se divergência >20%, fazer 3-5 entrevistas novas
4. Atualizar persona OU criar nova
5. ADR documentando a mudança

---

## 14. Frameworks adjacentes

| Framework | Quando usar |
|---|---|
| **Personas (Cooper)** | Design de UX (esta skill) |
| **Buyer personas (HubSpot)** | Marketing de conteúdo |
| **Customer Segments (BMC)** | Modelo de negócio |
| **Empathy Map** | Síntese rápida de pesquisa |
| **JTBD** | Motivação por trás do uso |
| **User Stories (Agile)** | Implementação técnica |

---

## 15. Integração com fluxo gsd

```
gsd-bootstrap → 5+ entrevistas + survey n>50
                            ↓
                cluster por comportamento
                            ↓
                3-5 personas (primary + secondary + anti)
                            ↓
                docs/personas/persona-*.md
                            ↓
                cada PLAN cita persona_id afetada
                            ↓
                heuristic-eval audita contra persona
                            ↓
                verify-work com UAT da persona real
                            ↓
                milestone-summary mede outcomes por persona
                            ↓
                a cada 6 meses: revisar com dado novo
```

---

## 16. Referências

- **Alan Cooper** — "The Inmates Are Running the Asylum" (1999) — origem das personas
- **Indi Young** — "Practical Empathy" (2015) — entrevistas de UX profundas
- **Steve Portigal** — "Interviewing Users" (2013) — técnicas de entrevista
- **Erika Hall** — "Just Enough Research" (2013) — pesquisa lean para produtos

---

**Última atualização:** v0.7.0 (densificação)
**Densidade:** 16 seções, 5 personas exemplos completos, anti-patterns com correção, 4 templates copy-paste, checklist de 15 itens
