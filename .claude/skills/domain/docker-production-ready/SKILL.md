# Skill: docker-production-ready

> Docker + Docker Compose + Nginx production-ready para o {PROJETO} em VPS Hostinger Ubuntu: multi-stage builds, non-root, healthcheck, secrets, logging, limits.
> Categoria: `domain` · 2026-04-18

## Propósito

Deployar o {PROJETO} em VPS Hostinger de forma segura, observável e resiliente. Foco em production — não é tutorial de Docker, é o que usar quando vai pro ar.

## Quando usar (triggers)

- Criar ou modificar `Dockerfile` de qualquer app (`api`, `admin`, `mobile`, `nginx`)
- Modificar `docker-compose.yml` ou `docker-compose.prod.yml`
- Configurar Nginx reverse proxy
- Deployar na VPS pela primeira vez
- Adicionar novo serviço ao compose
- Troubleshoot de container em produção

---

## 1. Multi-stage Dockerfile (API)

```dockerfile
# apps/api/Dockerfile
# --- Stage 1: Build ---
FROM python:3.12-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Instalar uv (package manager)
RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# --- Stage 2: Runtime ---
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Criar usuário não-root
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

# Copiar venv do builder
COPY --from=builder --chown=app:app /build/.venv /app/.venv

# Copiar código
COPY --chown=app:app apps/api /app

USER app

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Pontos críticos:**
- Multi-stage reduz imagem de ~800 MB → ~200 MB
- `USER app` — nunca rodar como root
- `HEALTHCHECK` obrigatório — compose/k8s detecta container morto
- `--workers 4` em produção (1 worker em dev)

---

## 2. Multi-stage Dockerfile (Admin Angular)

```dockerfile
# apps/admin/Dockerfile
# --- Stage 1: Build ---
FROM node:20-alpine AS builder

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci --prefer-offline --no-audit

COPY apps/admin /build/apps/admin
COPY packages /build/packages
COPY tsconfig.base.json nx.json ./

RUN npx nx build admin --configuration=production

# --- Stage 2: Runtime (Nginx) ---
FROM nginx:1.27-alpine

# Remover config default
RUN rm /etc/nginx/conf.d/default.conf

# Copiar build
COPY --from=builder /build/dist/apps/admin /usr/share/nginx/html

# Copiar config custom
COPY infra/nginx/admin.conf /etc/nginx/conf.d/admin.conf

# Non-root
RUN addgroup -S app && adduser -S app -G app \
    && chown -R app:app /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid && chown app:app /var/run/nginx.pid

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

---

## 3. docker-compose.prod.yml

```yaml
services:
  api:
    image: app/api:${APP_VERSION:-latest}
    restart: unless-stopped
    environment:
      - DATABASE_URL=mysql+aiomysql://app:${MYSQL_PASSWORD}@mysql:3306/app
      - REDIS_URL=redis://redis:6379/0
      - ENCRYPTION_KEY_FILE=/run/secrets/encryption_key
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
      - ENV=production
      - LOG_LEVEL=info
    secrets:
      - encryption_key
      - jwt_secret
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - backend
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: json-file
      options:
        max-size: "20m"
        max-file: "5"

  admin:
    image: app/admin:${APP_VERSION:-latest}
    restart: unless-stopped
    networks:
      - frontend
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  mysql:
    image: mysql:8.0
    restart: unless-stopped
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --max_connections=200
      --innodb_buffer_pool_size=512M
    environment:
      - MYSQL_ROOT_PASSWORD_FILE=/run/secrets/mysql_root_password
      - MYSQL_DATABASE=app
      - MYSQL_USER=app
      - MYSQL_PASSWORD_FILE=/run/secrets/mysql_password
    secrets:
      - mysql_root_password
      - mysql_password
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - backend
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p$$(cat /run/secrets/mysql_root_password)"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/gateway.conf:/etc/nginx/conf.d/default.conf:ro
      - ./infra/nginx/ssl:/etc/nginx/ssl:ro
      - certbot_webroot:/var/www/certbot:ro
    depends_on:
      - api
      - admin
    networks:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s

volumes:
  mysql_data:
  redis_data:
  certbot_webroot:

networks:
  frontend:
  backend:
    internal: true  # Sem acesso externo direto

secrets:
  encryption_key:
    file: ./secrets/encryption_key.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  mysql_root_password:
    file: ./secrets/mysql_root_password.txt
  mysql_password:
    file: ./secrets/mysql_password.txt
```

