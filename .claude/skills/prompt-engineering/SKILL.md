---
name: prompt-engineering
description: >
  Tecnicas de prompt engineering e melhores praticas da Anthropic.
  Use quando precisar melhorar qualidade dos outputs, criar prompts
  mais eficientes, ou otimizar instrucoes para agentes e skills.
---

# Prompt Engineering

## Principios

### 1. Seja especifico
RUIM: "Crie um endpoint"
BOM: "Crie POST /api/v1/users com Pydantic schema, retornando 201"

### 2. Forneca contexto
RUIM: "Corrija o bug"
BOM: "GET /professionals retorna 500 quando service_id nao existe. Erro: NoResultFound"

### 3. Use exemplos (few-shot)
"Crie repository seguindo o padrao do user_repository.py"

### 4. Especifique formato
"Responda com: 1) Causa 2) Arquivo e linha 3) Fix 4) Teste"

### 5. Divida tarefas complexas
Nao: "Crie todo o modulo de pagamento"
Sim: Schema > Repository > Service > Router > Testes

### 6. Use constraints
"Siga CLAUDE.md. Sem any. Sem print. Use logging."

## Padroes para Claude Code

### Endpoint: "/endpoint POST /api/v1/proposals - profissional envia proposta"
### Componente: "/component perfil do profissional para app mobile Ionic"
### Debug: "Use systematic-debugging para diagnosticar test_create_user falhando 422"
