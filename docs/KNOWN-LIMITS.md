# KNOWN-LIMITS.md

> Limitações conscientes do framework. Não são bugs — são decisões de escopo ou trade-offs assumidos. Documentadas para evitar surpresas.

---

## 1. Plan-checker valida citação de skills, não aplicação

O `gsd-plan-checker` verifica que skills obrigatórias estão **citadas** na seção `## Skills Consultadas` do PLAN.md. Não verifica se elas foram **aplicadas** no código.

**Mitigação (ampliada na v0.9.6):** o hook `gsd-skill-application-check.js` (PostToolUse) compara skills citadas vs fingerprints (imports/keywords) no código e no SUMMARY.md quando o SUMMARY é escrito. Cobertura: **73 de 73 skills** têm fingerprint (era 12/66 — a v0.9.6 também corrigiu o bug de keying que fazia `standalone/owasp-security` nunca casar, e a extração que ignorava skills sem categoria).

**Honestidade sobre o que a heurística prova:** keyword presente NÃO prova aplicação profunda — prova que o domínio da skill foi tocado. O check otimiza para o caso inverso, que é o que importa: **skill citada e completamente ignorada** (zero sinais no código e no SUMMARY) é detectada com alta confiança. Para profundidade real de aplicação, a barreira é o Gate 8 (`gsd-tools verify quality-bar`, enforcement por script desde a v0.9.6) + a Regra 5 do CLAUDE.md nos primeiros sprints.

**Quando o gap residual aparece:** skill aplicada superficialmente (uma keyword, zero substância) passa no fingerprint. Mitigação: Gate 8 Bloco correspondente + code review.

---

## 2. Multi-milestone exige `MILESTONES.md` atualizado

`getMilestoneInfo()` em `gsd-tools.cjs` prioriza `MILESTONES.md` "in_progress" para detectar milestone atual. Se você muda de milestone manualmente sem atualizar `MILESTONES.md`, o framework pode usar info desatualizada.

**Mitigação:** comandos `/gsd:complete-milestone` e `/gsd:bootstrap` atualizam `MILESTONES.md` automaticamente. Hook `gsd-state-integrity-check.js` detecta divergência na entrada da sessão.

**Quando o gap aparece:** edição manual de `STATE.md` sem atualizar `MILESTONES.md`.

---

## 3. Auto-promoção de UAT pode gerar items com placeholders

Hook `gsd-uat-promoter.js` auto-promove items `human_needed` de `VERIFICATION.md` para `HUMAN-UAT-BACKLOG.md`. Items extraídos vêm com placeholders: "Tipo: [auto-extraído — refinar]", "Pré-condição: [preencher]".

**Esperado:** operator refina antes de fechar o milestone. Sem refinamento, o backlog vira ruído visual.

**Quando o gap aparece:** se você executa `/gsd:complete-milestone` sem revisar `HUMAN-UAT-BACKLOG.md`, items ficam com placeholders.

---

## 4. Sem field data acumulado v0.8.x antes de v0.9

v0.8.0 e v0.8.1 não tiveram um ciclo de campo completo antes de v0.9. Mudanças foram calibradas com diagnóstico do Rota Certa (v0.7.x) e pesquisa de skills externas, mas não com telemetria de uso do v0.8.

**Esperado:** v0.9 acumula primeiro ciclo de campo. v0.10 será calibrado com esses dados.

---

## 5. PDF muito grande pode estourar contexto

`gsd-project-ingestor` lê PDFs nativamente, mas PDFs >200 páginas podem estourar contexto.

**Mitigação:** o agent detecta tamanho e sugere `bin/convert-docs.sh` para fragmentar.

---

## 6. OCR de wireframes não é perfeito

`gsd-project-ingestor` lê imagens (PNG, JPG) e descreve estrutura, mas se o wireframe tem labels muito pequenas ou texto manuscrito, pode perder informação.

**Mitigação:** prefira wireframes com texto legível, ou complemente com `.md` descrevendo a tela.

---

## 7. Skills citadas em excesso pelo orquestrador

Em projetos com UI complexa, plan-checker pode aceitar PLAN.md citando 8-12 skills relacionadas (`ui-ux-pro-max` + `meta/composition-patterns` + `quality/web-design-audit` + `quality/typography-scale` + ...). Não há limite enforçado.

**Esperado:** orquestrador deve dispensar skills redundantes na seção `## Skills Dispensadas (com justificativa)`. Plan-checker não força isso.

**Solução futura:** adicionar dimension 8 no plan-checker que penaliza redundância sem justificativa.

---

## 8. Telemetria local-only

`bin/export-telemetry.sh` gera JSON anonimizado para análise manual. Não há servidor central de telemetria. Para calibração entre versões, usuário envia manualmente.

**Esperado:** próximas versões podem adicionar opt-in para telemetria automática.

---

## 9. Recovery de hooks ausente

Se um hook tem bug e quebra (ex: JSON malformado em `settings.json`), Claude Code pode parar de processar outros hooks na mesma fase do ciclo (PostToolUse, etc.).

**Mitigação:** todos os hooks do framework têm `try/catch` no main + `process.exit(0)` no catch. Falha silenciosa preferida a falha ruidosa.

**Sintoma de bug:** hook não dispara, mas Claude Code não loga erro visível. Use `GSD_<HOOK>_DEBUG=1` para ativar logs.

---

## 10. Pasta `projeto/` é input one-way (por design)

Pasta `projeto/` é input do usuário. Framework lê mas **nunca modifica** arquivos lá. Isso significa:

- Se você refatora REQUIREMENTS em `.planning/`, `projeto/regras-negocio/` não muda automaticamente
- Re-rodar `/gsd:ingest` pode regenerar REQ-001 a partir do mesmo arquivo, mesmo após você ter editado o REQ-001 em `.planning/`

**Mitigação:** `--force` é obrigatório para sobrescrever `.planning/`. Sem `--force`, agent faz merge inteligente. Hook detecta colisões.

**Solução futura:** sincronização bidirecional opt-in (perigosa, requer design cuidadoso).

---

## 11. ui-ux-pro-max não tem fingerprint genérico

Hook `gsd-skill-application-check.js` tem fingerprints para skills específicas (sentry_sdk, axe-core, etc.). Para `ui-ux-pro-max`, que é amplo (tokens, paleta, estilo), o fingerprint é mais difícil de definir.

**Mitigação:** verificação é feita por keyword (`design system`, `tokens.json`, `--color-`). Pode dar falso negativo se projeto usa convenção diferente.

---

## 12. Single-orchestrator em paralelismo

Squad de agents paralelos (research, audit, integration) usa `Task` tool, mas todos retornam ao orquestrador principal para síntese. Não há "agente líder de squad" — orquestração é centralizada em uma instância de Claude.

**Esperado:** essa é a arquitetura do Claude Code. Não é uma limitação a corrigir, é decisão de design.

---

## Como reportar uma limitação não documentada

Se você encontrou algo que não está aqui:

1. Verifique se é **limitação** (decisão consciente) ou **bug** (defeito não intencional)
2. Se bug: abra issue em `.planning/SUGGESTIONS.md` com tag `[bug]`
3. Se limitação não documentada: PR adicionando aqui é bem-vindo

---

## Princípio editorial deste documento

- **Honestidade explícita > otimismo escondido**
- **Cada limit tem mitigação** (mesmo que parcial)
- **"Solução futura"** quando há plano realista; sem prometer datas
- **Não há "errata"** — o que escrevemos no framework é o que é. Limitações são parte do design, não erros de documentação.
