# Accessibility Pro — a11y em CI, não apenas checklist manual

> Skill obrigatória para qualquer fase com UI.
> Endereça a lacuna do relatório 3: a11y tratada como "checklist manual no review" em vez de enforcement automatizado.

## WCAG 2.1 AA como piso

Target mínimo: **WCAG 2.1 Level AA** em todas as rotas públicas.

Dimensões cobertas:
- **Perceivable** — contraste, texto alternativo, legendas
- **Operable** — teclado, tempo, epilepsia
- **Understandable** — language tag, erros claros, consistência
- **Robust** — semantic HTML, aria correto

## Enforcement automático em CI

### axe-core (unit / integration tests)

```typescript
// testing-library + jest-axe
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

test('proposal-card é acessível', async () => {
  const { container } = render(<ProposalCard proposal={mockProposal} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

Aplicar em **todo** componente visual no design system. CI bloqueia PR com violations.

### Lighthouse CI (e2e)

```yaml
# .github/workflows/a11y.yml
- name: Lighthouse CI
  run: |
    npx lhci autorun \
      --collect.url=http://localhost:3000/ \
      --collect.url=http://localhost:3000/proposals \
      --assert.assertions.categories:accessibility=0.95
```

Threshold: 95/100 em Lighthouse a11y score. Abaixo = PR bloqueado.

### pa11y (automation cross-browser)

```bash
npx pa11y-ci --config .pa11yci.json
```

`.pa11yci.json`:
```json
{
  "defaults": {
    "standard": "WCAG2AA",
    "timeout": 30000
  },
  "urls": [
    "http://localhost:3000/",
    "http://localhost:3000/proposals",
    "http://localhost:3000/login"
  ]
}
```

## Regras por categoria

### Contraste

- Texto normal: **≥ 4.5:1**
- Texto grande (18pt+ ou 14pt+ bold): **≥ 3:1**
- UI components (bordas de input, icons interativos): **≥ 3:1**

Validar com: Chrome DevTools color picker (mostra contraste automaticamente), ou `color-contrast-checker` em CI.

Caso crítico: **placeholder não é texto primário**. Label sempre visível.

### Teclado

Todo interativo deve ser:
1. Alcançável via Tab (ordem lógica)
2. Acionável via Enter (button) ou Space (button) ou Enter (link)
3. Visible focus state (outline nunca removido sem substituto visual)

**Anti-patterns:**
- `outline: none` sem `:focus-visible` substituto
- `tabindex="5"` (tabindex positivo quebra ordem)
- Custom `<div onClick>` sem `role="button"` + `tabindex="0"` + handler de Enter/Space

**Padrão correto para custom button:**
```html
<div role="button" tabindex="0" 
     onClick={handleClick}
     onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleClick()}
     aria-label="Confirmar">
  ✓
</div>
```

Melhor ainda: usar `<button>` e estilizar.

### Labels e nomes acessíveis

Todo `<input>` tem:
```html
<label for="cpf-input">CPF</label>
<input id="cpf-input" name="cpf" type="text" inputmode="numeric" />
```

Ou:
```html
<label>
  CPF
  <input name="cpf" type="text" />
</label>
```

Ou com `aria-labelledby`:
```html
<span id="cpf-label">CPF</span>
<input aria-labelledby="cpf-label" type="text" />
```

**NUNCA:** placeholder como único label. `aria-label` em ícone quando não há texto visível.

### Landmarks

Toda página tem:
```html
<header><!-- ou role="banner" --></header>
<nav><!-- ou role="navigation" com aria-label --></nav>
<main><!-- principal conteúdo, um só por página --></main>
<aside><!-- ou role="complementary" --></aside>
<footer><!-- ou role="contentinfo" --></footer>
```

Multiple navs: cada um com `aria-label` único ("Navegação principal", "Breadcrumb", "Menu do usuário").

### Modal e dialog

```typescript
// Padrão focus trap
const Modal = ({ isOpen, onClose, children }) => {
  const firstFocusableRef = useRef();
  const lastFocusableRef = useRef();
  
  useEffect(() => {
    if (isOpen) {
      const previousFocus = document.activeElement;
      firstFocusableRef.current?.focus();
      return () => (previousFocus as HTMLElement)?.focus();
    }
  }, [isOpen]);

  return isOpen && (
    <div role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <h2 id="modal-title">...</h2>
      <button ref={firstFocusableRef} onClick={onClose}>Cancelar</button>
      {children}
      <button ref={lastFocusableRef} onClick={handleConfirm}>OK</button>
    </div>
  );
};
```

Esc fecha modal. Focus trap retorna ao elemento que abriu o modal. Overlay click opcional (UX decide).

### Live regions

Para feedback assíncrono (toast, validação inline que aparece após blur):

```html
<div aria-live="polite" aria-atomic="true">
  {toast && <span>{toast.message}</span>}
