---
name: heuristic-evaluation
category: quality
description: Avaliação heurística de UX baseada nas 10 heurísticas de Nielsen + critérios de domínio. Detecta 60-80% dos problemas de usabilidade ANTES de teste com usuário. Inclui checklists, severity scale, templates de relatório, exemplos por heurística e como integrar com fix iterations.
---

# Heuristic Evaluation — Avaliação Heurística

> Audit estruturado de UX feito por especialista (não usuário). Detecta 60-80% dos problemas de usabilidade ANTES de gastar com teste com usuário ou pior, ANTES de release.

Esta skill é o gate de qualidade pré-release de qualquer phase com UI.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| `/gsd-verify-work` em phase com UI | Audit antes de marcar phase como done |
| `/gsd-audit-milestone` em milestones com UI | Consolidação no fim do milestone |
| Antes de release público | Último checkpoint |
| Após code review aprovar | Code review checa código, não UX |
| Em phase de redesign | Identificar dores antes de redesenhar |

## 2. Diferença vs outros tipos de audit

| Audit | O que avalia | Quem faz | Quando |
|---|---|---|---|
| **Heuristic Evaluation** | UX/usabilidade | Especialista | Pré-release |
| **Accessibility audit** | WCAG, a11y | axe + humano | Pré-release |
| **Code review** | Qualidade do código | Outro dev | Durante phase |
| **User testing** | Comportamento real | Usuário real | Após release ou prototype |
| **Analytics audit** | Métricas de uso | Analytics tool | Pós-release |

Heuristic eval **complementa** outros, não substitui.

---

## 3. As 10 heurísticas de Nielsen

### Heurística 1 — Visibilidade do estado do sistema

> Sempre informar onde o usuário está, o que está acontecendo, o resultado de ações.

**Boas práticas:**
- Loading states em ações >100ms
- Confirmação após ação (toast)
- Breadcrumbs em navegação profunda
- Indicador de progresso em operações longas
- Status indicators (online/offline, salvando/salvo)

**Exemplos:**

```
✅ "Salvando rascunho..." → "Rascunho salvo às 14:32"
✅ Botão de submit fica disabled + spinner durante request
✅ Upload de arquivo mostra % de progresso

❌ Botão clicado, nada acontece visualmente, sem feedback
❌ Ação completa em 3s sem nenhum indicador
❌ Erro silencioso (request falhou, UI parece ok)
```

**Checklist específico:**

```
□ Toda ação tem feedback visual em <100ms?
□ Operações >2s mostram loading explícito?
□ Estados (online, salvo, erro) são visíveis?
□ Posição do usuário no app é clara (active nav, breadcrumb)?
```

### Heurística 2 — Match entre sistema e mundo real

> Linguagem do usuário, não jargão técnico. Conceitos familiares.

**Boas práticas:**
- Termos do domínio do usuário (não do dev)
- Ícones reconhecíveis (lixeira pra deletar, casa pra home)
- Ordem natural (primeiro nome, sobrenome — não "snd_nm")
- Datas no formato regional (dd/mm/aaaa em pt-BR)
- Moeda local (R$ 1.234,56)

**Exemplos:**

```
✅ "Cancelar assinatura"
❌ "Deactivate subscription entity"

✅ "Você foi banido"
❌ "Forbidden 403"

✅ "Pedido entregue em 30 min"
❌ "Status: DELIVERED, ETA: 1800000ms"

✅ "R$ 99,90/mês"
❌ "9990 cents/mo"
```

**Checklist específico:**

```
□ Sem jargão técnico em UI (deactivated, fetched, persisted, queue, etc.)?
□ Datas no formato regional (dd/mm/aaaa em pt-BR)?
□ Moeda no formato regional (R$ 1.234,56)?
□ Terminologia consistente com domínio do usuário?
□ Ícones convencionais (não invenção)?
```

### Heurística 3 — Controle e liberdade do usuário

> Saídas de emergência: undo, cancel, voltar, sair sem perda.

**Boas práticas:**
- Botão "Voltar" sempre visível em fluxos
- Modal tem botão fechar visível (X no canto)
- Undo após ações destrutivas (toast com botão Desfazer)
- ESC fecha modal
- Salvar rascunho automático (form longo)

**Exemplos:**

