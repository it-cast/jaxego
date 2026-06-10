# stacks/

**Tecnologias do projeto.** O que vai ser usado (ou opções em consideração).

## O que jogar aqui

- Stack frontend (framework, UI lib, state management)
- Stack backend (linguagem, framework, ORM)
- Banco de dados
- Infra (cloud, container, CI/CD)
- Serviços terceiros (auth, pagamento, email, storage)
- Mobile (se houver)
- Restrições técnicas (versões mínimas, libs proibidas, etc.)

## Formatos aceitos

`.md`, `.yaml`, `.json`, `.txt`

## Exemplo de stack completa

```yaml
# stacks/stack.yaml
frontend:
  framework: Angular 19
  ui: Ionic 8
  state: Signals (sem NgRx)
  build: esbuild
  styling: SCSS + design tokens

mobile:
  capacitor: 8.x
  ios: 16+
  android: 13+ (API 33)

backend:
  language: Python 3.13
  framework: FastAPI
  orm: SQLAlchemy 2 (async)
  migrations: Alembic

database:
  primary: MySQL 8
  cache: Redis 7
  queue: Arq (Redis-backed)

infra:
  hosting: VPS (Hetzner)
  containers: Docker Compose
  ci: GitHub Actions
  monitoring: Sentry + Prometheus

integrations:
  payment: Pagar.me + Safe2Pay (split)
  email: Postmark
  kyc: Idwall
  storage: Backblaze B2
  sms: Twilio Programmable Messaging

restricoes:
  - "MySQL obrigatório (cliente exige)"
  - "Sem NgRx"
  - "Locale pt-BR em tudo"
```

## Stack mínima (se você ainda não decidiu tudo)

```md
# stacks/incomplete.md

Frontend: ainda em discussão (Angular ou React?)
Backend: provavelmente FastAPI
Banco: MySQL (cliente exige)
Hosting: VPS, não cloud premium
```

Claude vai perguntar o que falta no `/gsd:ingest`.

## O que NÃO jogar aqui

- Documentação de APIs externas que você VAI integrar (vai em `docs-externos/`)
- Decisões já tomadas que precisam virar ADR (vai em `decisoes-existentes/`)
