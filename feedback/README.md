# Feedback para o GSD Framework — origem: Jaxegô v1.0

> Pacote de feedback de campo gerado a partir de um caso real: o projeto **Jaxegô**
> rodou 14 phases (MS-01 a MS-06) majoritariamente em **autopilot**, fechou todas com
> gates verdes e `STATE.md` declarando "100% dev/test" — mas o produto **não navega de
> ponta a ponta**, superfícies inteiras eram stubs, e ao integrar/deployar surgiu uma
> cascata de 9 falhas de CI/deploy. É exatamente o field data que o framework não tinha
> (FRAMEWORK-STATUS.md, limitação #1: "zero field data").

## Mapa do pacote (leia nesta ordem)

| # | Arquivo | Para quê |
|--:|---|---|
| 1 | `README.md` | Este índice + TL;DR da falha-raiz. |
| 2 | `POSTMORTEM-jaxego-v1.md` | As 8 falhas de **produto** (F1-F8), com evidência e classe [DOC]/[COD]/[PROC]. |
| 3 | `FIELD-REPORT-02-ci-deploy-merge.md` | As 7 falhas de **pipeline/integração** (A1-A7): CI real, deploy, merge multi-dev. |
| 4 | `GAPS-MATRIX.md` | **Matriz-mestre** unificada (F1-F8 + A1-A7) priorizada por impacto/custo → mecanismo → gate. Comece por aqui se quiser o panorama. |
| 5 | `GSD-IMPROVEMENTS.md` | Cada falha de produto traduzida em **mudança de mecanismo** (M1-M9: gates, reconcile, autopilot). |
| 6 | `METRICS-jaxego-v1.md` | **Números reais** do repo (281 commits, fix-rate, CI round-trips) + as métricas que o GSD NÃO tem e deveria. |
| 7 | `RETRO-reconstrucao-integracao.md` | Retrospectiva preenchida do trabalho de **salvamento** (reconstrução + merge + CI verde). |
| 8 | `TELEMETRY-INTERPRETACAO-HUMANA.md` | Os campos `<FILL>` da telemetria do framework, **preenchidos** com veredito de campo. |
| 9 | `CHECKLIST-PROXIMO-PROJETO.md` | Acionável: o que incluir antes/durante/no fechamento para não repetir. |

## Evidência-base

A auditoria arquivo-a-arquivo que sustenta o postmortem está em
`docs/AUDITORIA-FRONTEND-v1.md` (mesmo repo). Números de linha citados referenciam o
código real. Métricas são reproduzíveis com `git log`/`find` (ver `METRICS-jaxego-v1.md`).

## TL;DR — a falha-raiz em uma frase

> O GSD valida **artefatos** (arquivo existe, teste passa, skill citada, plano
> reconcilia com código presente) mas **não valida produto** (a tela é alcançável? o
> endpoint tem UI? o fluxo fecha?) **nem paridade de pipeline** (o CI real do repo passa?).
> Largura passou em todos os gates; profundidade de integração nunca foi exigida.

As 15 falhas (8 de produto + 7 de pipeline) **não são bugs isolados** — são consequências
previsíveis desse buraco. As **duas correções de maior ROI**:

1. **GSD conhece e roda o CI real do projeto** na definition-of-done (B1/B2). → frente de pipeline.
2. **Gate de alcançabilidade + checkpoint UAT humano por milestone** (M1/M8). → frente de produto.

## O que o framework JÁ faz bem (não regredir)

Research que lê o código existente (pegou EXIF GPS), verificação ao vivo (3 bugs de
migration), TECH-DEBT com urgency_class, rastro de DECISIONS. Detalhe em `GAPS-MATRIX.md §E`.
As correções devem **somar** à disciplina de planejamento, não substituí-la.