```
✅ "Item movido para lixeira. Desfazer (10s)"
✅ Modal com X visível + Esc para fechar
✅ Wizard com botões "Anterior" e "Continuar"
✅ Edit-in-place que volta ao estado anterior se cancelar

❌ Modal sem botão fechar (só "Confirmar")
❌ Delete permanente sem confirmação nem undo
❌ Form longo que perde dados se navegação ocorrer
```

**Checklist específico:**

```
□ Toda modal tem botão de fechar visível?
□ Tecla ESC fecha modal?
□ Ações destrutivas têm confirmação OU undo?
□ Forms longos auto-salvam rascunho?
□ Wizards permitem voltar a passo anterior sem perda?
```

### Heurística 4 — Consistência e padrões

> Mesma palavra, mesma cor, mesmo lugar para mesma ação. Em todo o app.

**Boas práticas:**
- Botão primário sempre mesma cor (brand)
- "Salvar" sempre à direita, "Cancelar" à esquerda (ou vice-versa, mas consistente)
- Ícones têm 1 significado (engrenagem = config sempre)
- Padrões da plataforma (iOS swipe, Android back button)

**Exemplos:**

```
✅ Botão de submit sempre azul brand, primário, à direita
✅ Ícone de lixeira sempre = deletar (não às vezes "fechar")
✅ Modal de confirmação sempre com mesma estrutura

❌ Submit às vezes verde, às vezes azul, às vezes à esquerda
❌ Ícone de "+" às vezes adiciona, às vezes expande
❌ Modal de erro com layout diferente do modal de sucesso
```

**Checklist específico:**

```
□ Botão primário tem mesma cor/estilo em toda app?
□ Ações similares (criar, editar, deletar) têm padrão visual?
□ Posição de botões (primário/secundário) é consistente?
□ Ícones têm significado único e consistente?
□ Padrões de plataforma respeitados (iOS, Android, web)?
```

### Heurística 5 — Prevenção de erros

> Eliminar condição que causa erro ANTES de mostrar erro.

**Boas práticas:**
- Datepicker não permite passado em "data de viagem"
- Input mask em CPF, CEP, telefone
- Validação inline em forms (não só no submit)
- Confirmação antes de ações destrutivas
- Defaults inteligentes

**Exemplos:**

```
✅ Datepicker desabilita datas inválidas
✅ CPF com máscara automática (xxx.xxx.xxx-xx)
✅ Botão de submit só habilita quando form válido
✅ "Tem certeza? Esta ação é irreversível" antes de delete

❌ Aceita data passada, depois mostra "data inválida"
❌ Aceita CPF mal formatado, depois rejeita
❌ Permite submit de form vazio
❌ Delete sem confirmação
```

**Checklist específico:**

```
□ Inputs têm máscaras para formatos brasileiros (CPF, CNPJ, CEP, telefone)?
□ Datepickers limitam range (ex: passado bloqueado)?
□ Validação inline (on blur) antes de submit?
□ Submit disabled até form válido?
□ Ações destrutivas têm confirmação?
```

### Heurística 6 — Reconhecimento ao invés de memorização

> Mostrar opções, não exigir lembrar.

**Boas práticas:**
- Dropdowns com últimas opções usadas
- Autocomplete em campos comuns
- Histórico visível (últimas pesquisas)
- Templates pré-preenchidos
- Hints contextuais

**Exemplos:**

```
✅ Dropdown com últimos 5 endereços usados
✅ Autocomplete de cidade ao digitar 3 letras
✅ "Recente" tab em buscador
✅ Form de contato com nome auto-preenchido se logado

❌ Campo livre exigindo digitar código exato
❌ "Use o atalho Ctrl+K" sem mostrar visualmente
❌ Lista de 50 países sem busca/agrupamento
```

**Checklist específico:**

```
□ Dropdowns mostram opções (não pedem para digitar exato)?
□ Autocomplete em campos com muitas opções?
□ Histórico de uso visível (últimas pesquisas, items recentes)?
□ Defaults inteligentes (campos pré-preenchidos)?
□ Hints contextuais (placeholders, helper text)?
```

### Heurística 7 — Flexibilidade e eficiência de uso

> Atalhos para experts sem atrapalhar novatos.

