---
name: empathy-map
category: meta
description: Construir empathy map de 4 quadrantes (Diz, Pensa, Faz, Sente) para sintetizar pesquisa do usuário em insights acionáveis. Usar quando capturar entendimento do usuário rapidamente.
---

# Empathy Map — Mapa de Empatia

> Empathy map é "user persona em 30 minutos". Quando você precisa capturar entendimento sem fazer pesquisa formal pesada.

## Quando esta skill é obrigatória

- `/gsd-research-phase` em features com persona já definida mas sem dados profundos
- Após entrevistas qualitativas (3-5 sessões) para sintetizar
- `/gsd-discuss-phase` quando time precisa alinhar entendimento do usuário antes de planejar

## Estrutura: 4 quadrantes

```
┌─────────────────────┬─────────────────────┐
│      DIZ (Says)     │    PENSA (Thinks)   │
│                     │                     │
│ Citações literais   │ Crenças, dúvidas,   │
│ do usuário          │ medos não verbais   │
│                     │                     │
├─────────────────────┼─────────────────────┤
│      FAZ (Does)     │    SENTE (Feels)    │
│                     │                     │
│ Comportamento       │ Emoções dominantes  │
│ observável          │ por contexto        │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

## Processo (30-60 minutos)

### 1. Definir o sujeito

- **Persona específica** (não "usuários em geral")
- **Contexto específico** (ex: "Bruna no momento de tentar configurar PIX no app")

### 2. Preencher cada quadrante

**Diz** (10 min): citações literais que você ouviu
- "Não sei se isso está dando dinheiro"
- "Meu marido que cuida das contas"
- "Já tentei outros sistemas e tudo trava"

**Faz** (10 min): comportamento concreto, observável
- Anota vendas no caderno
- Pergunta para o filho como faz coisas no celular
- Abandona se demorar mais que 5 min

**Pensa** (10 min): inferir do contexto, da fala não-dita
- "Será que vou conseguir aprender?"
- "E se eu apertar o botão errado e perder tudo?"
- "Outras donas de loja saberiam fazer isso?"

**Sente** (10 min): emoção dominante por contexto
- Insegurança ao mexer com tecnologia
- Orgulho do próprio negócio
- Cansaço de ter sido enganada por software ruim

### 3. Síntese — 3 insights acionáveis

Para cada quadrante, extrair UM insight prioritário:

```
1. Bruna abandona se travar em 5 min → onboarding precisa funcionar offline-first
2. Bruna pergunta para o filho → produto precisa parecer "fácil de mostrar"
3. Bruna teme apertar botão errado → undo + confirmações + linguagem reversível
```

## Anti-patterns

❌ Inventar citações que ninguém disse
❌ "Diz" e "Pensa" idênticos — propósito é capturar gap entre fala e crença
❌ Empathy map sem persona definida ("usuário em geral")
❌ Pular síntese (3 insights acionáveis) — empathy map sem síntese é decoração

## Integração

- Antes: `meta/user-persona`
- Em paralelo: `meta/journey-map`
- Depois: input direto para `/gsd-discuss-phase` da próxima feature
