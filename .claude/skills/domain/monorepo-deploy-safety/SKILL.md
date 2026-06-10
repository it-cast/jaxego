# Skill: monorepo-deploy-safety

> Deploy seguro e confiável de monorepo poliglota (FastAPI/Python + Angular + Capacitor) em VPS. Estratégia padrão: **symlink atomic deploy**. Blue-green documentado como upgrade futuro condicional.
> Categoria: `domain` · 2026-05-15

## Propósito

Garantir deploy atômico, rollback instantâneo e ordem correta num monorepo de 3 diretórios poliglotas (`backend/` + `frontend/` + `mobile/`). Foco em VPS (não cloud premium), onde você controla o servidor.

**Esta skill NÃO recomenda Turborepo nem Nx para monorepo de 3 dirs poliglotas.** Veja seção "Quando usar orquestrador de monorepo" no fim.

## Quando usar (triggers)

- Planejar a phase de release / deploy
- Definir estrutura de deploy de um monorepo
- Configurar CI/CD para múltiplos apps
- Decidir entre blue-green vs symlink vs container swap
- Escrever script de deploy
- Definir ordem de deploy quando há migrations

---

## 1. Decisão de estratégia — symlink atomic (padrão)

### Por que symlink, não blue-green

| Critério | Symlink atomic | Blue-green |
|----------|----------------|------------|
| Custo de infra | Zero (1 servidor) | 2x recursos (2 ambientes vivos) |
| Downtime | ~1s (graceful reload) | Zero |
| Rollback | Instantâneo (re-aponta symlink) | Instantâneo (vira LB) |
| Complexidade DB | Baixa | Alta (migrations backward-compat obrigatórias) |
| Quando vale | VPS, B2B estágio inicial/médio, tráfego moderado | SLA contratual, tráfego alto, downtime custa dinheiro |

**Regra:** comece com symlink. Promova para blue-green SÓ quando um destes for verdade:
- SLA contratual de uptime (ex: 99.9% com penalidade)
- 1s de downtime custa dinheiro mensurável (e-commerce alto volume)
- Deploys múltiplos por dia com time grande
- Tráfego onde reload de Uvicorn/Gunicorn é perceptível (>1000 req/s sustentado)

Promoção para blue-green deve virar ADR formal em `docs/adrs/`, não decisão silenciosa.

### Estrutura de diretórios (symlink atomic)

```
/opt/{projeto}/
├── releases/
│   ├── 2026-05-15-143012/        # release por timestamp ou commit SHA
│   │   ├── backend/
│   │   ├── frontend-dist/        # build do Angular já compilado
│   │   └── RELEASE-INFO.json     # commit, data, quem fez deploy
│   ├── 2026-05-15-160045/
│   └── 2026-05-16-091533/
├── shared/                       # NUNCA dentro de release — persiste entre deploys
│   ├── .env                      # secrets e config
│   ├── logs/
│   ├── uploads/                  # arquivos de usuário
│   └── venv/                     # opcional: venv compartilhado se deps estáveis
├── current → releases/2026-05-16-091533/   # SYMLINK — troca atômica
└── deploy.lock                   # previne deploy concorrente
```

---

## 2. Invariantes que symlink impõe ao código (DESDE A PHASE 1)

**Crítico:** estas invariantes afetam a primeira phase, não a phase de release. Registrar como ADR no bootstrap. Se descobertas só no deploy, geram retrabalho (ver retros Rota Certa: alembic env.py assumiu path errado desde Phase 1, penou até Phase 4).

### Invariante 1: Sem paths absolutos hardcoded

```python
# ❌ ERRADO — quebra quando symlink troca
UPLOAD_DIR = "/opt/projeto/releases/2026-05-15-143012/uploads"

# ✅ CERTO — relativo ao shared/, fora da release
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/opt/projeto/shared/uploads")
```

### Invariante 2: Config e secrets em shared/, não na release

```python
# .env vive em /opt/projeto/shared/.env
# Cada release tem symlink: release/backend/.env → ../../../shared/.env
# Deploy NÃO sobrescreve .env
```

### Invariante 3: Logs e uploads em shared/

```python
# Logs vão para /opt/projeto/shared/logs/
# Uploads vão para /opt/projeto/shared/uploads/
# Senão você perde dados de usuário a cada deploy
```

### Invariante 4: App lê seu próprio path via current/

```python
# App não deve assumir que está em path fixo
# Usar: Path(__file__).resolve() para descobrir onde está
# Ou variável APP_ROOT injetada pelo systemd/supervisor apontando para current/
```