**Boas práticas:**
- Atalhos de teclado (Ctrl+S, Ctrl+K)
- Bulk actions (selecionar múltiplos)
- Customização (favorites, ocultar colunas)
- Duplicar item ou template

**Exemplos:**

```
✅ Ctrl+Enter envia mensagem (mas botão também existe)
✅ Selecionar 10 emails de uma vez para deletar
✅ Salvar query como "favorita"

❌ Só atalho de teclado, sem botão visível
❌ Tem que deletar item por item (sem multi-select)
❌ Toda ação repetida exige refazer do zero
```

**Checklist específico:**

```
□ Atalhos de teclado para ações frequentes (não obrigatórios)?
□ Bulk actions onde faz sentido (lista de items)?
□ Customização básica (favoritos, ocultar colunas, layout)?
□ Templates ou duplicar para reuso?
```

### Heurística 8 — Design estético e minimalista

> Cada elemento extra compete com o relevante. Cortar.

**Boas práticas:**
- Hierarquia visual clara (1 ação primária por tela)
- Espaço em branco generoso
- Tipografia limpa
- Cor brand restrita ao essencial

**Exemplos:**

```
✅ Tela de checkout só com campos essenciais
✅ 1 CTA primária por tela
✅ Sidebar com 5-7 itens de menu

❌ Checkout com banner promocional + ad de outro produto + sidebar
❌ 5 botões "primários" competindo
❌ Sidebar com 25 itens, todos no mesmo nível
```

**Checklist específico:**

```
□ Cada tela tem 1 ação primária clara?
□ Espaço em branco adequado (não claustrofóbico)?
□ Hierarquia visual: 1 cor brand + cinzas?
□ Sem elementos decorativos sem propósito?
```

### Heurística 9 — Mensagens de erro úteis

> Ajudar usuários a reconhecer, diagnosticar e recuperar de erros.

**Boas práticas:**
- Linguagem clara, sem código de erro
- Descrever problema + sugerir solução
- Tom respeitoso (não culpar usuário)
- Recuperação fácil (botão de retry, link para suporte)

**Exemplos:**

```
✅ "Senha precisa ter 8+ caracteres com 1 número e 1 maiúscula"
✅ "Não foi possível conectar. Verifique sua internet e tente novamente. [Tentar de novo]"
✅ "Email já cadastrado. Esqueceu a senha? [Recuperar acesso]"

❌ "Erro 422: validation failed"
❌ "Senha inválida" (sem dizer como corrigir)
❌ "Erro inesperado" (sem ação)
```

**Checklist específico:**

```
□ Mensagens de erro em linguagem clara (não código)?
□ Cada erro sugere ação para resolver?
□ Tom respeitoso (não acusatório)?
□ Erros em pt-BR para usuários BR?
□ Erros têm botão/link para recuperar?
```

### Heurística 10 — Ajuda e documentação

> Documentação contextual, fácil de buscar, focada em tarefa do usuário.

**Boas práticas:**
- Help icons inline (tooltip)
- FAQ acessível
- Tutoriais contextuais (não só onboarding)
- Contato/chat de suporte visível

**Exemplos:**

```
✅ Help icon ao lado do campo "CFOP" com explicação inline
✅ FAQ no rodapé, organizado por seção
✅ Chat de suporte disponível em horário comercial
✅ Vídeos curtos (<2min) para fluxos complexos

❌ Manual PDF de 200 páginas
❌ Documentação só em inglês para usuário BR
❌ Sem help para campos técnicos (CFOP, CEST, NCM)
```

**Checklist específico:**

```
□ Help inline (tooltip) em campos técnicos/complexos?
□ FAQ ou Help Center acessível?
□ Documentação em pt-BR para usuário BR?
□ Suporte (chat, email) visível e acessível?
```

---

## 4. Severity Scale (escala Nielsen)

Para cada problema encontrado, atribuir severity:

```yaml
severity:
  0:  Não é problema
  1:  Cosmético (fix se sobrar tempo)
      Exemplo: "Espaço entre botões está 12px, deveria ser 16px"
  2:  Pequeno (prioridade baixa)
      Exemplo: "Tooltip aparece levemente atrasado"
  3:  Maior (prioridade alta)
      Exemplo: "Form perde dados se usuário voltar para tela anterior"
  4:  Catastrófico (fix obrigatório antes do release)
      Exemplo: "Submit sem feedback gera duplo pagamento"
```

