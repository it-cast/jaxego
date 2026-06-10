# HUMAN-UAT-BACKLOG — itens pendentes de validação humana

> Backlog **consolidado** de tudo que precisa de teste manual antes do release.
> Atualizado quando uma phase fecha com `human_needed` items.
>
> **Não substitui** os arquivos `*-UAT.md` ou `*-VERIFICATION.md` por phase.
> Ele agrega os itens dispersos para que o owner saiba, em UM lugar:
> "o que ainda preciso testar manualmente antes de fechar este milestone?"
>
> Diagnóstico v0.7.x identificou que itens UAT ficavam espalhados em 3+ arquivos
> sem visão consolidada. Este arquivo resolve isso.

---

## Status counters

- 📋 Pendentes: 0
- ✅ Validados: 0
- ❌ Falharam: 0
- ⏸️ Bloqueados: 0

---

## Como usar

1. **Quando uma phase fecha com `human_needed` items**, o autopilot promove os itens
   para este arquivo automaticamente (a partir de `phases/NN-xxx/NN-VERIFICATION.md`
   ou `NN-HUMAN-UAT.md`).
2. **Antes de fechar um milestone**, o operator revisa este arquivo, executa cada item,
   e marca status.
3. **Itens que falham** devem virar gap-closure plan na phase em que estão (ou nova phase
   de hardening, se for cross-cutting).

---

## Itens pendentes

> Formato:
>
> ```
> ### UAT-{milestone}-{phase}-{nn} — Título curto
>
> - **Origem:** Phase NN, file `phases/NN-xxx/NN-VERIFICATION.md`
> - **Tipo:** smoke | integration | visual | device | regression
> - **Pré-condição:** o que precisa estar pronto antes (staging URL, seed, device, etc.)
> - **Passos:**
>   1. ...
>   2. ...
> - **Esperado:** ...
> - **Status:** 📋 pendente | ✅ validado | ❌ falhou | ⏸️ bloqueado
> - **Notas:** (preencher após execução)
> ```

(vazio — populado quando phases fecham com human_needed)

---

## Itens validados

(vazio — itens completos movem-se aqui após execução com sucesso)

---

## Itens que falharam

(vazio — itens que falharam viram gap-closure ou ADR)

---

## Itens bloqueados

(vazio — itens que não podem ser executados ainda; documentar bloqueio)

---

## Histórico de releases

> Quando um milestone é fechado, todos os itens validados deste arquivo são arquivados
> aqui com data e referência ao tag.

(vazio)
