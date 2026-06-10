# Jaxego API

Backend FastAPI do Jaxegô (monorepo — `apps/api/`).

Stack: Python 3.13 (uv) · FastAPI 0.115 · SQLAlchemy 2.x async (aiomysql) ·
Alembic · MySQL 8.0 (utf8mb4) · Redis · arq · structlog · Sentry (condicional).

## Desenvolvimento local

```bash
# A partir de apps/api/
uv sync                       # instala deps + Python 3.13
uv run ruff check .           # lint
uv run ruff format --check .  # format check
uv run basedpyright           # typecheck
uv run pytest                 # testes
```

## Stack completa via Docker Compose

```bash
# A partir da raiz do repositório
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d
curl -f localhost:8000/health   # 200 com db: ok, redis: ok
```

## Migrations (Alembic)

```bash
# A partir de apps/api/ (DATABASE_URL apontando para o MySQL)
uv run alembic upgrade head
uv run alembic downgrade base
```

## Convenções

- Timestamps **UTC** sempre; conversão só na borda (guard de naive datetime em
  `tools/check_naive_datetime.py`).
- Logs JSON estruturados em stdout com `request_id`; sem PII.
- Endpoints de domínio sob `/v1`; o health probe fica na raiz em `/health`.