**Decisão por severity:**

| Severity | Ação |
|---|---|
| 4 | Bloqueia release. Fix imediato. |
| 3 | Fix em phase atual ou próxima. |
| 2 | Entra em TECH-DEBT.md, fix em phase de polish. |
| 1 | Backlog, fix oportunístico. |
| 0 | Ignorar. |

---

## 5. Processo de avaliação

### 5.1 Passo 1 — Definir escopo

Não tente avaliar "o app inteiro". Defina:

- **Quais telas/fluxos** (1-5 fluxos por sessão)
- **Quais heurísticas** (todas 10 ou subset relevante)
- **Persona alvo** (heuristic 6 muda conforme expertise da persona)

**Exemplo:**

```
Escopo: avaliação heurística da Phase 4 — Checkout

Telas:
  - /carrinho
  - /checkout
  - /pagamento
  - /confirmacao

Heurísticas: todas 10
Persona: Bruna (digital_maturity=3.5)
Tempo estimado: 90-120 min
```

### 5.2 Passo 2 — Avaliar cada tela

Para cada tela, percorrer as 10 heurísticas.

**Para cada problema encontrado, anotar:**

```yaml
problem:
  id: "HE-001"
  heuristic: "1. Visibilidade do estado"
  severity: 4
  description: |
    Botão de "Confirmar Pagamento" não dá feedback após clique.
    Usuário pode clicar várias vezes, gerando duplo pagamento.
  location: "Tela /checkout/pagamento, botão Confirmar"
  steps_to_reproduce:
    - "Adicione item ao carrinho"
    - "Vá para checkout"
    - "Preencha cartão"
    - "Clique em Confirmar Pagamento"
    - "Note: nenhum loading, nenhum disable do botão"
  evidence: "screenshot-001.png"
  fix_suggestion: |
    1. Disable botão imediatamente após click
    2. Mostrar spinner inline ("Processando...")
    3. Após resposta, mostrar toast "Pagamento confirmado!"
    4. Usar idempotência no backend para garantir
  estimated_effort: "1h"
  related_skills:
    - ux-advanced/loading-states
    - ux-advanced/feedback-patterns
    - ux-advanced/payment-checkout-ux
```

### 5.3 Passo 3 — Compilar relatório

```markdown
# Heuristic Evaluation — Phase 4 (Checkout)

**Avaliador:** [nome]
**Data:** 2026-04-29
**Persona:** Bruna (P-001)
**Telas avaliadas:** /carrinho, /checkout, /pagamento, /confirmacao

## Resumo executivo

- **Problemas encontrados:** 12
  - Severity 4 (catastrófico): 2 ⛔ bloqueia release
  - Severity 3 (maior): 5 → fix em phase atual
  - Severity 2 (pequeno): 3 → tech debt
  - Severity 1 (cosmético): 2 → backlog

## Problemas por heurística

### Heurística 1 — Visibilidade do estado (3 problemas)

#### HE-001 [Severity 4] — Submit sem feedback gera duplo pagamento
[detalhes...]

#### HE-002 [Severity 3] — Status do pedido não atualiza em real-time
[detalhes...]

### Heurística 5 — Prevenção de erros (2 problemas)

#### HE-006 [Severity 4] — Aceita CPF inválido
[detalhes...]

[...]

## Recomendações priorizadas

### Imediato (bloqueia release)
1. HE-001: Loading state no submit do pagamento
2. HE-006: Validação de CPF antes do submit

### Próxima phase
3. HE-002: WebSocket para status do pedido
4. HE-007: Confirmação antes de cancelar carrinho
[...]

## Validação pós-fix

Após fixes implementados, re-avaliar as heurísticas afetadas.
```

### 5.4 Passo 4 — Salvar e linkar

```bash
# Salvar em
.planning/phases/04-checkout/04-HEURISTIC-EVAL.md

# Linkar em
.planning/phases/04-checkout/04-VERIFICATION.md
```

---

## 6. Templates copy-paste

### 6.1 Quick eval (30 min, 1 fluxo)

Quando não há tempo para audit completo:

```markdown
# Quick Heuristic Eval — [fluxo]

## Top 3 problemas encontrados

### #1 [Severity X] — [título]
**Heurística:** [1-10]
**Onde:** [tela]
**Problema:** [1-2 frases]
**Fix:** [1 frase]

### #2 [Severity X] — [título]
[...]

### #3 [Severity X] — [título]
[...]

## Heurísticas que estão BOAS

- [N]. [Heurística]: [evidência de que está ok]
- [N]. [Heurística]: [...]

## Recomendação

[ ] Pode seguir para release
[X] Fix #1 obrigatório antes de release
[ ] Re-avaliar após fixes
```

### 6.2 Full eval (2-4 horas, todas 10 heurísticas, múltiplos fluxos)

Vide seção 5.3 acima.

### 6.3 Comparative eval (avaliar app contra concorrente)

```markdown
# Comparative Heuristic Eval — [meu produto] vs [concorrente]

## Heurísticas onde [meu produto] está MELHOR

### Heurística 5 (Prevenção de erros)
- Meu produto: validação inline em todos os campos
- Concorrente: só valida no submit
- **Vantagem competitiva**

[...]

## Heurísticas onde [concorrente] está MELHOR

### Heurística 7 (Flexibilidade)
- Meu produto: sem atalhos de teclado
- Concorrente: Cmd+K para busca, Cmd+Enter para enviar
- **Lacuna a fechar**

[...]

## Conclusão competitiva

Atendemos [N] heurísticas melhor.
Estamos atrás em [M] heurísticas.
Prioridade: fechar lacunas em [...].
```

---

## 7. Checklists específicos por contexto

### 7.1 E-commerce (carrinho, checkout)

```
PREVENÇÃO DE ERROS (H5):
□ CPF, CEP, telefone com máscara automática?
□ Cartão valida número (Luhn) antes do submit?
□ Cupom inválido detectado antes de aplicar?
□ Quantidade não permite negativo?

VISIBILIDADE (H1):
□ Carrinho mostra quantidade total no header?
□ Checkout mostra qual etapa está (1/3, 2/3, 3/3)?
□ Submit de pagamento dá loading + feedback?

CONTROLE (H3):
□ Pode editar item do carrinho sem voltar?
□ Pode pausar e voltar depois (carrinho persiste)?
□ Pode cancelar checkout sem perder dados?
```

### 7.2 SaaS dashboard

```
RECONHECIMENTO (H6):
□ Filtros têm nomes descritivos?
□ Datas em formato regional?
□ Exportar para Excel é encontrável?

FLEXIBILIDADE (H7):
□ Bulk actions em listas?
□ Atalhos de teclado para ações frequentes?
□ Customização de colunas (mostrar/ocultar)?

ESTÉTICO (H8):
□ Densidade adequada (não claustrofóbico)?
□ Filtros agrupados logicamente?
□ Ações primárias destacadas?
```

### 7.3 Mobile app (Áugure por exemplo)

```
MATCH REAL WORLD (H2):
□ Termos brasileiros (CPF, CEP, "Lucro Líquido")?
□ Datas em dd/mm/aaaa?
□ Moeda em R$ 1.234,56?

CONTROLE (H3):
□ Gesture de voltar (swipe right) funciona?
□ Pull to refresh em listas?
□ Pode cancelar long-running operation?

PREVENÇÃO (H5):
□ Confirmação antes de pagamento?
□ Avisa antes de sair de form com dados?
□ Limita ações destrutivas em offline?
```

### 7.4 Form longo (cadastro, onboarding)

```
PREVENÇÃO (H5):
□ Auto-save de rascunho?
□ Validação inline (on blur)?
□ Indicador de progresso?

VISIBILIDADE (H1):
□ Quais campos são obrigatórios (asterisco ou label)?
□ Quanto falta (3/5 etapas)?
□ Erro de validação mostrado inline?

RECONHECIMENTO (H6):
□ Helper text para campos não-óbvios?
□ Auto-completar onde possível (CEP → endereço)?
□ Pré-preencher se logado?
```

---

## 8. Anti-patterns com correção

### Anti-pattern 1: Avaliação sem severity

```
❌ "Encontrei vários problemas. Aqui está a lista de 30 itens."

✅ "Severity 4: 2 problemas (bloqueiam release).
   Severity 3: 5 problemas (fix em phase).
   Severity 1-2: 23 problemas (tech debt + backlog)."
```

