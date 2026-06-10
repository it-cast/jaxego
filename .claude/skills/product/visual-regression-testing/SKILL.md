# Visual Regression Testing — Storybook + Chromatic/Percy/Playwright

> Skill obrigatória para projetos com design system que cresce. Sem baseline visual automatizado, qualquer refactor de CSS quebra componentes silenciosamente até alguém reportar em produção.

## Princípio central

Testes unitários dizem "a função retorna certo". Testes visuais dizem "o pixel certo apareceu". São ortogonais — um componente pode passar em 100% dos testes unitários e estar visualmente quebrado. O inverso também é verdade. Portanto: **todo componente reutilizável do design system tem story + baseline visual**.

## Stack

| Ferramenta | Função | Trade-off |
|------------|--------|-----------|
| **Storybook** | Cataloga componentes em isolamento | Setup inicial de 1-2 dias; daí vira autodocumentação |
| **Chromatic** | Hosting + diff visual em CI | Pago acima de 5k snapshots/mês; melhor integração com Storybook |
| **Percy** (BrowserStack) | Alternativa a Chromatic | Similar em preço |
| **Playwright `toHaveScreenshot()`** | Self-hosted | Zero custo, setup mais braçal, sem UI de review |
| **Loki** | Self-hosted + Storybook | Fosco na manutenção |

**Recomendação por perfil:**
- Projeto comercial, time > 3 devs: **Chromatic** (ROI compensa)
- Projeto open-source ou pequeno: **Playwright screenshots** (gratuito)
- Time enterprise com BrowserStack já contratado: **Percy**

## O que deve ter story

### Obrigatório
- Todo componente em `libs/ui/` ou `packages/design-system/` ou `apps/*/src/components/shared/`
- Todo componente com 3+ consumidores
- Páginas inteiras com layout crítico (login, checkout, dashboard inicial)

### Opcional
- Componentes feature-specific com 1 consumidor (pode ficar sem)
- Wrappers triviais

### Nunca
- Componentes com dados hardcoded de usuário real
- Stories que chamam API real (usar mocks/fixtures)

## Anatomia de uma story

```typescript
// libs/ui/button/button.stories.ts
import { Meta, StoryObj } from '@storybook/angular';
import { ButtonComponent } from './button.component';

const meta: Meta<ButtonComponent> = {
  title: 'UI/Button',
  component: ButtonComponent,
  parameters: {
    docs: {
      description: {
        component: 'Botão primário do design system. 5 variantes, 3 tamanhos.',
      },
    },
  },
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'danger', 'ghost', 'link'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    loading: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
};
export default meta;

type Story = StoryObj<ButtonComponent>;

export const Primary: Story = { args: { variant: 'primary', label: 'Confirmar' } };
export const Secondary: Story = { args: { variant: 'secondary', label: 'Cancelar' } };
export const Danger: Story = { args: { variant: 'danger', label: 'Excluir' } };
export const Loading: Story = { args: { variant: 'primary', label: 'Salvando', loading: true } };
export const Disabled: Story = { args: { variant: 'primary', label: 'Indisponível', disabled: true } };

// Matrix para cobrir combinações críticas
export const AllVariants: Story = {
  render: () => ({
    template: `
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; padding: 24px">
        <app-button variant="primary" size="sm">Primary SM</app-button>
        <app-button variant="primary" size="md">Primary MD</app-button>
        <app-button variant="primary" size="lg">Primary LG</app-button>
        <!-- ... -->
      </div>
    `,
  }),
};
```

### Stories para os 5 estados mínimos

Todo componente com dados tem stories para:
1. **Loading** — skeleton ou spinner
2. **Empty** — vazio com CTA
3. **Populated** — com dados reais (via fixture)
4. **Error** — estado de erro com retry
5. **Offline** (se mobile) — adicional

```typescript
export const Loading: Story = { args: { isLoading: true } };
export const Empty: Story = { args: { items: [] } };
export const WithData: Story = { args: { items: mockOrdersFixture } };
export const Error: Story = { args: { error: { code: 'NETWORK_ERROR', message: 'Sem conexão' } } };
```

## Fixtures

```typescript
// libs/ui/testing/fixtures/orders.fixture.ts
export const mockOrder = (overrides?: Partial<Order>): Order => ({
  id: 'order_fixture_1',
  status: 'confirmed',
  amount: '450.00',
  currency: 'BRL',
  created_at: '2026-04-22T10:00:00Z',
  customer: { id: 'cust_1', name: 'Cliente Exemplo' },
  ...overrides,
});

export const mockOrdersList = (n = 5): Order[] =>
  Array.from({ length: n }, (_, i) => mockOrder({ id: `order_${i}` }));
```

Fixtures em arquivo separado permitem reuso entre stories, testes unitários, e e2e.

## Playwright screenshots (alternativa self-hosted)

