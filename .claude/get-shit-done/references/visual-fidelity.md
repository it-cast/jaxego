# Visual Fidelity — enforcement de identidade visual em sprints

> Referência normativa. Todo sprint com UI (`has_ui: true` no front-matter do `SPRINT.md`) passa por este checker antes de ser aprovado para execução.
> Objetivo: transformar "identidade visual" de documento pendurado em regra mecânica.

## Princípio central

Identidade visual é **contrato**, não sugestão. Um design system existe apenas quando:

1. Todo componente novo deriva de tokens **declarados** (cores, espaçamentos, tipografia, raios, sombras, motion)
2. Zero valor visual aparece hardcoded no código (cor hex, `px`, `rem` arbitrário)
3. Cada sprint com UI declara, **antes de codar**, quais tokens usará
4. Violação pega em PR via ESLint custom rule (`tooling/eslint/no-hardcoded-colors.js`) + revisão visual via Chromatic/Playwright screenshot

## Arquivos consultados

Este checker lê `docs/identidade-visual/`:

| Arquivo | Função |
|---------|--------|
| `docs/identidade-visual/tokens.json` | Fonte única de verdade. Style Dictionary format. |
| `docs/identidade-visual/design-system.md` | Documentação dos tokens e patterns do sistema. |
| `docs/identidade-visual/brand.md` | Voz, tom, vocabulário canônico (usado pelo `ux-copywriting-ptbr`). |

Se `tokens.json` estiver vazio ou não existir, **sprints com UI são bloqueados** até o usuário preencher. `bootstrap` avisa no setup.

## Estrutura esperada de `tokens.json`

Categorias mínimas para sprints com UI serem desbloqueados:

```json
{
  "color": {
    "brand": {
      "50": { "value": "#eff6ff" },
      "500": { "value": "#3b82f6" },
      "900": { "value": "#1e3a8a" }
    },
    "text": { "primary": { "value": "#111827" }, "secondary": { "value": "#6b7280" } },
    "surface": { "default": { "value": "#ffffff" }, "elevated": { "value": "#f9fafb" } },
    "border": { "default": { "value": "#e5e7eb" } },
    "semantic": {
      "success": { "value": "#10b981" },
      "warning": { "value": "#f59e0b" },
      "danger": { "value": "#ef4444" }
    }
  },
  "space": {
    "xs": { "value": "4px" },
    "sm": { "value": "8px" },
    "md": { "value": "16px" },
    "lg": { "value": "24px" },
    "xl": { "value": "32px" }
  },
  "radius": {
    "sm": { "value": "4px" },
    "md": { "value": "8px" },
    "lg": { "value": "16px" },
    "full": { "value": "9999px" }
  },
  "typography": {
    "family": { "base": { "value": "Inter, sans-serif" } },
    "size": {
      "xs": { "value": "12px" },
      "sm": { "value": "14px" },
      "md": { "value": "16px" },
      "lg": { "value": "20px" },
      "xl": { "value": "24px" }
    },
    "weight": { "regular": { "value": "400" }, "medium": { "value": "500" }, "semibold": { "value": "600" }, "bold": { "value": "700" } }
  },
  "motion": {
    "duration": { "fast": { "value": "100ms" }, "normal": { "value": "200ms" }, "slow": { "value": "400ms" } },
    "easing": {
      "out": { "value": "cubic-bezier(0, 0, 0.2, 1)" },
      "in": { "value": "cubic-bezier(0.4, 0, 1, 1)" },
      "inout": { "value": "cubic-bezier(0.4, 0, 0.2, 1)" }
    }
  }
}
```

Ausência de **qualquer** dessas categorias em projetos com UI = warning no bootstrap; ausência de `color` + `space` = block.

## Seção obrigatória em `SPRINT.md`

Todo `SPRINT.md` com `has_ui: true` inclui:

```markdown
## Visual Contract

Tokens usados nesta sprint (devem existir em `docs/identidade-visual/tokens.json`):

### Cores
- `color.brand.500` — botão primário, links ativos
- `color.text.primary` — títulos e corpo principal
- `color.surface.default` — fundo de card
- `color.semantic.danger` — mensagens de erro inline

### Espaçamentos
- `space.md` (16px) — padding interno de card
- `space.lg` (24px) — gap entre seções da página

### Tipografia
- `typography.size.lg` + `typography.weight.semibold` — título da tela
- `typography.size.md` + `typography.weight.regular` — corpo

### Motion (se aplicável)
- `motion.duration.normal` + `motion.easing.out` — transição de abertura do modal

### Componentes novos
- `app-status-badge` — usa cores semânticas + `radius.full`
- Adicionado ao `packages/ui/` por promover-para-shared (ver `component-library-governance`)
```

Formato livre dentro desta estrutura, desde que cada token citado exista em `tokens.json`.

