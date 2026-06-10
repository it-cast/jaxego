# UI-SPEC — Phase {N}: {nome}

> Design contract. Gerado por `gsd-ui-researcher` em {date}. Aprovado por `gsd-ui-checker` em {date}.
> **BLOQUEIA** `plan-phase` se não existir (Gate 2 do framework).
> Plataforma: {web | mobile | web+mobile}

---

## Fontes de verdade consultadas

- `docs/identidade-visual/design-system.md` — {resumo em 1 linha}
- `docs/identidade-visual/tokens.json` — {tokens herdados}
- `docs/identidade-visual/brand.md` — {tom, personalidade}
- Fases anteriores:
  - Phase {X} UI-SPEC.md — componentes herdados: {lista}
- Skills consultadas:
  - `design-to-code` — regra: design → tokens → implementação (nunca direto ao framework)
  - `ui-ux-pro-max` — princípios aplicados: {lista curta}
  - `{plataforma específica}` — `angular-material-patterns` | `react-patterns` | `ionic-patterns`

---

## Telas cobertas por esta fase

Cada tela tem seção completa abaixo:

1. {tela 1}
2. {tela 2}
3. {tela N}

---

## Design tokens (herdados + específicos desta fase)

**Herdados de `docs/identidade-visual/tokens.json`:** sem mudanças (referência acima).

**Novos tokens propostos (se aplicável):**

```css
/* adicionar em tokens.json após aprovação — use prefixo do projeto (ver specs/project.yaml) */
--{prefix}-{status-semantico-1}: var(--color-success-500);
--{prefix}-{status-semantico-2}: var(--color-warning-500);
```

Nenhum `#hex` hardcoded em código. Todo valor visual = token.

---

## Tipografia

- Scale herdada: {h1=32, h2=24, body=16, caption=12}
- Peso: regular 400, medium 500, semibold 600, bold 700
- Font-family: via token `--font-sans`, nenhum `font-family: "X"` inline em template

---

## Espaçamento

- Base: 4px (como no sistema)
- Scale: 4, 8, 12, 16, 24, 32, 48, 64
- Uso de tokens: `padding: var(--space-md)` — nunca `padding: 16px`

---

## Copy (texto visível ao usuário)

Aplicando `ux-copywriting-ptbr` (ou equivalente do locale):

| Localização | Texto | Observação |
|-------------|-------|------------|
| Header | "{título da tela}" | Tom: direto, sem "Bem-vindo a" |
| Empty state | "{Nenhum X ainda}" + CTA "{ação específica}" | Acionável, sem "não há dados" |
| Erro network | "Não conseguimos carregar {recurso}. Tente novamente em alguns segundos." | Específico + ação |
| Loading | Skeleton do layout real, não spinner | Reflete estrutura esperada |
| Success toast | "{ação-no-pretérito}" (ex: "Pedido enviado", "Item salvo") | Curto, confirma a ação |

**Sem abreviação, sem jargão técnico, sem "Ops!"**.

---

## Estados por componente/tela

Todo componente/tela declara 5 estados mínimos:

### {Tela 1}: {nome}

| Estado | Quando ocorre | Como aparece |
|--------|---------------|--------------|
| **Loading** | Ao montar, requisição em curso | Skeleton do card principal (não spinner) |
| **Empty** | API retornou 0 items | Ilustração + copy + CTA |
| **Success** | Dados carregados | Layout completo |
| **Error** | 4xx ou 5xx da API | Mensagem específica + retry |
| **Offline** (mobile) | Sem rede, com cache | Banner "Modo offline" + dados em cache marcados |

---

## Interações e micro-animações

Aplicando `micro-animations-delight`:

- **Botão ao clicar:** scale 0.95 em 100ms, ease-out
- **Card ao abrir:** slide-up 200ms, spring
- **Remoção de item:** collapse height + fade 300ms
- **Celebração (ex: ação crítica confirmada):** ✓ animado + cor de sucesso flash 400ms
- **Transição entre telas:** 200-300ms, respeitar `prefers-reduced-motion`

