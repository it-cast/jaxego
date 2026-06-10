---
name: gsd:go
description: |
  Comando único de entrada do framework. Detecta o estado do projeto e roteia
  automaticamente: projeto novo → ingest → bootstrap → autopilot; projeto em
  andamento → resume do ponto exato. O usuário não precisa saber qual dos 92
  commands usar — /gsd:go sabe.
---

# /gsd:go

**O caminho de ouro em um comando.** Para quem quer: jogar a documentação em `projeto/` e receber o sistema pronto, pausando só onde decisão humana é obrigatória.

## Uso

```
/gsd:go                  # detecta estado e faz a coisa certa
/gsd:go --dry-run        # mostra o que faria, não executa
/gsd:go --until=plan     # para após o planejamento (revisar antes de codar)
/gsd:go --status         # só diagnóstico: onde o projeto está + próximo passo
```

## Árvore de decisão (o que o comando faz por você)

```
/gsd:go
  │
  ├─ .planning/ NÃO existe?
  │    ├─ projeto/ tem conteúdo?
  │    │    └─ SIM → /gsd:ingest → mostrar DISCOVERY-REPORT
  │    │             → confirmar com humano → /gsd:bootstrap
  │    │             → mostrar ROADMAP → confirmar → /gsd:autopilot M1
  │    └─ projeto/ vazia?
  │         └─ Explicar projeto/README.md, oferecer discovery
  │            interativo (GUIA-DESCOBERTA) como alternativa
  │
  ├─ .planning/ existe, STATE.md aponta phase em andamento?
  │    └─ /gsd:resume-work (continua do ponto exato — task, wave, gate)
  │
  ├─ .planning/ existe, milestone atual completo?
  │    └─ Oferecer: /gsd:milestone-summary → próximo milestone via autopilot
  │
  └─ Estado inconsistente (STATE diverge de artefatos)?
       └─ /gsd:health → reportar divergências → propor reconcile
```

## Pausas garantidas (mesmo no caminho automático)

1. Após DISCOVERY-REPORT (você valida o que o Claude entendeu dos seus docs)
2. Após ROADMAP gerado (primeiro ponto de falha de alinhamento — sempre revisar)
3. Gate block, verification failure, decisão de ADR
4. Fim de cada milestone

Tudo entre essas pausas roda sozinho, com todos os 8 gates ativos.

## O que /gsd:go NÃO é

- Não é `/gsd:autonomous` (v0.1, bypassa gates). /gsd:go respeita 100% do enforcement.
- Não substitui os outros 92 commands para quem quer controle fino — é a porta de entrada para quem não quer decorá-los.

---

## Invocação

Você é o roteador. Execute a árvore de decisão acima literalmente:

1. **Diagnóstico** (sempre, mesmo sem --status):
```bash
node .claude/get-shit-done/bin/gsd-tools.cjs state get 2>/dev/null
ls .planning/ 2>/dev/null
find projeto/ -type f ! -name "README.md" 2>/dev/null | head -5
```

2. **Anuncie a rota escolhida em 2 linhas** antes de executar ("Detectei: projeto novo com 14 arquivos em projeto/. Rota: ingest → bootstrap → autopilot M1, com 2 pausas de revisão.").

3. **Execute via Skill()** os workflows na ordem da rota. `--dry-run` imprime a rota e para. `--until=<step>` para após o step nomeado (ingest|bootstrap|plan).

4. **Em qualquer erro**: parar, mostrar o erro real, indicar o comando granular para o humano intervir (e qual arquivo olhar). Nunca improvisar rota alternativa silenciosamente.
