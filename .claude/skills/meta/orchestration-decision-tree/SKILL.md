---
name: orchestration-decision-tree
description: Árvore de decisão de roteamento para o gsd-orchestrator do {PROJETO}. Mapeia intenção do usuário para workflows GSD e skills obrigatórias.
type: meta
project: global-brasil-conecta
---

# Skill: Orchestration Decision Tree

> Routing brain do gsd-orchestrator. Leia este arquivo antes de qualquer roteamento.

---

## 1. Protocolo de leitura obrigatória

Antes de rotear QUALQUER tarefa, ler nesta ordem:
1. `CLAUDE.md` — contrato do projeto (stack, banco, regras, anti-patterns)
2. `.planning/STATE.md` — fase atual, progresso, bloqueios ativos
3. `git log --oneline -5` — estado recente do código

---

## 2. Matriz de roteamento por intenção

| Gatilho na mensagem do usuário | Workflow principal | Skills obrigatórias |
|---|---|---|
| "nova tela", "nova página", "nova feature com UI" | `/gsd-ui-phase N` → `/gsd-plan-phase N` → `/gsd-execute-phase N` | ui-ux-pro-max, design-tokens-system, ux-copywriting-ptbr |
| "implementar", "adicionar feature", "criar endpoint" | `/gsd-plan-phase N` → `/gsd-execute-phase N` | spartan-ai-toolkit + skills de domínio relevantes |
| "bug", "erro", "não funciona", "quebrando", "500", "crash" | `/gsd-debug` | systematic-debugging, spartan-ai-toolkit |
| "revisar", "code review", "PR", "antes de mergear" | `/gsd-code-review` | owasp-security, lgpd-compliance, systematic-debugging |
| "segurança", "vulnerabilidade", "LGPD", "PII", "compliance" | `/gsd-secure-phase` | owasp-security, lgpd-compliance, {gateway-pagamento}-escrow-br |
| "planejar", "criar plano", "fase", "roadmap" | `/gsd-plan-phase N` | spartan-ai-toolkit, pattern-mapper |
| "executar plano", "implementar plano pronto" | `/gsd-execute-phase N` | skills de domínio do PLAN.md |
| "documentação", "doc", "atualizar README" | `/gsd-doc-update` | ux-copywriting-ptbr |
| "auditoria UI", "UI review", "score de design" | `/gsd-ui-review` | ui-ux-pro-max, design-tokens-system |
| "saúde do projeto", "health check", "status geral" | `/gsd-health` | — |
| "retomar", "onde parei", "continuar" | `/gsd-resume-project` | — |
| "teste", "cobertura", "spec", "playwright" | `/gsd-add-tests` | webapp-testing, spartan-ai-toolkit |
| "migração", "alembic", "nova tabela", "schema" | Inline + `/gsd-plan-phase` | mysql-schema-design |
| "deploy", "docker", "produção", "nginx" | `/gsd-plan-phase` | docker-production-ready |
| "início de sessão", "novo dia", primeira mensagem vaga | Ler STATE.md → sugerir próximo passo | — |

---

## 3. Enriquecimento automático de skills por domínio

Quando a tarefa toca um desses domínios, injetar as skills correspondentes **sempre**:

| Domínio detectado | Skills a injetar |
|---|---|
| Qualquer CSS/SCSS novo | design-tokens-system |
| Componente mobile (`apps/mobile/`) | ionic-patterns |
| Componente admin (`apps/admin/`) | angular-material-patterns |
| Campo CPF/CNPJ/CEP/telefone/BRL | brazilian-forms |
| Texto visível ao usuário (labels, botões, erros) | ux-copywriting-ptbr |
| Upload de arquivo/foto | file-upload-ux |
| Tela que consome API (lista, detalhe) | empty-states-polish |
| Nova tabela ou coluna no banco | mysql-schema-design |
| Endpoint com dado pessoal (PII) | lgpd-compliance |
| Fluxo de pagamento (Pix, cartão, escrow) | {gateway-pagamento}-escrow-br, payment-checkout-ux |
| Chat / mensagens / proposta | chat-ux-patterns |
| Formulário multi-campo | form-ux-mastery |
| Fluxo de cadastro / onboarding | onboarding-patterns |
| Badge de verificação / escrow visualization | trust-safety-ux |
| Dashboard / KPIs / gráficos | saas-dashboard-patterns |
| Input avançado (color picker, date range) | ui-input-rich-patterns |
| Animação / transição / micro-interação | motion-design-patterns |
| Componente interativo (botão, modal, form) | accessibility-pro |
| Layout, grid, breakpoints | responsive-breakpoint-strategy |
| Gesto mobile (swipe, long press, haptic) | gesture-touch-patterns |
| Tela de pagamento / checkout | payment-checkout-ux |

---

## 4. Regras de escalação (quando pedir clarificação)

Pedir confirmação ANTES de agir quando:

1. **Tarefa destrutiva**: "deletar", "remover feature", "reverter", "reset" → confirmar escopo
2. **Toca múltiplas fases**: feature que envolve banco + API + mobile + admin → perguntar se é 1 plano ou N planos
3. **Estimativa > 2 horas de execução**: apresentar scope antes de spawnar agentes
4. **Conflito com STATE.md**: tarefa pedida é de Fase 2 mas estamos na Fase 1 → alertar e confirmar
5. **Tarefa vaga sem contexto**: "melhora a busca" → clarificar: qual tela? qual aspecto? qual problema?

---

## 5. {PROJETO} shortcuts — tarefas frequentes e seus fluxos

| Tarefa {PROJETO} | Fluxo exato |
|---|---|
| Nova tela mobile (cliente ou profissional) | `/gsd-ui-phase redesign` → `/gsd-plan-phase N` → `/gsd-execute-phase N` |
| Novo endpoint FastAPI | `/gsd-plan-phase N` (sem ui-phase) + skills: mysql-schema + lgpd |
| Fix de bug no chat/WebSocket | `/gsd-debug "descrição"` + skill: chat-ux-patterns |
| Integração {gateway-pagamento} (Pix/Cartão) | `/gsd-plan-phase N` + skill: {gateway-pagamento}-escrow-br + payment-checkout-ux |
| Token migration em SCSS | Inline (não precisa de fase) + skill: design-tokens-system |
| Nova migration Alembic | Inline + skill: mysql-schema-design |
| Code review antes de PR | `/gsd-code-review` + skills: owasp + lgpd + ionic/angular |
| Auditoria visual de tela | `/gsd-ui-review` |
| Verificar cobertura de testes | `/gsd-add-tests` ou `/gsd-nyquist-auditor` |

---

## 6. Regra de ouro do orquestrador

```
Nunca escrever código → sempre rotear para o workflow correto
Nunca spawnar sem ler STATE.md primeiro
Nunca ignorar o domínio da tarefa (injetar skills de domínio)
Sempre confirmar ações destrutivas ou caras
```
