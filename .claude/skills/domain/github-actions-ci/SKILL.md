# Skill: github-actions-ci

> CI/CD com GitHub Actions para a stack do framework: pipeline canônico FastAPI + Angular/Ionic, cache certo, secrets, build de imagem GHCR, deploy para VPS, mobile build, proteção contra os erros de campo já vividos.
> Categoria: `domain` · v0.9.5 · 2026-06-09

## Propósito

O framework tinha `deploy-atomic.sh`, `deploy-docker.sh` e a skill de Docker — mas nenhuma skill dizendo **como o CI que chama esses scripts deve ser construído**. Resultado de campo: workflows YAML escritos ad-hoc por phase, cada um diferente. Esta skill fecha o ciclo código → CI → deploy.

## Quando usar (triggers)

- Phase que cria/altera `.github/workflows/`
- Setup de CI em projeto novo (bootstrap)
- Build mobile (Capacitor), publicação de imagem GHCR, deploy VPS

---

## 1. Pipeline canônico (monorepo back+front)

```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true        # PR atualizado mata run velho — economiza minutos

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env: { MYSQL_ROOT_PASSWORD: test, MYSQL_DATABASE: app_test }
        ports: ["3306:3306"]
        options: --health-cmd "mysqladmin ping" --health-interval 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --frozen          # --frozen: lockfile divergente FALHA, não resolve silencioso
      - run: uv run alembic upgrade head
        env: { DATABASE_URL: mysql+aiomysql://root:test@127.0.0.1/app_test }
      - run: uv run pytest -q
      - run: uv run ruff check .

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm, cache-dependency-path: frontend/package-lock.json }
      - run: npm ci                    # ci, NUNCA install — lockfile é lei
        working-directory: frontend
      - run: npm run lint && npm run test -- --watch=false --browsers=ChromeHeadless
        working-directory: frontend
      - run: npm run build -- --configuration=production
        working-directory: frontend
```

Regras:

- **`npm ci` e `uv sync --frozen`** — CI nunca resolve dependências; divergência de lockfile é erro, não warning (bug de campo: conflito arq/redis passando silencioso).
- **MySQL real como service** — testes de integração contra MySQL 8 de verdade, não SQLite "parecido" (diferenças de collation/FULLTEXT só aparecem no banco real).
- **Migrations rodam no CI** — `alembic upgrade head` em DB limpo a cada run pega migration quebrada/irreversível antes de produção.
- **`concurrency` + `cancel-in-progress`** — sem isso, 5 pushes = 5 runs enfileirados.

## 2. Build de imagem → GHCR (alinhado a v0.9.4 Docker)

```yaml
# disparo: tag v*
- uses: docker/login-action@v3
  with: { registry: ghcr.io, username: ${{ github.actor }}, password: ${{ secrets.GITHUB_TOKEN }} }
- uses: docker/build-push-action@v6
  with:
    push: true
    tags: |
      ghcr.io/${{ github.repository }}/api:${{ github.ref_name }}
      ghcr.io/${{ github.repository }}/api:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

- Tag imutável por release (`v1.2.3`) é o que vai para o deploy; `latest` é conveniência, nunca referência de deploy.
- `cache-from/to: gha` corta build de 8min para ~2min.

## 3. Deploy para VPS

```yaml
deploy:
  needs: [backend, frontend]
  if: startsWith(github.ref, 'refs/tags/v')
  environment: production            # exige aprovação manual se configurado no repo
  steps:
    - uses: appleboy/ssh-action@v1
      with:
        host: ${{ secrets.VPS_HOST }}
        username: deploy
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /srv/app && bash bin/deploy-docker.sh ${{ github.ref_name }}
```

- O CI **chama** `bin/deploy-docker.sh` / `deploy-atomic.sh` — a lógica de deploy mora no repo, versionada, testável local. CI é só o gatilho. (Inverter isso = lógica de deploy presa em YAML não-testável.)
- O script já aborta se backup pré-migração falhar (inegociável v0.9.4) — CI herda isso de graça.
- Usuário `deploy` dedicado na VPS, chave exclusiva do Actions, sem sudo amplo.

## 4. Secrets — regras

- Tudo sensível em `Settings → Secrets`; **nada** de env hardcoded em YAML (nem "temporário")
- `pull_request` de fork não recebe secrets — jobs de deploy nunca em `pull_request`
- Logar valor de secret = vazamento (Actions mascara, mas não em base64/transformações). Proibido `echo $SECRET` até para debug.

## 5. Mobile (Capacitor) — o mínimo honesto

- CI valida `npx cap sync` + build Android debug em PR que toca o app (pega plugin quebrado cedo)
- Build assinado de release (keystore/certificados iOS): **fora do CI público** por padrão — secrets de assinatura em CI só com decisão registrada em ADR (risco vs conveniência)
- Versionar `versionCode`/`build number` automaticamente a partir da tag
- Actions de terceiros para mobile: **pin por SHA, não por @v3 flutuante** — `apple-actions@v3` LOW confidence foi caso de campo (Rota Certa phase-09); tag flutuante quebra sem aviso

## 6. Higiene geral

- Pin de actions: oficiais por major (`@v4`); terceiros por SHA completo
- `timeout-minutes` em todo job (default 15) — job pendurado não queima a cota da conta
- Badge de status no README — sinal honesto de saúde do repo
- Falhou no CI e passou local? Primeiro suspeito: versão de Node/Python divergente — CI fixa versões explícitas sempre

## Checklist de review

- [ ] `npm ci` / `uv sync --frozen` (nunca install/resolve)
- [ ] Migrations rodando em DB limpo no CI
- [ ] `concurrency` configurado
- [ ] Deploy só em tag + environment protection
- [ ] Lógica de deploy em `bin/`, CI apenas invoca
- [ ] Secrets sem exposição em log/fork
- [ ] Actions de terceiros pinadas por SHA
- [ ] `timeout-minutes` em todos os jobs

## Relação com outras skills

- `domain/docker-production-ready` — a imagem que o §2 publica
- `domain/monorepo-deploy-safety` — symlink atomic / rollback que o §3 invoca
- `quality/observability-production` — verificação pós-deploy
- `owasp-security` — gestão de secrets
