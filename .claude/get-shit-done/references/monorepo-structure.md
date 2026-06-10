# Monorepo Structure — padrão v0.5.0

> Default do framework: monorepo com pasta `apps/`. Cada aplicação (API, web, mobile) vive em sua própria sub-pasta com `package.json` ou `pyproject.toml` próprio.

## Estrutura canônica

```
projeto/
├── apps/
│   ├── api/                 # Backend (FastAPI, NestJS, Gin, etc.)
│   │   ├── src/             # ou app/, source/, lib/ conforme stack
│   │   ├── tests/
│   │   ├── pyproject.toml   # ou package.json, go.mod
│   │   └── Dockerfile
│   ├── web/                 # Frontend web (Angular, React, Vue)
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── angular.json     # ou next.config.js, vite.config.ts
│   └── mobile/              # App mobile (Ionic/Capacitor, RN, Flutter)
│       ├── src/
│       ├── ios/             # gerado pelo Capacitor build
│       ├── android/
│       └── package.json
│
├── packages/                # opcional: código compartilhado entre apps
│   ├── shared-types/        # TypeScript types compartilhados
│   ├── api-client/          # SDK auto-gerado da API
│   └── design-tokens/       # tokens.json gerado
│
├── tools/                   # opcional: scripts e ferramentas
│   ├── scripts/
│   └── ci/
│
├── docs/                    # documentação humana (canônico do projeto)
├── specs/                   # specs estruturadas (yaml)
├── .planning/               # estado do framework
└── .claude/                 # framework instalado
```

## Quando usar monorepo (default)

- Projeto B2B/B2C com web + mobile
- API + frontend em mesmo repo
- Time pequeno (até 5 devs) — facilita compartilhamento
- Necessidade de tipos/contratos compartilhados

## Quando NÃO usar monorepo

- Backend puro sem frontend
- Web puro sem backend (estático)
- Times grandes em repos separados
- Setar `monorepo: false` em `specs/project.yaml`

## Convenções por app

### apps/api
- Stack default: FastAPI + Python 3.11+
- Estrutura: `src/{routers,services,models,schemas,utils}`
- Testes: `tests/{unit,integration,e2e}`
- Migrations: `migrations/versions/`

### apps/web
- Stack default: Angular 19 (admin) ou Next.js (público)
- Estrutura: `src/app/{features,shared,core}` (Angular) ou `app/` (Next)
- Tokens: importam de `packages/design-tokens` ou `docs/identidade-visual/tokens.json`

### apps/mobile
- Stack default: Angular + Ionic + Capacitor
- Estrutura: similar a apps/web mas com `capacitor.config.ts`
- Build nativo: `npx cap sync && npx cap build ios|android`

## Configuração de bootstrap

O `/gsd-bootstrap` lê `specs/project.yaml > project.monorepo` e:

- Se `true`: cria estrutura `apps/{api,web,mobile}` vazia com `.gitkeep`
- Se `false`: cria estrutura flat (raiz do repo é a app)

Para personalizar quais apps criar, editar `project.apps[]` em `specs/project.yaml`.

## Comando para validar estrutura

```bash
node .claude/get-shit-done/bin/gsd-tools.cjs verify monorepo-structure
```

Retorna lista de apps esperadas vs apps presentes, e flagra desvios.
