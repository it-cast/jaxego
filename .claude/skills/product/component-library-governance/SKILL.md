# Component Library Governance — evitar fragmentação do design system

> Skill obrigatória para projetos com múltiplos apps/surfaces (web + mobile + admin) compartilhando design system.

## Princípio central

Um design system **não é pasta com componentes**. É contrato: toda parte da UI consome via API estável, com stories visuais, tokens semânticos, e política de deprecação. Sem governance, cada feature duplica componentes, variantes proliferam, consistência morre.

## Decisão: shared vs feature-specific

### Promover para `shared/` quando:
- Tem 2+ consumidores ativos
- Uso previsto em > 1 feature nos próximos 3 meses
- Representa conceito do design system (Button, Input, Card) — não lógica de negócio

### Manter em `feature/` quando:
- Único consumidor
- Acoplado a lógica de negócio específica
- Uso pontual (ex: `<CheckoutShippingForm>` só existe no checkout)

**Regra do 3:** primeira ocorrência → cria no feature. Segunda → cria novamente onde precisa. Terceira → promove para `shared/`. Evita generalização prematura baseada em 1 uso.

## Estrutura de repositório

### Monorepo (recomendado)
```
packages/
├── design-tokens/          # CSS vars, SCSS vars, TS consts
├── ui-primitives/          # Button, Input, Card — zero business logic
├── ui-composed/            # OrderCard, UserAvatar — combinam primitivos
└── ui-patterns/            # PageLayout, EmptyState — patterns reutilizáveis
apps/
├── web/                    # consome packages/*
├── mobile/                 # consome packages/*
└── admin/                  # consome packages/*
```

### Polyrepo (último recurso — só se monorepo impossível)
- Package NPM versionado
- Consumidores pinam versão específica
- Breaking changes seguem semver estrito

## Nomenclatura

### Prefixo por origem
```
app-button       → primitivo do design system (app = prefixo do projeto, ex: "acme")
app-order-card   → composto compartilhado
checkout-address-form  → feature-specific (prefixo do feature, não do projeto)
```

### Sufixo por tipo
```
app-button.component.ts
app-button.stories.ts
app-button.spec.ts        # unit
app-button.a11y.spec.ts   # accessibility
```

### Variantes
```typescript
// ❌ multiplos componentes para mesma coisa
<app-primary-button>
<app-secondary-button>
<app-danger-button>

// ✅ um componente, prop variant
<app-button variant="primary">
<app-button variant="secondary">
<app-button variant="danger">
```

## API estável

### Props mínimas, opinião alta

```typescript
// ❌ API com muitos defaults customizáveis
@Input() paddingTop: string = '16px';
@Input() paddingBottom: string = '16px';
@Input() paddingLeft: string = '24px';
@Input() paddingRight: string = '24px';
@Input() fontSize: string = '14px';
@Input() color: string = '#333';

// ✅ API semântica
@Input() size: 'sm' | 'md' | 'lg' = 'md';
@Input() variant: ButtonVariant = 'primary';
// Tokens internos — usuário não escolhe pixel, escolhe conceito
```

### Slots para conteúdo, props para comportamento

```html
<!-- Angular -->
<app-card>
  <div card-header>{{ title }}</div>
  <div card-body>{{ content }}</div>
  <div card-footer>
    <app-button>Ação</app-button>
  </div>
</app-card>

<!-- React: children props -->
<Card>
  <Card.Header>...</Card.Header>
  <Card.Body>...</Card.Body>
  <Card.Footer>...</Card.Footer>
</Card>
```

### Outputs claros

```typescript
// ❌ genérico
@Output() action = new EventEmitter<any>();

// ✅ específico
@Output() clickConfirm = new EventEmitter<void>();
@Output() clickCancel = new EventEmitter<void>();
@Output() changeSelection = new EventEmitter<SelectionChangeEvent>();
```

## Tokens: nunca hex hardcoded

```scss
// ❌
.button {
  background: #3b82f6;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
}

// ✅
.button {
  background: var(--color-brand-500);
  color: var(--color-text-inverse);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
}
```

Se token não existe, **adicionar ao design system primeiro**, depois usar. Nunca um-off.

## Documentação inline

### JSDoc em toda prop pública

```typescript
@Component({...})
export class ButtonComponent {
  /**
   * Variante visual. `primary` para ações principais, `secondary` para complementares,
   * `danger` para ações destrutivas, `ghost` para interações secundárias com pouco peso visual.
   */
  @Input() variant: 'primary' | 'secondary' | 'danger' | 'ghost' = 'primary';
  
  /**
   * Estado de loading. Substitui conteúdo por spinner e desabilita clique.
   * Use quando aguardando resposta async de uma ação.
   */
  @Input() loading: boolean = false;
  
  /**
   * Emitido ao clique (apenas quando não loading e não disabled).
   */
  @Output() clicked = new EventEmitter<void>();
}
```

### Stories como documentação vivente

Storybook docs page gerada automaticamente da JSDoc + stories. Cada variante = uma story.

## Checklist para adicionar componente a `shared/`

- [ ] Tem ≥ 2 consumidores concretos (não especulativo)
- [ ] Tem story Storybook com 5 estados mínimos
- [ ] Tem testes unitários (comportamento + eventos)
- [ ] Tem teste de acessibilidade (jest-axe)
- [ ] Usa apenas tokens — zero hex hardcoded
- [ ] JSDoc em todas as props/outputs públicas
- [ ] Não tem dependência circular (não importa de feature/)
- [ ] Segue nomenclatura `{prefix}-{name}`
- [ ] API mínima e opinativa (tokens, não pixels)
- [ ] Changelog atualizado com entrada "Added"
- [ ] PR aprovado por owner do design system

