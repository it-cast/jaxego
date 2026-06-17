# Feedback para o GSD Framework — origem: Jaxegô v1.0

> Pacote de feedback gerado em 2026-06-15 a partir de um caso real de campo:
> o projeto **Jaxegô** rodou 14 phases (MS-01 a MS-06) majoritariamente em
> **autopilot**, fechou todas com gates verdes e `STATE.md` declarando "100%
> dev/test" — mas o produto **não navega de ponta a ponta** e superfícies
> inteiras são stubs. Este é o tipo de field data que o framework não tinha
> (FRAMEWORK-STATUS.md, limitação #1: "zero field data").

## O que tem aqui

| Arquivo | Para quê |
|---|---|
| `POSTMORTEM-jaxego-v1.md` | O que falhou, com evidência. Separa **falha de documentação/planejamento** de **falha de codificação**. |
| `GSD-IMPROVEMENTS.md` | Tradução de cada falha em **mudança concreta de mecanismo** do GSD (gate, reconcile, autopilot, plan-checker). É o entregável acionável. |
| `FIELD-REPORT-02-ci-deploy-merge.md` | Field data da sessão de reconstrução+integração: CI real (ruff format/karma/zero-hex) e deploy (ordem, DATABASE_URL) que só falharam **pós-push**. Mudança-chave: **GSD precisa conhecer e rodar o CI real do projeto** na definition-of-done. |

## Evidência-base

A auditoria arquivo-a-arquivo que sustenta tudo isto está em
`docs/AUDITORIA-FRONTEND-v1.md` (mesmo repo). Os números de linha citados
aqui referenciam o código real do projeto.

## TL;DR — a falha-raiz em uma frase

> O GSD valida **artefatos** (arquivo existe, teste passa, skill citada, plano
> reconcilia com código presente) mas **não valida produto** (a tela é
> alcançável? o endpoint tem UI? o fluxo fecha?). Largura passou em todos os
> gates; profundidade de integração nunca foi exigida.

As 8 falhas detalhadas no postmortem **não são bugs isolados** — são
consequências previsíveis desse buraco. O `GSD-IMPROVEMENTS.md` fecha o buraco.