### Anti-pattern 2: Problema sem fix suggestion

```
❌ "Botão de submit não tem feedback."

✅ "Botão de submit não tem feedback.
   FIX: 1) disable após click, 2) spinner inline,
   3) toast após resposta, 4) idempotência backend."
```

### Anti-pattern 3: Avaliar sem persona definida

```
❌ "Heurística 6 falha — UI exige memorização."

✅ "Heurística 6 falha PARA Bruna (digital_maturity=3.5).
   Para Pedro (digital_maturity=8), tolerável.
   FIX prioritário porque persona primária é Bruna."
```

### Anti-pattern 4: Avaliar tudo

```
❌ "Vou avaliar o app inteiro." → 50h, ninguém lê o relatório.

✅ "Avaliação focada em Phase 4 (checkout). 90-120min.
   Próxima sessão: Phase 5 (perfil)."
```

### Anti-pattern 5: Avaliação sem follow-up

```
❌ Relatório de 30 problemas, nenhum corrigido.

✅ Severity 4 fixados antes de release.
   Severity 3 fixados em fix iteration.
   Severity 1-2 entram em TECH-DEBT.md.
   Re-eval após fixes para validar.
```

### Anti-pattern 6: Avaliar só um avaliador

Nielsen recomenda 3-5 avaliadores. Cada um pega 30-50% dos problemas. Juntos pegam 80-90%.

```
✅ 3 avaliadores diferentes. Consolidam findings em sessão de 30min.
```

---

## 9. Exemplos completos de findings

### 9.1 Áugure — Phase de simulação

```yaml
HE-001:
  heuristic: 1 (Visibilidade)
  severity: 4
  location: "/simular, durante processamento de 15min"
  problem: |
    Após enviar simulação, página mostra apenas spinner sem indicar
    quanto tempo falta. Em uma simulação de 15 minutos, usuário
    abandona pensando que travou.
  fix: |
    1. Mostrar progresso real (% completo)
    2. Tempo estimado restante
    3. Permitir fechar e receber notificação por email
    4. Salvar parcialmente se fechar
  effort: "4h"

HE-002:
  heuristic: 9 (Mensagens de erro)
  severity: 3
  location: "/simular, quando dado de mercado não existe"
  problem: |
    Erro "MARKET_DATA_UNAVAILABLE_FOR_SECTOR_X" exibido para usuário.
  fix: |
    Substituir por:
    "Não temos dados suficientes para simular este setor.
     Estamos coletando dados — você pode pedir notificação quando estiver pronto."
    Adicionar botão [Notificar quando disponível]
  effort: "2h"
```

### 9.2 SaaS billing

```yaml
HE-003:
  heuristic: 5 (Prevenção)
  severity: 4
  location: "/configurações/cancelar-assinatura"
  problem: |
    Botão "Cancelar assinatura" sem confirmação. Click acidental
    cancela imediatamente. Sem undo.
  fix: |
    Modal de confirmação:
    "Tem certeza que quer cancelar?
     Você perderá acesso em [data fim do período pago].
     Você pode reativar a qualquer momento antes disso."
     [Cancelar mesmo assim] [Manter assinatura]
  effort: "1h"
```

---

## 10. Como rodar avaliação

### 10.1 Tempo necessário

| Escopo | Tempo |
|---|---|
| Quick eval (1 fluxo, top 3) | 30 min |
| Full eval (1 phase, todas 10 heurísticas) | 2-4h |
| Milestone audit (3-5 phases) | 1 dia |
| Comparative eval (vs concorrente) | 2 dias |

### 10.2 Como executar

**Solo:**
1. Abrir cada tela do escopo
2. Para cada tela, percorrer as 10 heurísticas
3. Anotar problemas em template (seção 6)
4. Atribuir severity
5. Compilar relatório

**Em par:**
1. 2 avaliadores avaliam separadamente (1-2h cada)
2. Sessão de consolidação (30min)
3. Resolver discordâncias por consenso
4. 1 relatório final

**Com Claude:**

