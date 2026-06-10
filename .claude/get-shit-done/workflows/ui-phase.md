<purpose>
Gera o design contract (UI-SPEC.md) de uma fase ANTES do plan-phase.
É o Gate 2 do framework — sem UI-SPEC aprovado, plan-phase recusa rodar.
v3: flag --mobile ativa seções exclusivas de mobile (safe area, keyboard, haptic, offline, first-load).
</purpose>

<required_reading>
@$CLAUDE_PROJECT_DIR/CLAUDE.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/references/gates-v3.md
@$CLAUDE_PROJECT_DIR/.claude/get-shit-done/templates/UI-SPEC.md
@$CLAUDE_PROJECT_DIR/docs/identidade-visual/design-system.md
@$CLAUDE_PROJECT_DIR/docs/identidade-visual/brand.md
</required_reading>

<trigger>
/gsd-ui-phase <N>                # UI web
/gsd-ui-phase <N> --mobile       # mobile-only OU web+mobile (se ambos, ambas as seções aparecem)
/gsd-ui-phase <N> --revision     # re-roda após ui-checker BLOCK
</trigger>

<process>

## 1. Pré-condições

```bash
[ -f .planning/PROJECT.md ] || die "Bootstrap não executado"
[ -f .planning/phases/$(padded $PHASE)-*/CONTEXT.md ] || warn "CONTEXT.md ausente — ui-researcher vai assumir defaults"
```

## 2. Carregar fontes de design

Obrigatórias:
- `docs/identidade-visual/design-system.md`
- `docs/identidade-visual/brand.md`

Se ausentes, bloquear:
```
❌ docs/identidade-visual/design-system.md não existe.

Sem design system definido, cada UI-SPEC vai inventar tokens e causar inconsistência
entre fases. Preencha o design system antes de rodar ui-phase.

Template: .claude/get-shit-done/templates/design-system.md
```

Opcionais (ui-researcher aproveita se existirem):
- `docs/identidade-visual/tokens.json`
- UI-SPECs de fases anteriores (para herdar componentes)

## 2.5. Wireframe como fonte de verdade (v0.9.7 — obrigatório quando existe)

Antes de invocar o researcher, procurar wireframes da(s) tela(s) desta phase em
`projeto/wireframes/` (match por nome de tela, número de fluxo `NN-`, ou rota).

**Se existir wireframe HTML/JSX/TSX/Vue/Svelte para uma tela:**
```bash
node .claude/get-shit-done/bin/gsd-tools.cjs wireframe-contract projeto/wireframes/<arquivo>
```
O JSON resultante é o **contrato estrutural** da tela: regiões, headings,
elementos interativos (texto + destino), forms/inputs, estados e cores.

Regras inegociáveis:
1. O UI-SPEC declara `wireframe_source: <path>` por tela coberta, e embute o
   contrato (ou referencia o JSON salvo em `{phase}/wireframe-contracts/`).