### Invariante 5: Migrations são forward-only e idempotentes

```python
# Migration nunca assume estado anterior específico
# alembic upgrade head deve ser seguro rodar 2x (idempotente)
# Nunca DROP COLUMN na mesma migration que adiciona substituta (quebra rollback)
```

---

## 3. Ordem de deploy no monorepo poliglota

**A ordem importa.** Deploy fora de ordem = janela de inconsistência ou downtime.

```
1. Pre-flight check
   - env-smoke-check passou?
   - secrets existem em shared/.env?
   - build local OK?

2. Subir nova release para releases/{timestamp}/
   - rsync backend/ (sem .env, sem __pycache__)
   - copiar frontend-dist/ (build do Angular já feito no CI)
   - escrever RELEASE-INFO.json

3. Migrations ANTES do switch (forward-compatible)
   - cd releases/{timestamp}/backend
   - alembic upgrade head
   - SE FALHAR: abortar, NÃO trocar symlink, release antiga continua servindo

4. Trocar symlink atomicamente
   - ln -sfn releases/{timestamp} current.tmp && mv -T current.tmp current
   - (mv -T de symlink é atômico no Linux)

5. Graceful reload do backend
   - systemctl reload {projeto}-api  (Gunicorn HUP / Uvicorn workers)
   - OU: supervisorctl signal HUP {projeto}-api

6. Frontend: já está em current/frontend-dist/, Nginx serve de lá
   - nginx -s reload (re-lê symlink)

7. Health check pós-deploy
   - curl -f http://localhost:8000/health (backend)
   - curl -f http://localhost/ (frontend via nginx)
   - SE FALHAR: rollback automático (passo 8)

8. Rollback (se health check falhar)
   - ln -sfn releases/{release_anterior} current.tmp && mv -T current.tmp current
   - systemctl reload {projeto}-api
   - alembic downgrade (SE a migration era reversível — senão alertar humano)

9. Cleanup
   - manter últimas 5 releases, rm -rf nas mais antigas
   - liberar deploy.lock
```

### Por que migrations ANTES do switch

Se você troca o symlink primeiro e migra depois, há uma janela onde o código novo roda contra schema antigo → erro 500. Migrar antes garante que quando o código novo assume, o schema já o suporta.

**Exceção (migrations destrutivas):** se a migration remove coluna que o código antigo ainda usa, você precisa de **expand-contract**:
- Deploy N: adiciona coluna nova, código usa as duas (expand)
- Deploy N+1: remove coluna antiga depois que nenhum código usa (contract)

Isso é a única disciplina extra que symlink exige, e só para mudanças destrutivas.

---

## 4. Mobile (Capacitor) — fora do ciclo de symlink

Mobile não faz deploy por symlink. O ciclo é diferente:

```
- Backend/frontend: symlink atomic na VPS (esta skill)
- Mobile: build via CI (Xcode/Gradle) → store submission (TestFlight/Play Console)
```

Mobile consome a API via URL fixa. Quando você faz deploy atomic do backend, o app mobile não percebe (mesma URL, novo código atrás). A única regra: **API deve ser backward-compatible com versões do app em produção** (usuário pode estar com app antigo). Versionar API (`/api/v1/`, `/api/v2/`) quando breaking change.

---

## 5. Template de script

Ver `bin/deploy-atomic.sh` no framework — template cross-platform (bash) que implementa os passos 2-9. Adaptar paths e service names ao projeto.

---

## 5B. Variante Docker + registry (v0.9.4)

**Quando usar esta variante em vez do symlink físico:** quando você quer isolamento por container (cada app empacotado com suas deps), facilidade de migrar de servidor (servidor novo só precisa de Docker), e rollback por tag de imagem. É a escolha recomendada para stack poliglota (FastAPI + Angular + Capacitor).

### Princípio central: imagem descartável, dados sagrados

A separação mais importante de entender:

| | Imagem / Container | Dados |
|---|---|---|
| Natureza | Descartável | Sagrado |
| Onde mora | Registry (GHCR) → recriado a cada deploy | Volume / banco nativo, no disco, fora do deploy |
| Deploy toca? | Sim — troca a cada release | **Nunca** |
| Se destruir? | Recria do registry em segundos | Perda irreversível (por isso backup) |

**Trocar a imagem do app é fisicamente incapaz de tocar o banco.** São serviços separados com persistências separadas.

### Arquitetura recomendada (decidida em campo)