```typescript
// tests/visual/button.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Button component', () => {
  test('primary default', async ({ page }) => {
    await page.goto('/storybook?path=/story/ui-button--primary');
    await page.locator('app-button').waitFor();
    await expect(page.locator('app-button')).toHaveScreenshot('button-primary-default.png', {
      maxDiffPixels: 100,  // tolerância a anti-aliasing
    });
  });
  
  test('loading state', async ({ page }) => {
    await page.goto('/storybook?path=/story/ui-button--loading');
    await page.locator('app-button[data-loading]').waitFor();
    await expect(page.locator('app-button')).toHaveScreenshot('button-loading.png');
  });
});
```

Nomenclatura de screenshot: `{component}-{state}-{viewport?}.png`

Viewports múltiplos:
```typescript
test.describe.parallel('responsivo', () => {
  [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1440, height: 900 },
  ].forEach(({ name, width, height }) => {
    test(`order card - ${name}`, async ({ page }) => {
      await page.setViewportSize({ width, height });
      await page.goto('/storybook?path=/story/ui-order-card--populated');
      await expect(page).toHaveScreenshot(`order-card-populated-${name}.png`);
    });
  });
});
```

## CI integration

### Chromatic

```yaml
# .github/workflows/chromatic.yml
- name: Publish to Chromatic
  uses: chromaui/action@v11
  with:
    projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
    exitOnceUploaded: true
    onlyChanged: true  # só processa stories afetadas
    autoAcceptChanges: main  # branch main auto-accept
```

Workflow:
1. PR push → Chromatic tira screenshots
2. Compara com baseline de `main`
3. Se há diff visual, comenta no PR com UI de review
4. Humano aceita (= novo baseline) ou rejeita (= bug)
5. Aceite → próxima comparação usa nova baseline

### Playwright self-hosted

```yaml
- name: Visual regression
  run: npx playwright test --project=visual
- name: Upload diffs on failure
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: playwright-report
    path: playwright-report/
```

Baselines commitadas em `tests/visual/__screenshots__/`. Atualizar intencionalmente:
```bash
npx playwright test --update-snapshots
git add tests/visual/__screenshots__/
```

## Lidando com flakiness

Fontes comuns de falsos positivos:
- **Anti-aliasing de fontes** → `maxDiffPixels: 100` ou `threshold: 0.2`
- **Animações em curso** → desabilitar via CSS nas stories:
  ```css
  .sb-show-main * {
    animation: none !important;
    transition: none !important;
  }
  ```
- **Datas dinâmicas** (`new Date()`) → mockar data nas fixtures
- **Cursor piscando em input** → `page.locator('body').click({ position: { x: 0, y: 0 } })` antes do screenshot
- **Scrollbar diferente OS a OS** → rodar CI em Linux consistente (Ubuntu) + Chromium consistente
- **Skeletons shimmer** → desabilitar animação via prop `[disableAnimation]` ou via CSS em story mode

## Cobertura recomendada

Não precisa de 100% dos componentes — foco em impacto:

| Categoria | Cobertura alvo |
|-----------|----------------|
| Design system primitivos (Button, Input, Card) | 100% |
| Componentes compostos compartilhados (OrderCard, UserAvatar, NavBar) | 100% |
| Páginas críticas (Login, Checkout, Dashboard) | 80-100% |
| Componentes feature-specific com 1 consumer | 0-30% |
| Layout containers triviais | 0% |

Métrica saudável: > 80% de componentes `shared/` com story.

## Anti-patterns

- Usar dados reais de produção em fixtures (vaza PII)
- Story sem nomear estado (`Default` para tudo — vira "Default 1", "Default 2")
- Baseline desatualizada commitada (nunca re-snapshot sem revisão visual humana)
- Screenshots com date-time real (quebra a cada run)
- Tolerância muito alta (`maxDiffPixels: 10000` esconde bugs reais)
- Apenas desktop — ignorar mobile
- Stories só para componentes perfeitos — estado de erro/empty é onde bugs visuais moram
- Storybook com versão desatualizada em relação ao app principal (divergência no build)

## Integração com outros processos

- **Design review** — designer abre Storybook, valida antes do merge
- **A11y** — `@storybook/addon-a11y` mostra violations axe inline
- **Docs** — `@storybook/addon-docs` gera site público (Zeroheight-like)
- **PR review** — reviewer confere screenshots anexados no Chromatic UI

## Checklist para PLAN.md

- [ ] Storybook instalado e rodando
- [ ] Todo componente novo em `shared/` tem story
- [ ] Cada componente com 5 estados mínimos (loading/empty/populated/error/offline)
- [ ] Fixtures em arquivo dedicado, reutilizáveis
- [ ] Screenshots em CI (Chromatic ou Playwright)
- [ ] Baselines commitadas (Playwright) ou autoaceite em main (Chromatic)
- [ ] Animações desabilitadas em stories para evitar flakiness
- [ ] Cobertura de viewports (mobile + desktop mínimo)
- [ ] A11y addon ativo no Storybook
- [ ] Métrica de cobertura >= 80% de componentes shared com story