2. **Todo item do contrato aparece no UI-SPEC** — ou na spec da tela, ou num
   bloco `deviations:` com razão explícita ("dropdown do wireframe vira
   radio por acessibilidade, ref. accessibility-pro §X"). Omissão silenciosa
   reprova na Dimension 7 do checker.
3. Cores literais do contrato são MAPEADAS para tokens existentes em
   `tokens.json` (Gate 2) — se uma cor do wireframe não tem token, a decisão
   (criar token vs ajustar wireframe) é declarada, não improvisada.
4. `nav_targets` do contrato viram rotas reais no spec — links do wireframe
   que não levam a lugar nenhum na aplicação são deviation declarada.

**Se o wireframe for imagem (.png/.jpg/.pdf):** não há contrato mecânico —
o researcher lê a imagem e o UI-SPEC declara `wireframe_source` + descreve
fidelidade visualmente. A Dimension 7 valida presença da declaração e do
bloco de deviations, sem checagem item-a-item.

**Se não houver wireframe para a tela:** declarar `wireframe_source: none`
no spec da tela. Dimension 7 vira N/A para ela.

## 3. Invocar `gsd-ui-researcher` com contexto

Contexto passado:
- CONTEXT.md da fase
- Design system + brand
- **Contratos de wireframe extraídos no passo 2.5 (quando existirem)**
- Bloco desta fase no ROADMAP
- Flag `--mobile` (se presente)
- Skills pré-carregadas: `ui-ux-pro-max`, `design-to-code`, `accessibility-pro`, `error-ux-patterns`, `ux-copywriting-{locale}`, `micro-animations-delight`
- Se `--mobile`: carregar também `ionic-patterns` (ou equivalente), `mobile/safe-areas`, `mobile/keyboard-avoidance`, `mobile/touch-gestures`, `mobile/offline-first`

Instrução ao researcher:
> Gere `UI-SPEC.md` seguindo o template em `.claude/get-shit-done/templates/UI-SPEC.md`.
> Todas as seções do template são obrigatórias exceto onde explicitamente marcadas "N/A se <condição>".
>
> **Se --mobile ativo:** a seção "Seções exclusivas MOBILE" é obrigatória com todos os subtópicos (safe area, keyboard, touch targets, gestures, offline, first-load).
>
> **Anti-patterns proibidos no UI-SPEC:**
> - Citar hex hardcoded em vez de token (`#3b82f6` → `var(--color-brand-500)`)
> - Declarar componente sem 5 estados mínimos (loading, empty, success, error, offline-se-mobile)
> - Copy com "Ops!", "Algo deu errado", ou jargão técnico
> - Motion > 500ms em ação crítica
> - Ignorar `prefers-reduced-motion`
> - Omitir seção mobile quando --mobile ativo

## 4. Invocar `gsd-ui-checker` — validação em 7 dimensões

Checker avalia o UI-SPEC em 7 dimensões, pontuando cada uma em 4 pontos (total 28):

1. **Tokens e consistência visual** — uso correto de tokens herdados, sem hex hardcoded
2. **Tipografia** — scale correta, pesos apropriados, hierarquia clara
3. **Copy** — em pt-BR (ou locale), sem anti-patterns, tom alinhado com brand.md
4. **Estados** — 5 mínimos por componente (6 se mobile: + offline)
5. **Interações e motion** — durações apropriadas, easing do sistema, prefers-reduced-motion respeitado
6. **Acessibilidade** — contraste, labels, focus, landmarks, aria-*

**Se --mobile, dimensão 7 adicional:**
7. **Mobile-exclusive** — safe area declarada, keyboard avoidance descrito, touch targets ≥ 44×44, gestures documentados, offline behavior por tela

Threshold: 20/24 (ou 23/28 se mobile) para PASS. Abaixo disso: BLOCK com relatório detalhado.

### Loop de revisão

Se ui-checker BLOCK:
- Ui-researcher recebe feedback granular por dimensão
- Re-gera seções que falharam (não o arquivo inteiro)
- Checker re-avalia
- Max 3 iterações. Se ainda BLOCK: escalar ao humano

## 5. Aprovação final

Após PASS:

```markdown
## Approval

- [x] ui-checker validou 6 dimensões ({24}/{threshold})
- [ ] Humano revisou (ou delegou)
- **Aprovado em:** {date} por {humano|ui-checker-delegated}
```

Se `config.json: ui_phase_auto_approve: false`, exibir resumo ao humano e aguardar confirmação explícita.

## 6. Atualizar STATE.md + EXECUTION-LOG.md

```markdown
## {date} — /gsd-ui-phase {N} {--mobile?}
- UI-SPEC.md aprovado (score: 28/28)
- Telas cobertas: {N}
- Componentes novos: {lista}
- Próximo: /gsd-plan-phase {N}
```

## 7. Mensagem final

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► UI-PHASE — Phase {N} {--mobile?}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UI-SPEC.md gerado em .planning/phases/{N}-{slug}/UI-SPEC.md

  • Telas cobertas: {N}
  • Componentes novos/iterados: {lista}
  • Design tokens: sem conflito com design-system.md
  • Copy: validado em locale {pt-BR}
  • Estados por tela: 5 (loading/empty/success/error/offline*)
  • Micro-interações: {N} animações documentadas
  • Acessibilidade: contraste validado, landmarks declarados

  {se --mobile:}
  • Mobile-exclusive:
    - Safe areas: env(safe-area-inset-*) declarado em {N} telas
    - Keyboard avoidance: em {N} formulários
    - Touch targets: ≥ 44×44 verificado
    - Gestures: {swipe, pull-to-refresh declarados}
    - Offline: comportamento por tela documentado
    - First-load: splash < 1s, skeleton em {N} telas

ui-checker score: {24/24 ou 27/28}

Gate 2 do framework: ✅ satisfeito.

Próximo passo:
  /gsd-plan-phase {N}
```

</process>

<heuristics>

## Quando --mobile deve ser ativado

- Path da fase toca `apps/mobile/`, `mobile/`, `ionic/`, `capacitor`, `native`
- ROADMAP declara `mobile: true` na fase
- CONTEXT.md menciona dispositivos móveis como target primário

Se dúvida: humano decide no /gsd-discuss-phase.

## Herança de UI-SPECs anteriores

Fase N pode herdar UI-SPECs de fases N-1, N-2, etc. Ui-researcher:
1. Lista UI-SPECs de fases já fechadas
2. Identifica componentes/padrões reutilizáveis
3. Cita herança explicitamente no novo UI-SPEC:
   ```
   ## Herdado
   - Componente `{prefix}-{recurso}-card` — UI-SPEC Phase {N-anterior}
   - Estados de loading — mesmos de Phase 03
   ```

Isso evita inconsistências entre fases.

## Quando UI-SPEC pode ser "simples"

Nem toda fase com UI precisa de UI-SPEC de 500 linhas. Casos legítimos de UI-SPEC curto:
- Fase de bugfix visual (ajuste de spacing, fix de contraste)
- Fase de adição pontual de componente já documentado
- Fase de refactor interno com zero mudança visual

Nestes casos, UI-SPEC pode ter apenas:
- Seção "Fontes consultadas"
- Seção "Componentes/telas tocadas" (com link pro UI-SPEC anterior)
- Seção "Mudança específica" (diff mínimo)

Ui-checker adapta scoring para não exigir 24/24 em UI-SPEC simplificado — exige 12/12 das dimensões que se aplicam.

</heuristics>

<failure_modes>
- **design-system.md muito incompleto** — ui-researcher produz UI-SPEC com muitos "TBD". Fix: discuss-phase N precede ui-phase e humano preenche gaps de design system se necessário.
- **Copy exige conhecimento de negócio que ui-researcher não tem** — fix: CONTEXT.md captura no discuss-phase frases-chave, termos canônicos, pronomes.
- **Mobile check falha porque projeto não é mobile-only** — fix: --mobile só adiciona seções, não substitui as web. Ambas coexistem se o produto é cross-platform.
</failure_modes>