```
┌─────────────────────────────────────────────┐
│ VPS                                          │
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │ container api│  │ container web│  ← Docker (GHCR)
│  │ (descartável)│  │ (descartável)│         │
│  └──────┬───────┘  └──────────────┘         │
│         │ conecta via DATABASE_URL          │
│         ▼                                    │
│  ┌──────────────────────┐                   │
│  │ MySQL NATIVO          │  ← FORA do Docker │
│  │ /var/lib/mysql        │     systemd       │
│  │ (sagrado, visível)    │                   │
│  └──────────┬───────────┘                    │
│             │ mysqldump --single-transaction │
│             ▼                                 │
└─────────────┼─────────────────────────────────┘
              ▼
        Backblaze B2 (dump diário 30d + binlog PITR)
```

**Decisões registradas:**
- **App em Docker**, imagens no GHCR (`ghcr.io/usuario/projeto-{api,web}:TAG`)
- **MySQL nativo na VPS, fora do Docker** — dados em `/var/lib/mysql`, visível e familiar. Banco nunca entra no `docker-compose`.
- **Tag imutável** (SHA do commit ou timestamp), nunca `latest` em produção
- **Backup pré-migration obrigatório** pro B2 antes de qualquer migration
- **Rollback por tag** — imagem anterior já está no registry

### Três níveis de proteção de dados (escolha por projeto)

| Nível | Setup | RPO | Quando usar |
|-------|-------|-----|-------------|
| 1.5 — MySQL nativo VPS + backup B2 | Baixo | minutos (com binlog) | Padrão. Projetos em estágio inicial/médio. Migração de servidor rara. |
| 2 — MySQL gerenciado separado | Médio + mensalidade | segundos (PITR automático) | Projetos com dados de cliente críticos, alta disponibilidade |
| 3 — Backup B2 (dump + binlog) | Baixo | minutos | **SEMPRE, em qualquer nível** — rede de segurança universal |

**Recomendação de campo:** Nível 1.5 + 3 como padrão. Promover projeto específico para Nível 2 quando dados de cliente justificarem a mensalidade. Migração de servidor no Nível 1.5 = operação manual planejada (madrugada/fim de semana, dump consistente) — rara o suficiente para não justificar gerenciado.

### Recuperação de desastre (RPO real, honesto)

- **Só dump diário:** perde até 24h (último dump)
- **Dump diário + binlog arquivado (PITR):** perde minutos (dump base + replay binlog até o instante) ← **recomendado**
- **Replicação síncrona:** zero perda, mas caro e complexo — over-engineering para estágio inicial/médio

"Recuperação ao segundo" literal exige replicação síncrona. Dump + binlog entrega "perda de poucos minutos", que é indistinguível na prática para a maioria dos casos B2B e custa uma fração.

### Fluxo de deploy Docker

```
CI (GitHub Actions):
  1. testes + lint (falhou → para, nada vai pro registry)
  2. docker build api/web → tag :SHA + :timestamp
  3. docker login ghcr.io (GITHUB_TOKEN automático)
  4. docker push pro GHCR

VPS (bin/deploy-docker.sh):
  1. pre-flight (.env existe, compose existe, login registry)
  2. docker compose pull (baixa tag nova)
  3. SE migrations pendentes:
       a. backup-mysql-b2.sh pre-migration (OBRIGATÓRIO — aborta se falhar)
       b. alembic upgrade head (via container que conecta no MySQL nativo)
       c. se falhar → aborta, containers antigos seguem
  4. docker compose up -d (recria com tag nova, graceful)
  5. health check (6 tentativas, 30s)
  6. se falhar → rollback automático pra tag anterior
  7. registra tag atual + docker image prune
```

### Volumes e persistência (compose conceitual)

```yaml
# docker-compose.prod.yml
services:
  api:
    image: ghcr.io/usuario/projeto-api:${TAG}    # TAG via env
    env_file: /opt/projeto/shared/.env            # secrets FORA da imagem
    environment:
      DATABASE_URL: mysql://user:pass@host.docker.internal:3306/db  # MySQL nativo
    volumes:
      - /opt/projeto/shared/uploads:/app/uploads  # uploads persistem
      - /opt/projeto/shared/logs:/app/logs        # logs persistem
    extra_hosts:
      - "host.docker.internal:host-gateway"       # container alcança MySQL nativo
  web:
    image: ghcr.io/usuario/projeto-web:${TAG}
    ports: ["80:80", "443:443"]

# SEM serviço mysql — banco é nativo na VPS, fora do compose
```

### Migração de servidor (runbook — operação rara, manual)

