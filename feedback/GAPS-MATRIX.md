# Matriz-mestre — tudo que o GSD não fez (e o mecanismo que fecha)

> Consolida `POSTMORTEM-jaxego-v1.md` (F1-F8) + `FIELD-REPORT-02` (A1-A7) numa
> matriz única, priorizada por (impacto × frequência) ÷ esforço. Cada linha:
> o que faltou · classe · mecanismo proposto · esforço · qual gate passaria a cobrir.
>
> Classe: **[DOC]** planejamento/doc · **[COD]** código · **[PROC]** processo do framework.

---

## A. O buraco-raiz (1 frase)

> **O GSD valida artefatos (existe? testa? cita skill? reconcilia com código presente?)
> e não valida produto (a tela é alcançável? o endpoint tem UI? o fluxo fecha? o CI real
> passa?).** Tudo abaixo é consequência disso, em duas frentes: **integração de produto**
> (postmortem) e **integração de pipeline** (field report 02).

---

## B. Matriz priorizada

| # | O que o GSD NÃO fez | Classe | Evidência | Mecanismo proposto | Esforço | Vira gate |
|--:|---|:--:|---|---|:--:|:--:|
| 1 | Rodar o **CI real do projeto** antes do "pronto" | PROC | A1/A2/A3 (9 round-trips) | **B1** detectar jobs em `.github/workflows` + **B2** `gsd verify pre-push` que roda o equivalente local e bloqueia | M | **Gate 7+** |
| 2 | Exigir **alcançabilidade** (endpoint↔UI↔rota) | PROC | F1, F3 | **M1** `gsd-reachability-checker` → `REACHABILITY.md`; endpoint sem UI = FLAG | M | **Gate 9** |
| 3 | Distinguir **stub de tela pronta** | PROC/COD | F2, F4 | **M2** reconcile marca página só-empty-state como `STUB-GAP`; define "tela pronta" | S | Gate 6 |
| 4 | Rastrear **fiação diferida** ("T-06","Phase 9") | PROC | F5 | **M3** Regra 13: forward-ref vira task ou TD; grep no execute-phase | S | execute |
| 5 | **Promover UAT** "pendente ao vivo" → backlog | PROC | F6 | **M4** autopilot BLOCK se `human_needed` não espelhado no UAT-BACKLOG | S | close |
| 6 | Garantir **deploy só após CI verde** | DOC/PROC | A4 | **B3a** checker lê workflows, falha se deploy dispara em `push` paralelo | S | release |
| 7 | **Robustez de config/env** (aspas, vazio) | DOC | A5 | **B3b** pré-flight de env no deploy + normalização no app | S | release |
| 8 | Forçar `integration_check` em phases cross-surface | DOC | F7 | **M5** derivação automática: toca rota/auth/2 superfícies → `true`, sem ADR não baixa | S | Gate 5 |
| 9 | Detectar **drift spec↔código** | PROC | A2 | **B4** ao mudar assinatura/URL, sinaliza specs que referenciam | M | reconcile |
| 10 | Materializar **ADRs referenciados** como arquivo | DOC | F8 | **M7** checker: `ADR-NNN` citado deve existir em `docs/adrs/`; ingest gera stubs | S | health |
| 11 | Orientar **concorrência multi-dev** (branch/PR) | DOC | A6 | **B5** guia + `gsd:pr-branch` como padrão; avisa "ahead N" grande | S | guia |
| 12 | **Checkpoint UAT humano por milestone** | PROC | raiz | **M8** autopilot para no fim de cada milestone p/ UAT do produto integrado | M | autopilot |
| 13 | **Walking skeleton** antes de profundidade | DOC | raiz | **M9** 1ª phase com auth entrega login→cada superfície→tela base real | S | slicing |

Esforço: S = pequeno (grep/regra), M = médio (agente/checker novo).

---

## C. Ordem de implementação recomendada (impacto/custo)

1. **#1 (B1/B2 — CI real local)** — sozinho mata A1/A2/A3, as falhas mais frequentes. Maior ROI.
2. **#3 + #4 + #5 (stub, fiação, UAT)** — todos esforço S, fecham metade do postmortem.
3. **#6 + #7 (release-safety)** — esforço S, evita deploy quebrado ao vivo.
4. **#2 (alcançabilidade)** — esforço M, mas é o gate que define "produto usável".
5. **#8 + #10 + #11 (planejamento)** — higiene de doc/processo.
6. **#12 + #13 (autopilot/slicing)** — mudança estrutural; depende dos checkers acima existirem.

---

## D. As duas mudanças que sozinhas resolvem ~80%

1. **GSD conhece e roda o CI real do projeto** (#1) → mata a frente de pipeline.
2. **Gate de alcançabilidade + checkpoint UAT por milestone** (#2 + #12) → mata a frente de produto.

O resto são camadas de maturidade sobre essas duas fundações.

---

## E. O que o framework JÁ fazia bem (para não jogar fora)

Honestidade dos dois lados — não regredir nestes pontos ao corrigir:

- **Research que lê o código existente** pegou o EXIF GPS (comprovação preserva vs KYC strip) — evitou bug sério (retro Phase 9).
- **Verificação ao vivo** pegou 3 bugs de migration que mock/SQLite nunca pegariam (revision id >32 chars, FK downgrade).
- **TECH-DEBT com urgency_class** e **DECISIONS.md** mantiveram rastro de decisão honesto.
- **Gate 3 (skills citadas)** garantiu cobertura de consideração — o problema é aplicação, não citação.
- **Reconcile** pega divergência de existência (só não pega alcançabilidade).

> Lição: o GSD é forte em **disciplina de planejamento e rastro**; fraco em **validação de
> produto integrado e paridade com o pipeline real**. As correções devem somar à primeira,
> não substituí-la.
