---
name: project-kickoff-interview
description: Roteiro de entrevista para início de NOVO projeto (não aplicável ao {PROJETO} que já existe). Extrai contexto para configurar GSD e CLAUDE.md inicial.
type: meta
---

# Skill: Project Kickoff Interview

> Use APENAS quando CLAUDE.md não existe e git history está vazio. Para projetos existentes, ir direto ao orchestration-decision-tree.

---

## Quando usar

- Primeiro uso em projeto novo (sem CLAUDE.md)
- `git log` retorna vazio ou 1 commit inicial
- Usuário diz "quero começar um projeto do zero"

## Quando NÃO usar

- Projeto {PROJETO} (já tem CLAUDE.md e STATE.md)
- Qualquer projeto com CLAUDE.md existente → ir para routing direto

---

## 5 Perguntas do Kickoff

### Q1 — Qual é o produto?
"Em uma frase: o que o usuário faz no seu app e qual problema resolve?"
→ Captura: nome do produto, propósito, público-alvo

### Q2 — Quem são os usuários?
"Tem mais de um tipo de usuário? (ex: cliente e prestador, admin e usuário)"
→ Captura: múltiplos roles → implica separação de auth, áreas distintas

### Q3 — Qual é a stack?
"Mobile, web admin, ou ambos? Tem preferência de tecnologia?"
→ Mapear para: Ionic/Angular (mobile) + Angular/Material (admin) + FastAPI (API)
→ Se não tem preferência → recomendar stack {PROJETO} (ver stack-advisor)

### Q4 — Qual é o deployment target?
"VPS próprio, cloud (AWS/GCP/Azure), ou ainda não decidiu?"
→ Captura: influencia Docker strategy, CI/CD config

### Q5 — Tem pagamentos ou dados sensíveis?
"O app lida com dinheiro, CPF, cartão, ou saúde?"
→ Sim → injetar skills: {gateway-pagamento}-escrow-br, lgpd-compliance, owasp-security desde o início

---

## Mapeamento de respostas para config.json

```json
{
  "model_profile": "balanced",
  "workflow": {
    "ui_phase": true,      // sempre true se tem frontend
    "tdd_mode": false,     // ativar se equipe tem disciplina de testes
    "research": false      // ativar se domínio complexo (fintech, saúde)
  }
}
```

---

## Próximo passo após kickoff

1. Criar `CLAUDE.md` com stack, banco, convenções
2. Rodar `/gsd-new-project` para criar roadmap
3. O restante segue o orchestration-decision-tree normalmente
