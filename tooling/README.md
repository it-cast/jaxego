# Tooling — artefatos de enforcement prontos

Arquivos de configuração para CI e linting que **executam** as regras descritas pelas skills do framework. Sem isso, skills são só documentação — com isso, violações quebram build.

## O que tem aqui

```
tooling/
├── ci/
│   ├── quality.yml.template    ← GitHub Actions para quality gates
│   ├── bundlesize.config.json  ← orçamentos de bundle JS
│   ├── lighthouserc.json       ← thresholds Core Web Vitals
│   └── pa11yci.json            ← thresholds de a11y automática
├── pre-commit/
│   └── .pre-commit-config.yaml ← hooks locais (ruff, mypy, eslint, prettier)
├── jest/
│   └── jest.setup.a11y.js      ← setup jest-axe global
└── eslint/
    └── no-hardcoded-colors.js  ← custom rule (protege design tokens)
```

## Como instalar em projeto existente

### 1. CI (GitHub Actions)

```bash
# Na raiz do projeto:
mkdir -p .github/workflows
cp tooling/ci/quality.yml.template .github/workflows/quality.yml
cp tooling/ci/bundlesize.config.json .
cp tooling/ci/lighthouserc.json .
cp tooling/ci/pa11yci.json .
```

Editar `quality.yml`:
- Ajustar path de build (`dist/`, `build/`, etc.)
- Ajustar URL de dev server para Lighthouse CI
- Setar secrets no GitHub: `CHROMATIC_PROJECT_TOKEN` (se usa Chromatic)

### 2. Pre-commit

```bash
cp tooling/pre-commit/.pre-commit-config.yaml .
pip install pre-commit
pre-commit install
```

Primeira rodada manual: `pre-commit run --all-files`. Corrigir o que precisar.

### 3. Jest + axe (tests de a11y)

```bash
cp tooling/jest/jest.setup.a11y.js src/test/
npm install --save-dev jest-axe @types/jest-axe
```

No `jest.config.js`:
```js
module.exports = {
  setupFilesAfterEach: ['<rootDir>/src/test/jest.setup.a11y.js'],
};
```

Usar em testes de componente:
```typescript
import 'jest-axe/extend-expect';

it('has no a11y violations', async () => {
  const { container } = render(<MyComponent />);
  expect(await axe(container)).toHaveNoViolations();
});
```

### 4. ESLint custom rule

Opcional — se quer enforçar tokens de design system:

```bash
cp tooling/eslint/no-hardcoded-colors.js .eslint-rules/
```

No `.eslintrc.js`:
```js
module.exports = {
  rulePaths: ['.eslint-rules'],
  rules: { 'no-hardcoded-colors': 'error' },
};
```

## Relação com skills

| Artefato | Skill relacionada |
|----------|---------------------|
| `lighthouserc.json` | `quality/performance-web-vitals` |
| `bundlesize.config.json` | `quality/performance-web-vitals` |
| `pa11yci.json` + `jest.setup.a11y.js` | `quality/accessibility-pro` |
| `no-hardcoded-colors.js` | `product/component-library-governance` |
| `.pre-commit-config.yaml` | Todas — enforcement local |
| `quality.yml.template` | Integra todos acima |

## Ajustes esperados por projeto

Os números nos configs (thresholds, budgets) são **defaults sensatos**, não absolutos. Ajustar conforme realidade:

- Projeto greenfield: pode ser mais apertado
- Projeto legado: começar frouxo e apertar progressivamente
- Revisar trimestralmente (captura de dados via `bin/collect-metrics.sh` ajuda)