---

## 4. Nginx reverse proxy (gateway.conf)

```nginx
# infra/nginx/gateway.conf
upstream api_backend {
    server api:8000;
    keepalive 32;
}

upstream admin_backend {
    server admin:8080;
    keepalive 16;
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name app.com.br admin.app.com.br;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS — Admin
server {
    listen 443 ssl http2;
    server_name admin.app.com.br;

    ssl_certificate /etc/nginx/ssl/live/admin.app.com.br/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/admin.app.com.br/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.app.com.br wss://api.app.com.br" always;

    client_max_body_size 10M;

    location / {
        proxy_pass http://admin_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTPS — API
server {
    listen 443 ssl http2;
    server_name api.app.com.br;

    ssl_certificate /etc/nginx/ssl/live/api.app.com.br/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/api.app.com.br/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 10M;

    # CORS é gerido pelo FastAPI (não duplicar aqui)

    location /ws/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # 24h para WebSocket longo
    }

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## 5. Secrets (não usar `.env` em produção)

```bash
# Na VPS, primeira vez:
sudo mkdir -p /opt/app/secrets
cd /opt/app/secrets

# Gerar secrets fortes
openssl rand -base64 32 > encryption_key.txt
openssl rand -base64 48 > jwt_secret.txt
openssl rand -base64 24 > mysql_root_password.txt
openssl rand -base64 24 > mysql_password.txt

# Permissões restritas
sudo chmod 400 *.txt
sudo chown root:docker *.txt  # ou usuário que roda docker
```

**Nunca** commitar `secrets/` no git. Adicionar ao `.gitignore`.

---

## 6. Observabilidade mínima

```python
# apps/api/app/main.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.JSONRenderer(),
    ],
)

# Logar em JSON → fácil de parsear
logger.info('payment_created', payment_id=str(p.id), amount=float(p.total))
```

---

## 7. Deploy script (Hostinger VPS)

```bash
#!/bin/bash
# scripts/deploy.sh
set -euo pipefail

VERSION="${1:-latest}"
cd /opt/app

# 1. Pull imagens novas
docker compose -f docker-compose.prod.yml pull

# 2. Aplicar migrations (sem downtime no app novo)
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# 3. Restart com rolling update
APP_VERSION=$VERSION docker compose -f docker-compose.prod.yml up -d --no-deps --wait api admin

# 4. Verificar saúde
sleep 5
curl -sf https://api.app.com.br/health || { echo "API unhealthy"; exit 1; }

echo "Deploy $VERSION OK"
```

---

## Anti-patterns

1. ❌ **`USER root`** no runtime — exec em container = acesso root no host via escape
2. ❌ **Sem `HEALTHCHECK`** — container zombie, compose acha que está bom
3. ❌ **Secrets em `environment:`** do compose — aparece em `docker inspect`
4. ❌ **`latest` tag em produção** — rollback impossível; use versão SemVer
5. ❌ **Sem `deploy.resources.limits`** — container OOM derruba o host
6. ❌ **Logs sem rotation** (`max-size`) — disco enche em semanas
7. ❌ **Single-stage Dockerfile** — imagem com 800 MB, toolchain exposta
8. ❌ **`COPY . .`** sem `.dockerignore` — vai `node_modules`, `.git`, secrets
9. ❌ **Migration no CMD do container** — race condition com múltiplos workers
10. ❌ **MySQL sem `innodb_buffer_pool_size`** configurado — performance ruim

---

## Checklist de review

- [ ] Multi-stage build (builder + runtime separados)
- [ ] `USER` não-root em runtime
- [ ] `HEALTHCHECK` definido em todo serviço
- [ ] Recursos limitados (`deploy.resources.limits`)
- [ ] Logs com rotation (`max-size`, `max-file`)
- [ ] Secrets via `secrets:`, não `environment:`
- [ ] Rede `backend` marcada `internal: true`
- [ ] Imagens tagueadas com versão (não `latest`)
- [ ] Nginx com HSTS, CSP, X-Frame-Options
- [ ] Nginx `client_max_body_size` coerente com limite da app
- [ ] WebSocket com timeout 86400 no proxy
- [ ] `.dockerignore` presente
- [ ] Volume mysql fora do container
- [ ] Certbot configurado para renovação automática

<!-- Skill aplicada: Dockerfile, docker-compose.*.yml, infra/nginx/*, scripts/deploy.sh -->
