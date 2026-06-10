---
name: gsd:ingest
description: |
  Lê tudo em projeto/ (qualquer formato) e gera documentação completa
  do projeto em .planning/, docs/ e design-system/. Substitui o bootstrap manual.
---

# /gsd:ingest

Acionar o agent **gsd-project-ingestor** para ler `projeto/` e popular toda a documentação do projeto.

## Uso

```
/gsd:ingest                       # leitura completa, gera tudo
/gsd:ingest --dry-run             # mostra o que vai gerar, não escreve
/gsd:ingest --only=requirements   # só regenera REQUIREMENTS.md
/gsd:ingest --force               # sobrescreve .planning/ existente
/gsd:ingest --from=meu-input/     # lê de pasta alternativa
```

## O que faz

1. Inventaria `projeto/` (recursivamente, todos os formatos)
2. Lê e categoriza arquivos (regras de negócio, wireframes, identidade visual, stacks, docs externos, referências, ADRs)
3. Detecta conflitos, gaps, decisões implícitas
4. Faz **discovery interativo** se há muitas Open Questions críticas
5. Gera:
   - `.planning/PROJECT.md, REQUIREMENTS.md, MILESTONES.md, ROADMAP.md, STATE.md, DECISIONS.md, TECH-DEBT.md, SUGGESTIONS.md`
   - `docs/` (personas, glossário, identidade visual, integrações, regras de negócio)
   - `design-system/MASTER.md` (se há material visual)
6. Gera **DISCOVERY-REPORT.md** na raiz mostrando o que foi extraído, o que foi assumido, o que ainda precisa decisão humana

## Pré-requisitos

- Pasta `projeto/` existe (com subpastas opcionais)
- Pelo menos algum conteúdo em `projeto/` (qualquer subpasta)

## Idempotência

Pode ser rodado múltiplas vezes. Adicionou mais arquivos em `projeto/`? Rode de novo — vai detectar o que é novo e atualizar `.planning/` em vez de sobrescrever.

## Próximo passo recomendado depois

```
/gsd:bootstrap   # se você quer revisar a planificação antes de começar
/gsd:autopilot   # se você confia no resultado e quer executar
```

---

## Invocação

Você é o orquestrador. Para esta tarefa:

1. **Verifique** se `projeto/` existe e tem conteúdo. Se não, peça ao usuário para criar a pasta e ler `projeto/README.md` para entender o que jogar lá.

2. **Acione** o agent `gsd-project-ingestor` via Task tool, passando os argumentos do comando (`--dry-run`, `--only`, `--force`, `--from`) como contexto.

3. **Mostre** o `DISCOVERY-REPORT.md` gerado para o usuário e destaque as Open Questions críticas.

4. **NÃO** escreva nada em `.planning/` diretamente — quem escreve é o agent.

5. **Se** Open Questions críticas foram detectadas, ajude o usuário a respondê-las antes de seguir para `/gsd:bootstrap`.
