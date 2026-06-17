# ADR-014: Apps fisicamente separados + lib compartilhada (monorepo npm workspaces)

- **Status:** accepted
- **Data:** 2026-06-17
- **Autor:** time Jaxegô
- **Deciders:** dono do produto (decisão explícita nesta sessão)

## Contexto

A v1.0 nasceu com **um único workspace Angular** em `apps/web`, onde as três
superfícies (admin, loja, entregador) eram apenas *build targets* (`main.*.ts` +
route maps) compartilhando o mesmo `src/`. Backend já vivia em `apps/api` (Python).

O dono pediu explicitamente a estrutura **backend `/apps/api`, admin/loja `/apps/web`
(Angular), entregador `/apps/app` (Ionic)** — separação **física** por pasta, não só
lógica. A primeira entrega não fez isso (decisão indevida do executor, registrada no
postmortem). O design system `jx-*` e o `core/auth` são fortemente compartilhados entre
web e app (o app do entregador consome ~30 componentes/utils da camada compartilhada),
então a separação só é sustentável sem duplicação se o código comum virar uma lib.

## Decisão

Adotar **monorepo npm workspaces** com três apps físicos + uma lib compartilhada:

- `apps/api` — backend Python (inalterado).
- `apps/web` — Angular: superfícies **admin + loja** (+ auth/tracking herdados da lib).
- `apps/app` — Ionic/Capacitor: app do **entregador** (mobile).
- `packages/shared` — design system `jx-*`, `core/auth`, tokens, `app.config`/`app.component`
  e as features cross-app (login, tracking público). Consumida via aliases
  `@jaxego/shared/*` e `@jaxego/core/*`.

`node_modules` é **hoisted na raiz** (workspaces), o que permite à lib resolver suas
dependências (`@angular/*`, `rxjs`, `@ionic/angular`, etc.) sem duplicar pacotes.

Não altera ADR-002 (stack backend) nem ADR-003 (Angular 19 + Ionic + Capacitor) —
apenas a **topologia de pastas e build**.

## Alternativas consideradas

### Opção A — manter tudo em `apps/web` (build targets)
- Prós: zero migração; um só `node_modules`.
- Contras: não é o que o dono pediu; entregador e web acoplados no mesmo `src/`;
  build/test/deploy do mobile misturado com o web.

### Opção B — duplicar o design system em `apps/app`
- Prós: estritamente 3 pastas, sem `packages/`.
- Contras: design system em dois lugares → **drift** garantido; um ajuste de token/
  componente precisaria ser feito 2×.

### Opção C — `apps/app` referencia `apps/web/src` via tsconfig paths
- Prós: 3 pastas, sem duplicar.
- Contras: app acoplado aos internos do web; não builda isolado; frágil.

### Opção D (escolhida) — 3 apps + `packages/shared` (npm workspaces)
- Prós: separação física pedida; **uma** fonte de verdade do design system; cada app
  builda/testa/deploya isolado; `node_modules` único (hoisted) resolve deps da lib.
- Contras: adiciona a pasta `packages/` e exige `npm ci` na raiz (não por-app).
- **Escolhida porque:** é a única que entrega a separação pedida **sem** drift do design
  system, e é o padrão de monorepo consolidado (estilo Nx) para web + mobile compartilhando UI.

## Consequências

### Positivas
- Estrutura conforme pedido; mobile isolado do web; lib única para o design system.
- Specs da lib continuam rodando (incluídos no karma do `web`).

### Negativas
- Instalação passa a ser **na raiz** (`npm ci` em `.`), não em `apps/web`.
- CI/CD precisou de jobs separados (`web`, `app`) e o APK passou a sair de `apps/app`.

### Neutras / requer atenção
- Imports cross-app são proibidos: tudo que web e app compartilham **deve** estar em
  `packages/shared` (ex.: `delivery.models`, `br-format`, login, tracking foram movidos).
  Um import relativo de `apps/app` para `apps/web` (ou vice-versa) deve falhar em review.

## Implementação

- [x] Lib `packages/shared` criada; `core/`, `shared/`, `styles/`, `app/`, features
      cross-app e o script de tokens movidos para lá.
- [x] `apps/web` reduzido a admin+loja; `apps/app` criado com o entregador.
- [x] npm workspaces na raiz; aliases `@jaxego/shared/*` e `@jaxego/core/*`.
- [x] CI: `npm ci` na raiz, jobs `web` e `app`, zero-hex cobrindo lib+apps, APK de `apps/app`.
- [x] Verde local: 4 builds (web/loja/admin/app) + lint (web/app) + testes (web 54, app 31).
- [ ] Migração de dados: não se aplica (mudança só de topologia frontend).
- [ ] Breaking change p/ deploy do frontend: hosting passa a publicar `apps/web/dist/*`
      e `apps/app/dist/app` (APK). Deploy do backend (apps/api) inalterado.

## Referências

- Pedido do dono (sessão 2026-06-17) e `feedback/POSTMORTEM-jaxego-v1.md` (separação física não feita na v1.0).
- Relacionada: ADR-003 (stack Angular/Ionic/Capacitor) — esta ADR só muda a topologia.