```
"Faça heuristic evaluation da phase 4 (checkout) seguindo
.claude/skills/quality/heuristic-evaluation/SKILL.md.

Persona: Bruna (P-001).
Telas: /carrinho, /checkout, /pagamento, /confirmacao.

Para cada heurística (1-10):
1. Identifique problemas observáveis
2. Atribua severity (0-4)
3. Sugira fix concreto

Compile relatório em .planning/phases/04-checkout/04-HEURISTIC-EVAL.md.
Resuma severity 4 no topo (bloqueia release)."
```

---

## 11. Como integra com fluxo gsd

### 11.1 → `/gsd-verify-work`

Antes de marcar phase como done, rodar heuristic eval. Severity 4 bloqueia.

### 11.2 → `/gsd-audit-milestone`

Audit consolidado de todas as phases do milestone. Identifica padrões (ex: heurística 5 sistematicamente falha).

### 11.3 → TECH-DEBT.md

Severity 1-2 vão para tech debt com link para HE-XXX.

### 11.4 → ROADMAP

Padrões repetidos (ex: 5 phases falham em heurística 1) viram phase de "polish UX" no roadmap.

### 11.5 → Métricas

Reportar em milestone summary:

```markdown
## Heuristic Evaluation Summary — Milestone v1.0

| Phase | Sev 4 | Sev 3 | Sev 2 | Sev 1 |
|---|---|---|---|---|
| Phase 1 | 0 | 2 | 5 | 3 |
| Phase 2 | 1 | 3 | 4 | 2 |
| Phase 3 | 0 | 1 | 6 | 4 |
| Phase 4 | 2 | 5 | 3 | 2 |
| Phase 5 | 0 | 0 | 2 | 1 |

**Total Sev 4 antes de fix: 3** (todos resolvidos antes de release)
**Total Sev 3 antes de fix: 11** (8 resolvidos, 3 viraram tech debt com ADR)
```

---

## 12. Erros comuns

### Erro 1: Avaliar sem persona
Heurística 6 (memorização) aplica diferente para iniciante vs expert.

### Erro 2: Skip de severity 4
"Vamos lançar e arrumar depois" — nunca depois. Severity 4 = bloqueia release.

### Erro 3: Avaliação sem re-eval
Fixar problema não garante que está resolvido. Re-avaliar.

### Erro 4: Relatório de 100 páginas
Ninguém lê. Foco em top 10 com severity descendente.

### Erro 5: Avaliar apenas heurísticas
Ignorar acessibilidade. Use também `quality/accessibility-pro`.

---

## 13. Frameworks adjacentes

| Framework | Quando usar |
|---|---|
| **Nielsen 10 heuristics** | Esta skill — UX geral |
| **WCAG audit** | `quality/accessibility-pro` — a11y específico |
| **Cognitive walkthrough** | Audit baseado em task (não em heurística) |
| **GOMS analysis** | Otimização de cliques/tempo |
| **System Usability Scale (SUS)** | Quantitativo, com usuários reais |
| **HEART (Google)** | Métricas de UX (Happiness, Engagement, Adoption, Retention, Task success) |

---

## 14. Checklist de validação do audit

```
□ Escopo definido (telas, persona, heurísticas)?
□ Cada problema tem severity (0-4)?
□ Cada problema severity 3-4 tem fix suggestion?
□ Cada problema tem location (tela, elemento)?
□ Steps to reproduce documentados?
□ Effort estimado (h)?
□ Severity 4 → bloqueia release?
□ Severity 3 → fix em phase atual?
□ Severity 1-2 → entrou em TECH-DEBT?
□ Relatório salvo em .planning/phases/<N>/N-HEURISTIC-EVAL.md?
□ Re-eval planejada após fixes?
□ Patterns identificados (heurística que falha em N phases)?
```

---

## 15. Referências

- **Jakob Nielsen** — "10 Usability Heuristics for User Interface Design" (1994)
- **Don Norman** — "The Design of Everyday Things" (heurísticas alinhadas)
- **NN/g (Nielsen Norman Group)** — nngroup.com (case studies)
- **Steve Krug** — "Don't Make Me Think" (heurísticas em prática)

---

**Última atualização:** v0.7.0 (densificação)
**Densidade:** 15 seções, 10 heurísticas com checklists, 4 templates copy-paste, exemplos por heurística, severity scale Nielsen, anti-patterns com correção
