---
name: systematic-debugging
description: >
  Debug estruturado e sistematico. Use quando encontrar qualquer bug,
  falha de teste, comportamento inesperado, erro de runtime, ou quando
  algo nao funciona e voce nao sabe por que. ANTES de propor fixes,
  use este metodo para diagnosticar a causa raiz.
---

# Systematic Debugging

## Regra #1: NUNCA adivinhe a causa. SEMPRE diagnostique primeiro.

## Processo de 5 passos

### PASSO 1 — Reproduzir
- Reproduza o bug de forma consistente
- Documente os passos exatos
- Quando comecou a falhar? Funciona em algum cenario?

### PASSO 2 — Isolar
- Qual CAMADA falha? Router? Service? Repository? DB?
- Use logs estrategicos (nao spam)
- O input esta correto? O output esta errado? Onde diverge?

### PASSO 3 — Hipotese
- Formule UMA hipotese especifica
- Crie teste que PROVA ou REFUTA
- Se refutada, volte ao passo 2

### PASSO 4 — Corrigir
- Corrija APENAS o que o diagnostico apontou
- Menor mudanca possivel
- Nao conserte coisas suspeitas sem evidencia

### PASSO 5 — Verificar
- Teste que reproduzia o bug agora passa?
- Testes existentes continuam passando?
- Documentar: causa, fix, como prevenir

## Padroes comuns

### WebSocket nao conecta
1. JWT no handshake correto? 2. CORS permite upgrade? 3. Redis rodando? 4. Rota ws:// correta?

### Pagamento nao confirma
1. Webhook URL acessivel? 2. idempotency_key unico? 3. Status {gateway-pagamento} sandbox? 4. Logs webhook?

### Query lenta
1. EXPLAIN ANALYZE 2. Indice existe? 3. N+1? 4. Paginacao?

### Angular nao renderiza
1. Standalone? 2. Imports corretos? 3. OnPush + signal? 4. Lazy loading?
