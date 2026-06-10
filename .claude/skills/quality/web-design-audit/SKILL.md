---
name: quality:web-design-audit
description: "Auditoria sistemática de UI contra 100+ regras de Web Interface Guidelines (acessibilidade, performance, UX). Use ao final de phase com UI: revisar componentes, páginas, formulários, contra checklist exaustivo de ARIA, focus states, touch targets, reduced-motion, semantic HTML, keyboard nav, heading hierarchy. Output em formato file:line:rule para ação imediata. Complementa quality/accessibility-pro (que foca em WCAG narrow); esta skill é cobertura ampla."
priority: high
tier: 2
phase_types:
  - ui-audit
  - phase-close
  - pre-launch
  - accessibility-review
keywords:
  pt-BR:
    - auditar UI
    - revisar interface
    - checklist UI
    - acessibilidade ampla
    - inspecionar UI
    - revisão de UI
    - audit antes de release
    - checagem final UI
    - revisão de boas práticas UI
    - validar interface
  en:
    - audit UI
    - check accessibility
    - review UI
    - design audit
    - web interface guidelines
    - WCAG check
    - review UX
    - check site against best practices
    - pre-launch UI review
    - UI compliance check
flags:
  has_ui: true
  is_phase_close: true
references:
  - source: vercel-labs/agent-skills
    path: skills/web-design-guidelines
    license: MIT
    last_updated: 2026-01
  - source: vercel-labs/web-interface-guidelines
    description: Canonical rule source (fetch via WebFetch)
---

# Web Design Audit — checklist sistemático antes de fechar phase com UI

Audita código UI contra 100+ regras de **Web Interface Guidelines** mantidas por Vercel Engineering. Não é inspiração visual (use `frontend-design`/`ui-ux-pro-max` para isso); é **conformidade**.

## Quando aplicar

- **Final de phase com UI** — checklist obrigatório antes de fechar
- **Pré-launch** — pega defeitos que escapam de revisão visual
- **Pull request review** de feature com UI substancial
- **Pós-design-system update** — verificar que rules continuam válidas

## Quando NÃO aplicar

- Phases sem UI (backend, infra, data) — desperdício de tokens
- Iteração inicial de design (use `frontend-design` em vez disso)
- Escopo cirúrgico de bug fix (rodar audit completo é overkill)

## Como rodar

A skill **busca as regras canônicas via WebFetch** (não duplica conteúdo localmente — fica sempre atualizada):

```
URL canônico: https://github.com/vercel-labs/web-interface-guidelines
```

Workflow:

1. Determinar files alvo (default: `src/components/**/*.tsx` + `src/pages/**/*.tsx`)
2. WebFetch das guidelines mais recentes
3. Para cada file, checar contra cada regra aplicável
4. Output em formato `file:line:rule_id:severity:description`
5. Agrupar por severidade (CRITICAL > HIGH > MEDIUM > LOW)

## 8 categorias cobertas

| Categoria | Foco | Severidade média |
|---|---|---|
| ARIA & Semantic HTML | aria-label, aria-describedby, role, semantic tags | CRITICAL |
| Focus & Keyboard | visible focus, tab order, escape handling, skip links | CRITICAL |
| Forms | labeled inputs, error association, autocomplete, required | HIGH |
| Touch & Pointer | 44pt min target, hit area, hover != touch | HIGH |
| Motion & Animation | reduced-motion respect, no autoplay, no infinite loops | HIGH |
| Heading hierarchy | h1 único, sem pular níveis, h2 sem h1 acima | HIGH |
| Color & Contrast | WCAG AA mínimo, AAA preferível, não-cor-only signal | MEDIUM |
| Performance | LCP, CLS, layout shift, image lazy, font subset | MEDIUM |

## Output esperado

```
src/components/Modal.tsx:23: focus-trap-missing CRITICAL
  Modal aberto não captura focus — keyboard user perde contexto.
  Fix: usar @radix-ui/react-dialog ou implementar focus-trap manual.

src/pages/checkout.tsx:87: aria-live-missing HIGH
  Erro de validação inline sem aria-live="polite".
  Screen reader não anuncia erro — user submete form repetidamente.
  Fix: <div aria-live="polite" role="alert">{error}</div>

src/components/Button.tsx:12: focus-visible-only MEDIUM
  Focus ring usa :focus em vez de :focus-visible.
  Mouse users veem outline ao clicar — UX ruim, mas a11y ok.
  Fix: trocar para :focus-visible.
```

## Diferença vs `quality/accessibility-pro`

| Aspecto | accessibility-pro | web-design-audit |
|---|---|---|
| Escopo | WCAG 2.1/2.2 specific | 100+ regras Web Interface Guidelines (inclui WCAG + UX) |
| Quando usar | Durante design e implementação inline | Auditoria sistemática **ao final da phase** |
| Output | Decisões durante código | Lista de gaps file:line:rule |
| Frequência | Contínua | 1x por phase / pré-launch |

**Use AS DUAS** — accessibility-pro guia escrita do código, web-design-audit fecha gaps que escaparam.

## Integração com framework GSD

- **Skill obrigatória** quando `phase_close: true` E `has_ui: true` no ROADMAP
- **Output deve gerar TDs** se gaps são MEDIUM/LOW (não bloqueantes)
- **Output deve bloquear close** se gaps são CRITICAL (focus trap missing, aria errado em form, etc.)
- **Rodar antes de** `gsd-skill-application-check` no fim da phase

## Limitação honesta

Esta skill depende de **WebFetch funcional** para as regras mais recentes. Em ambiente offline ou com acesso restrito ao github.com:

1. **Snapshot manual**: clone `vercel-labs/web-interface-guidelines` localmente e ajuste a skill para apontar para o path local
2. **Fallback degradado**: usar apenas `quality/accessibility-pro` (mais estreita mas autossuficiente)

## Source

Adaptado de [vercel-labs/agent-skills/web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) (MIT, 19k stars, 133k installs/sem). Regras canônicas em [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines).

Decisão de adoção: skill **revisada manualmente** — autor vetted (Vercel Engineering), regras observáveis em todo dev sênior, sem prompt injection, dependência única (WebFetch) bem documentada.