```
1. Servidor novo: instalar Docker + MySQL nativo
2. Banco:
   - parar app no servidor velho (janela de manutenção)
   - dump consistente: backup-mysql-b2.sh full
   - restore no servidor novo: restore-mysql-b2.sh --date=hoje
3. App:
   - copiar /opt/projeto/shared/ (.env, uploads, logs)
   - docker compose pull (imagens vêm do GHCR — nada a copiar)
   - docker compose up -d
4. Apontar DNS pro servidor novo
5. Validar, desligar servidor velho
```

Note como o app migra trivial (só pull do GHCR). O trabalho é o banco — por isso a janela planejada. No Nível 2 (gerenciado), nem isso: o banco nem muda de lugar.

### Anti-patterns específicos de Docker

- ❌ `docker compose down -v` em produção (apaga volumes) — JAMAIS
- ❌ MySQL dentro do compose com dados em volume não-backupeado
- ❌ Tag `latest` em produção (perde rastreabilidade e rollback)
- ❌ Build na VPS (`up --build`) — lento, pode falhar em prod, sem rollback limpo
- ❌ Migration sem backup pré-migration
- ❌ Secrets dentro da imagem (use env_file de fora)
- ❌ Banco no mesmo compose do app sem entender que volume ≠ imagem

### Scripts do framework

- `bin/deploy-docker.sh` — deploy via GHCR, backup pré-migration, rollback por tag, nunca `-v`
- `bin/backup-mysql-b2.sh` — dump diário + binlog PITR + pré-migration + prune (retenção 30d)
- `bin/restore-mysql-b2.sh` — restore de dump ou PITR até instante exato

---

## 6. Quando usar orquestrador de monorepo (Turborepo/Nx/Moon)

**Decisão honesta calibrada para stack FastAPI + Angular + Capacitor:**

| Cenário | Recomendação |
|---------|--------------|
| 3 dirs poliglotas (backend + frontend + mobile) | **Nenhum.** Makefile + scripts bastam. Angular já tem cache nativo. |
| 4-6 pacotes TS compartilhados (design system como pacote, libs) | **Nx** (Angular-first, plugin Python). NÃO Turborepo. |
| 7+ pacotes, time grande, CI lento | **Nx** com Nx Cloud, OU Moon se quiser cache poliglota real |
| Monorepo all-Next.js/React | Turborepo faz sentido (mas não é seu caso) |

**Por que NÃO Turborepo na sua stack:**
- Turborepo é Next.js/React-first; você usa Angular
- Cache do Turborepo não entende uv/poetry (Python fica de fora)
- Cobriria só Angular, que já tem cache do `@angular/build`
- Remote cache é Vercel-centric; você usa VPS

**Por que Nx SE for crescer pacotes TS:**
- Nx é Angular-first (co-desenhado com Angular CLI)
- Tem plugin Python (`@nxlv/python`)
- Generators e affected commands fazem sentido com 4+ pacotes

**Regra de ouro:** orquestrador de monorepo resolve "build lento por rebuildar tudo". Se seu build não está lento, não há problema para resolver. Não adote ferramenta por moda.

---

## 7. Anti-patterns

- ❌ Deploy que sobrescreve a pasta atual (`git pull` em prod) — sem rollback, downtime durante o pull
- ❌ Secrets dentro da release (perde a cada deploy)
- ❌ Migration destrutiva sem expand-contract (quebra rollback)
- ❌ Trocar symlink antes de migrar (janela de erro 500)
- ❌ Sem health check pós-deploy (descobre que quebrou pelo usuário)
- ❌ Sem deploy.lock (dois deploys concorrentes corrompem releases/)
- ❌ Blue-green "porque é mais profissional" sem ter o problema que blue-green resolve
- ❌ Turborepo/Nx em monorepo de 3 dirs poliglotas (over-engineering)

---

## 8. Checklist de release (resumo)

- [ ] env-smoke-check passou
- [ ] secrets em shared/.env confirmados
- [ ] build do frontend feito no CI
- [ ] migrations são forward-compatible (ou expand-contract se destrutiva)
- [ ] script de deploy tem rollback automático em health check fail
- [ ] deploy.lock implementado
- [ ] retenção de releases configurada (manter últimas 5)
- [ ] health check endpoints existem (/health no backend)
- [ ] systemd/supervisor configurado para graceful reload
- [ ] decisão symlink vs blue-green registrada em ADR

---

## Conexão com outras skills

- **Use junto com:** `domain/docker-production-ready` (se containerizado), `quality/observability-production` (health checks + alertas pós-deploy)
- **Validada por:** `gsd-release-auditor` agent (checklist de release na phase de deploy)
- **Antes de:** qualquer phase com `is_pre_release: true` no ROADMAP