Anti-patterns proibidos:
- Animação > 500ms em ação crítica
- Loop infinito sem pausa
- Animar propriedades além de `transform`/`opacity`

---

## Acessibilidade (mínimo obrigatório)

Aplicando `accessibility-pro`:

- [ ] Contraste ≥ 4.5:1 em texto normal, 3:1 em texto grande
- [ ] Todo input tem `<label>` associado (for/id)
- [ ] Todo botão icon-only tem `aria-label`
- [ ] Focus visível em todos os interativos (não remover `outline`)
- [ ] Ordem de tabulação lógica (top-left → bottom-right)
- [ ] Modal tem focus trap + esc para fechar + role="dialog"
- [ ] Live regions para toasts (`aria-live="polite"`)
- [ ] Landmark roles (`<main>`, `<nav>`, `<aside>`)

Validação no CI: `axe-core` rodando em staging. Zero violations críticas.

---

## Responsividade

Breakpoints herdados: 320, 480, 768, 1024, 1440.

Layout por tela:

| Tela | Mobile (320-480) | Tablet (768) | Desktop (1024+) |
|------|------|------|------|
| {tela 1} | stack vertical | 2 colunas | 3 colunas + sidebar |

---

## Seções exclusivas MOBILE (se platform inclui mobile)

Aplicando `mobile/*` skills.

### Safe areas

- iOS notch: `padding-top: env(safe-area-inset-top)`
- Android navbar: `padding-bottom: env(safe-area-inset-bottom)`
- Classes Ionic: `ion-padding` ou custom com `--ion-safe-area-*`

### Keyboard behavior

- Input em formulário: `scroll-assist` + `scroll-padding` para não esconder
- Botão primário acima do teclado (position sticky ou keyboard avoidance)
- `enterkeyhint="next"` em input não-final, `"send"` no último
- `inputmode` correto: `numeric` para CEP/CPF, `tel` para telefone, `email` para email

### Touch targets

- Mínimo 44×44 px (iOS HIG) / 48×48 dp (Material)
- Áreas clicáveis pequenas (ex: close icon) = expandir hitbox invisível

### Gestures

- Swipe-to-delete em lista? Declarar com haptic feedback leve
- Pull-to-refresh em listagem? Incluir indicador customizado
- Back hardware Android: rota correta, não fecha app

### Offline behavior

Declarar por tela:

| Tela | Offline | Comportamento |
|------|---------|---------------|
| Lista de recursos (read-only) | Cache | Mostra último estado + banner "Sincronizando" |
| Criação de recurso | Fila | Salva local + sincroniza ao reconectar |
| Pagamento | Bloqueado | Modal "Ação requer conexão. Verifique sua rede." |

### First-load perf

- Splash screen < 1s
- Skeleton (não spinner) até conteúdo aparecer
- Imagens: WebP + lazy loading

---

## Performance budget específico desta fase

Dentro do budget global:

- Lazy loading: {rotas a lazy-loadar}
- Imagens: WebP obrigatório, `loading="lazy"` abaixo da dobra
- Bundle incremental desta fase ≤ {N} KB gzip

---

## Visual regression

Aplicando `visual-regression-testing`:

Componentes novos desta fase que DEVEM ter story no Storybook:

- [ ] `{prefix}-{component-name}` — stories: {loading, default, com-dados, erro, vazio}
- [ ] `{prefix}-{outro-component}` — stories: {default, variant}

Nome de screenshot: `{component}-{state}-{viewport}.png`
Baseline capturada ao fim da fase, roda em CI daqui em diante.

---

## Open questions para o humano

Se o researcher não conseguiu decidir sozinho:

- [ ] {questão 1} — **recomendação do researcher:** {opção}
- [ ] {questão 2}

---

## Approval

- [ ] Humano revisou e aprovou (ou delegou ao ui-checker)
- [ ] ui-checker validou 6 dimensões: tokens, tipografia, copy, estados, interações, acessibilidade
- [ ] Aprovado em: {date}

**Próximo passo:** `/gsd-plan-phase {N}` — o planner recebe este UI-SPEC como contexto.