## Validações automáticas do plan-checker

Rodando em cima do `SPRINT.md`:

1. **Existência dos tokens citados**
   - Parser extrai dot-paths (`color.brand.500`, `space.md`, etc.) da seção `## Visual Contract`
   - Lookup em `docs/identidade-visual/tokens.json`
   - Qualquer token inexistente → **BLOCK** com `reason: token_not_in_design_system:<path>`

2. **Categorias mínimas presentes**
   - Se sprint tem `has_ui: true`, `tokens.json` precisa ter `color` + `space` preenchidos
   - Faltando → **BLOCK** com `reason: incomplete_tokens_json:<missing_categories>`

3. **Componentes novos seguem governance**
   - Se `SPRINT.md` introduz componente listado em `### Componentes novos`, valida contra `component-library-governance`:
     - Componente fica em `packages/ui/` (shared) se atende regra dos 3, ou em `feature/` se é único uso
     - Tem `.stories.ts` previsto no sprint
     - Nome segue prefix convention

4. **Cores citadas = cores usadas**
   - Grep no código escrito durante o sprint (pós-execute): se aparece hex hardcoded, BLOCK no reconcile
   - Regra ESLint `no-hardcoded-colors` ativa em `tooling/eslint/no-hardcoded-colors.js`

## Anti-patterns específicos deste checker

- Sprint com UI e sem seção `## Visual Contract` → BLOCK
- Seção `## Visual Contract` vazia ou genérica ("usa as cores do sistema") → BLOCK por falta de tokens concretos
- Sprint cita token que não existe → BLOCK
- Sprint introduz componente mas não define onde vai (`shared/` vs `feature/`) → WARN
- Componente em `shared/` sem `.stories.ts` previsto → WARN
- Cor hex aparece no código durante execute → reconcile BLOCK

## Integração com skills UX

`## Visual Contract` é o ponto onde as skills de UX são **aplicadas concretamente**. A matriz de obrigatoriedade por `has_ui: true`:

| Skill | Condição adicional | Como é aplicada no SPRINT.md |
|-------|---------------------|---------------------------------|
| `product/component-library-governance` | sempre | Seção `### Componentes novos` decide shared vs feature |
| `quality/accessibility-pro` | sempre | Seção `## A11y Checklist` lista o que o sprint garante (contraste AA, aria, teclado) |
| `br/ux-copywriting-ptbr` | locale=pt-BR | Seção `## Copy` lista strings principais; validadas contra vocabulário canônico do `brand.md` |
| `quality/error-ux-patterns` | se tem form ou estado de erro | Error codes novos listados; mensagens copy-libed |
| `product/micro-animations-delight` | se tem transição não-trivial | Tokens de motion citados na seção Visual Contract |
| `product/visual-regression-testing` | se toca `shared/` | `.stories.ts` previstas no sprint |

Ver `skills-enforcement.md > sprint_ui_matrix` para a matriz canônica.

## Por que isto não é teatro

"Citar token" poderia virar copy-paste mecânico de nomes para agradar o checker. Três proteções contra isso:

1. **Reconcile compara citação com código.** Se `## Visual Contract` diz que usa `color.brand.500` mas o componente implementado usa `#ff0000`, reconcile-state reporta divergência.
2. **ESLint `no-hardcoded-colors` roda em CI.** Hex no código = build quebra.
3. **Revisão visual em Chromatic/Playwright.** Review humano do pixel final, não só do AST.

As três em conjunto fazem "fidelidade visual" ser verificável, não aspiracional.

## Quando o projeto não tem design system pronto

Perfeitamente comum no começo. Duas opções:

**Opção A — Sprint 0 preenche tokens mínimos.** Designer ou dev decide cores principais, espaçamentos, tipografia base, e preenche `tokens.json` com o essencial. Não precisa ser completo — 5 cores, 4 espaçamentos, 3 tipos, pronto. Cresce conforme sprint precisa.

**Opção B — Sprint 0 declara tokens "provisórios" e marca para revisão posterior.** `tokens.json` ganha flag `"_provisional": true` nas entradas não finalizadas. Checker não bloqueia, mas avisa, e força revisão com designer antes do Sprint 3.

A escolha fica registrada em `.planning/config.json > visual_tokens_mode: final | provisional`. Projetos com budget de design: A. Projetos sem: B, sabendo que é dívida que precisa ser paga.

## Related

- Skill: `product/component-library-governance` (governance do design system)
- Skill: `product/visual-regression-testing` (como capturar baselines)
- Skill: `product/micro-animations-delight` (uso de motion tokens)
- Tooling: `tooling/eslint/no-hardcoded-colors.js` (enforcement em build)
- Template: `.claude/get-shit-done/templates/SPRINT.md` (estrutura do sprint)
