# Observability em produção — structlog + Sentry + OpenTelemetry

> Skill obrigatória para qualquer endpoint, background job ou integração externa em produção.
> Endereça a lacuna do relatório 3: print()/logger.info() sem estrutura, sem correlação, sem alerting.

## Princípio central

Observability ≠ logging. Tem 3 pilares:

1. **Logs estruturados** — queryable, correlacionados por request_id
2. **Traces** — caminho completo de uma requisição atravessando serviços
3. **Metrics** — contadores, histogramas, gauges

Um bug em produção se debuga com os 3. Faltando qualquer um, você está no escuro.

## Stack recomendada

- **Logs:** `structlog` (Python) / `pino` (Node) / `slog` (Go) → Loki / CloudWatch / Datadog Logs
- **Traces:** OpenTelemetry (OTel) → Jaeger / Tempo / Datadog APM
- **Errors:** Sentry (errors + release tracking + performance)
- **Metrics:** Prometheus → Grafana
- **Uptime / synthetic:** UptimeRobot, Better Uptime, ou custom health endpoints

## Campos obrigatórios em todo log

```json
{
  "timestamp": "2026-04-22T10:32:15.123Z",
  "level": "INFO",
  "logger": "app.api.proposals",
  "request_id": "7b8c9d...",
  "user_id": "uuid-user",
  "workspace_id": "uuid-workspace",
  "endpoint": "POST /api/v1/proposals/{id}/accept",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 42,
  "message": "proposal accepted",
  "extra": { ... }
}
```

Campos extras comuns: `ip`, `user_agent`, `trace_id`, `span_id`, `feature_flag_variant`.

## Implementação Python (FastAPI + structlog)

### Middleware de request_id + timing

```python
# backend/app/middleware/request_context.py
import structlog
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Propagar para logs e traces
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            endpoint=request.url.path,
            method=request.method,
        )
        
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)
            
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.exception(
                "request_failed",
                duration_ms=duration_ms,
                exc_type=type(exc).__name__,
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()
```

### Configuração do structlog

```python
# backend/app/core/logging.py
import structlog
import logging

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.dict_tracebacks,
        filter_pii,  # custom processor — ver abaixo
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

PII_FORBIDDEN_FIELDS = {
    "cpf", "cnpj", "rg", "email", "phone", "full_name",
    "password", "password_hash", "token", "jwt", "refresh_token",
    "card_number", "cvv", "api_key",
}

def filter_pii(_, __, event_dict):
    """Remove campos PII de logs. Substitui valor por '[REDACTED]'."""
    for key in list(event_dict.keys()):
        if key.lower() in PII_FORBIDDEN_FIELDS:
            event_dict[key] = "[REDACTED]"
    return event_dict
```

### Uso em handlers

```python
from app.core.logging import structlog
logger = structlog.get_logger()

# Exemplo hipotético — domínio: gestão de pedidos
@router.post("/orders/{id}/confirm")
async def confirm_order(id: UUID, body: ConfirmOrderBody, user: CurrentUser):
    logger.info("order_confirm_started", order_id=str(id), user_id=str(user.id))
    
    order = await db.get_order(id)
    if not order:
        logger.warning("order_not_found", order_id=str(id))
        raise HTTPException(404, detail="ORDER_NOT_FOUND")
    
    if order.confirmed_at is not None:
        logger.warning("order_already_confirmed", order_id=str(id))
        raise HTTPException(409, detail="ORDER_ALREADY_CONFIRMED")
    
    # ... lógica ...
    
    logger.info("order_confirmed", order_id=str(id), payment_id=str(payment.id))
    return {"payment_id": payment.id, "status": "pending"}
```

### OpenTelemetry tracing

```python
# backend/app/core/otel.py
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def setup_otel(app, db_engine):
    resource = Resource(attributes={
        "service.name": settings.SERVICE_NAME,  # ex: "my-api", "billing-worker" — vem de specs/stack.yaml
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=db_engine)
```

### Sentry

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    release=settings.APP_VERSION,
    traces_sample_rate=0.1,  # 10% em prod, 1.0 em staging
    profiles_sample_rate=0.1,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    before_send=scrub_pii_from_sentry,  # remove campos sensíveis
)

def scrub_pii_from_sentry(event, hint):
    # Remove PII conhecido de request.data, extras, breadcrumbs
    ...
    return event
```

## Frontend observability (complemento)

### Web Vitals + erros JS

```typescript
// src/core/observability.ts
import * as Sentry from "@sentry/browser";
import { onLCP, onINP, onCLS, onTTFB } from 'web-vitals';