## Breaking changes & deprecation

### Non-breaking (minor/patch)
- Adicionar prop opcional
- Adicionar variant enum
- Adicionar slot opcional
- Fix visual em estado específico
- Melhorar acessibilidade

### Breaking (major)
- Remover prop, output, ou variant
- Mudar default de prop
- Renomear componente
- Mudar comportamento observável

### Deprecation path

```typescript
@Component({...})
export class OldButtonComponent {
  constructor() {
    console.warn(
      '[DeprecationWarning] <old-button> está deprecated desde v2.3, remoção em v3.0. ' +
      'Use <app-button variant="primary"> no lugar. ' +
      'Docs: https://design-system.acme.com/migration-guides/button-v3'
    );
  }
}
```

Timeline típica:
1. v2.3 — novo componente lançado, antigo marcado deprecated
2. v2.4-2.9 — ambos funcionam; warning na console; migration codemods disponíveis
3. v3.0 — componente antigo removido; migração obrigatória

Comunicação ativa: changelog visível no Storybook, migration guide, suporte via Slack/canal dedicado.

## Prevenção de divergência

### Enforcement via ESLint custom rule

```javascript
// eslint-plugin-design-system/lib/no-hardcoded-colors.js
module.exports = {
  meta: { type: 'problem' },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value === 'string' && /^#[0-9a-f]{3,8}$/i.test(node.value)) {
          context.report({
            node,
            message: `Cor hardcoded '${node.value}'. Use token do design system (var(--color-*)).`,
          });
        }
      },
    };
  },
};
```

Aplicado a arquivos .ts, .html, .scss dentro de `packages/` e `apps/`. Em `tokens/` é permitido (é a única fonte).

### CI check: cobertura de stories

```yaml
- name: Check design system has stories
  run: |
    npx ts-node scripts/check-stories-coverage.ts
    # falha se componente em packages/ui-*/ sem .stories.ts ao lado
```

Script:
```typescript
// scripts/check-stories-coverage.ts
import { glob } from 'glob';
const components = await glob('packages/ui-*/src/**/*.component.ts');
const missing: string[] = [];
for (const c of components) {
  const story = c.replace('.component.ts', '.stories.ts');
  if (!(await fs.pathExists(story))) missing.push(c);
}
if (missing.length) {
  console.error(`Componentes sem story:\n${missing.join('\n')}`);
  process.exit(1);
}
```

### Review checklist

Template de PR para mudança em `packages/ui-*`:
```markdown
## Design system change

- [ ] Componente novo → ≥ 2 consumers previstos
- [ ] Props API revisada com design lead
- [ ] Tokens usados — zero hardcoded
- [ ] Stories cobrem todos os estados
- [ ] Testes a11y passando
- [ ] Não é breaking (ou deprecation path documentado)
- [ ] Changelog entry adicionado
- [ ] Screenshot visual (Chromatic link)
```

## Versioning

### Semver estrito
- **Major (x.0.0)** — breaking change em qualquer componente exportado
- **Minor (0.x.0)** — nova feature, novo componente, novo variant
- **Patch (0.0.x)** — bugfix, ajuste visual menor, doc, perf

### Changelog com seções

```markdown
# Changelog

## [2.3.0] - 2026-04-22

### Added
- `app-toast` com variante `success`
- Prop `compact` em `app-table` para densidade maior

### Changed
- `app-button` ganha estado `loading` com spinner (não-breaking)

### Deprecated
- `<old-button>` será removido em v3.0. Use `<app-button>`.

### Fixed
- `app-modal` focus trap quebrava com conteúdo dinâmico
```

## Ownership

### Design system team
- **1 owner explícito** — toma decisões de API em última instância
- **Contributors** do time amplo — propõem mudanças via PR
- **Design lead** — aprova mudanças visuais e tokens

### Síncronos regulares
- **Triagem semanal** — novos PRs, dúvidas
- **Review mensal** — componentes mais/menos usados, deprecations, direção

### Canal dedicado
- Slack/Discord para dúvidas ("como faço tal coisa?")
- Issues templadas no repo

## Anti-patterns

- Design system como "onde jogo o que não sei onde colocar" — vira lixão
- Componente com 20 props customizáveis — deixa consumidor fazer qualquer coisa = inconsistência
- Breaking change sem deprecation path
- Fork local ("copiei o Button para mudar uma coisinha") — gera divergência
- Sem versionamento → ninguém sabe quando mudou o quê
- Sem ownership → decisões são guerra política, não técnica
- Storybook "morto" (components existem, stories desatualizadas)
- Tokens centrais mas componentes ainda com hex hardcoded
- Design system acoplado a business logic (ex: `OrderCard` que chama API)

## Checklist para PLAN.md

- [ ] Mudança é non-breaking? Senão, deprecation path documentado?
- [ ] Se componente novo: critério dos 2+ consumidores cumprido
- [ ] Stories cobrem novo componente/variante/estado
- [ ] JSDoc em toda prop/output pública nova
- [ ] Tokens usados — ESLint rule de hex passa
- [ ] Test a11y (jest-axe) adicionado
- [ ] Changelog atualizado
- [ ] PR marcado com tag "design-system"
- [ ] Design lead revisou