</div>
```

- `polite` — não interrompe leitor de tela, fila
- `assertive` — interrompe imediatamente (usar só para alerta crítico)

### Formulários

Erros:
```html
<input aria-invalid="true" aria-describedby="cpf-error" />
<span id="cpf-error" role="alert">CPF deve ter 11 dígitos</span>
```

Required:
```html
<label>
  CPF <span aria-label="obrigatório">*</span>
  <input required aria-required="true" />
</label>
```

Inputmode correto:
```html
<input type="text" inputmode="numeric" pattern="[0-9]*" /> <!-- CEP/CPF -->
<input type="tel" /> <!-- telefone -->
<input type="email" /> <!-- email -->
```

### Motion e animação

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Nenhuma animação essencial — transição entre telas ok, mas não o pulsar de um CTA que exige reduced-motion para funcionar.

### Cor não é único canal

Nunca comunicar informação **só** por cor:
- ❌ "Campo inválido em vermelho"
- ✅ Campo inválido em vermelho + ícone ⚠️ + texto abaixo

### Idioma

```html
<html lang="pt-BR">
```

Trechos em outro idioma:
```html
<span lang="en">Fair use</span>
```

### Imagens

```html
<!-- informativa -->
<img src="chart.png" alt="Gráfico mostra vendas Q1 cresceram 15%" />

<!-- decorativa -->
<img src="pattern.svg" alt="" role="presentation" />

<!-- complexa (mapa, chart detalhado) -->
<img src="map.png" alt="Mapa do Brasil" />
<p>Descrição detalhada: São Paulo concentra 40% dos usuários, seguido por...</p>
```

SVG:
```html
<svg role="img" aria-label="Ícone de check">
  <title>Check</title>
  <path d="..."/>
</svg>
```

## Teste manual (complementar ao automatizado)

Automação pega 30-40% dos problemas. Restante:

1. **Navegação só com teclado** — toda rota principal percorrida sem mouse
2. **VoiceOver (Mac) ou NVDA (Win)** — ativar e ouvir rotas principais. Descrições fazem sentido? Ordem é lógica?
3. **Zoom 200%** — layout quebra? Texto corta?
4. **Modo de alto contraste (Windows)** — botões ainda visíveis?

Humano faz esse teste em PR que adiciona rotas significativas. Documentar no REVIEW.md.

## Componentes problemáticos e soluções

### Custom dropdown

Usar `<select>` se simples. Se complexo (com busca, multi-select), seguir padrão ARIA do APG (Authoring Practices Guide):
- `role="combobox"` no input
- `role="listbox"` no container de opções
- `role="option"` nas opções
- Keyboard: Arrow Up/Down navega, Enter seleciona, Esc fecha

### Toast

`aria-live="polite"` + `role="status"`. Nunca `role="alert"` salvo erro crítico (muito intrusivo).

### Data table

```html
<table>
  <caption>Seus pedidos (5 itens)</caption>
  <thead>
    <tr>
      <th scope="col">Pedido</th>
      <th scope="col">Status</th>
      <th scope="col">Valor</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">#A-1042</th>
      <td>Confirmado</td>
      <td>R$ 450</td>
    </tr>
  </tbody>
</table>
```

### Infinite scroll

Desafio de a11y. Alternativas:
- Botão "Carregar mais" explícito (recomendado)
- Se infinite, anunciar "N novos itens carregados" via live region

### Carousel

Evitar se possível. Se necessário:
- Controles prev/next visíveis
- Auto-play opcional e pausável
- Indicadores de slide (bullets) com aria-label

## Checklist para PLAN.md (fases com UI)

- [ ] Contraste ≥ 4.5:1 validado (Chrome DevTools ou tool automático)
- [ ] Toda rota navegável apenas com Tab/Enter
- [ ] Focus visível em todos interativos (`:focus-visible` ou `outline`)
- [ ] Todo input tem `<label>` associado
- [ ] Todo icon-only button tem `aria-label`
- [ ] Landmarks `<main>`, `<nav>`, `<header>` presentes, um `<main>` por página
- [ ] Modal com focus trap + esc + role="dialog" + aria-labelledby
- [ ] Toast com `aria-live="polite"` ou `role="status"`
- [ ] `prefers-reduced-motion` respeitado em todas as animações
- [ ] `lang="pt-BR"` (ou locale correto) no `<html>`
- [ ] Imagens com alt apropriado (vazio para decorativas)
- [ ] jest-axe rodando em unit tests dos componentes novos
- [ ] Lighthouse a11y score ≥ 95 em CI
- [ ] Teste manual com teclado + screen reader nas rotas críticas