Sentry.init({
  dsn: env.SENTRY_DSN,
  environment: env.ENVIRONMENT,
  release: env.APP_VERSION,
  tracesSampleRate: 0.1,
  integrations: [
    new Sentry.BrowserTracing(),
    new Sentry.Replay({ maskAllText: true, blockAllMedia: true }),  // respeitar PII
  ],
  beforeSend(event) {
    // scrub PII
    return event;
  },
});

// Web vitals → analytics + Sentry
const report = (name: string, value: number) => {
  Sentry.addBreadcrumb({ category: 'web-vitals', message: name, data: { value } });
  posthog.capture('web_vital', { name, value });
};

onLCP((m) => report('LCP', m.value));
onINP((m) => report('INP', m.value));
onCLS((m) => report('CLS', m.value));
onTTFB((m) => report('TTFB', m.value));
```

## Health endpoints

Todo serviço expõe três endpoints de health:

```python
# /healthz — liveness (o processo está vivo?)
@router.get("/healthz")
def liveness():
    return {"status": "ok"}

# /readyz — readiness (consegue servir requisições?)
@router.get("/readyz")
async def readiness():
    checks = {
        "db": await db_healthcheck(),
        "redis": await redis_healthcheck(),
        "llm_api": await llm_healthcheck(),
    }
    status = 200 if all(c["ok"] for c in checks.values()) else 503
    return JSONResponse(status_code=status, content={"checks": checks})

# /metrics — Prometheus
# (exportado via prometheus_client ou opentelemetry exporter)
```

Kubernetes/Docker usa `/healthz` para restart, `/readyz` para rotear tráfego.

## Métricas chave por tipo de serviço

### API REST

- `http_requests_total{method, endpoint, status}` — counter
- `http_request_duration_seconds{method, endpoint}` — histogram
- `http_requests_in_flight` — gauge
- Error rate: `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`

### Background workers

- `jobs_processed_total{job_name, status}` — counter
- `job_duration_seconds{job_name}` — histogram
- `queue_size{queue}` — gauge

### Integrações externas

- `external_api_calls_total{service, method, status}`
- `external_api_duration_seconds{service, method}`
- Alert se error rate > 5% por 5min

## Alerting

Regras mínimas em Prometheus/Grafana:

```yaml
# Alert 1: error rate alto
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) /
    sum(rate(http_requests_total[5m])) > 0.01
  for: 2m
  annotations:
    summary: "API error rate > 1% por 2min"

# Alert 2: latência p95 alta
- alert: HighLatencyP95
  expr: |
    histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  for: 5m

# Alert 3: pod em crash loop
- alert: PodCrashLooping
  expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
```

Notificações: Slack webhook para warning, PagerDuty para critical.

## Sampling e custo

Em produção, logar tudo é caro. Estratégia:

- INFO: 100% em staging, 100% em prod (todo request)
- DEBUG: 0% em prod, 100% em dev
- Traces: 10% em prod, 100% em staging
- Profiling: 1-10% em prod

Sampleamento com contexto: amostras sempre incluem erros + lentos (não apenas aleatório).

## PII e compliance

- Lista em `specs/rules.yaml > pii_fields` é verdade. Nenhum desses campos aparece em log sem `[REDACTED]`.
- Log retention: 30 dias padrão, 90 dias para auditoria.
- Sentry configurado com `beforeSend` que filtra request body/query params sensíveis.
- Sessão de usuário em Sentry Replay: `maskAllText: true`, `blockAllMedia: true`.

## Checklist para PLAN.md

Copiar para `## Observability checklist`:

- [ ] Middleware de request_id instalado e injeta em todos os logs
- [ ] Logger estruturado com campos obrigatórios (request_id, user_id, endpoint, duration_ms, status_code)
- [ ] Zero PII em logs (filtro ativo em structlog processor ou equivalente)
- [ ] Endpoints novos logam início, warning em 4xx, error em 5xx
- [ ] Queries > 100ms logadas (SQLAlchemy event listener)
- [ ] Sentry configurado com release tag + environment
- [ ] OpenTelemetry propagando request_id como span_id
- [ ] `/healthz` e `/readyz` atualizados se serviço novo
- [ ] Dashboard Grafana com as métricas chave
- [ ] Alertas Prometheus configurados (error rate, latency)
- [ ] Retention policy definida (logs, traces, metrics)
