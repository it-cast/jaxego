# Phase 8: Despacho em cascata + oferta + aceite — Research

**Researched:** 2026-06-10
**Domain:** Orquestração assíncrona de despacho (arq + Redis), concorrência distribuída (lock de aceite único), privacidade de PII no payload de oferta (RN-013), adapters de integração (OSRM/ETA, Web Push VAPID)
**Confidence:** HIGH (stack/concorrência/privacidade verificados em código + docs); MEDIUM (mecânica exata do agendamento da cascata, contrato OSRM self-hosted)

<user_constraints>
## User Constraints (from 08-CONTEXT.md)

### Locked Decisions (CONTEXT § Implementation Decisions)
- **D-01:** Cascata SEQUENCIAL (nunca broadcast — RN-009). Elegíveis = online + cobre coleta E entrega (Phase 6) + carga < limite + não bloqueado pela loja. Favoritos elegíveis primeiro (1 por vez, `timeout_oferta_s` default 20s; janela total de favoritos `timeout_favoritos_s` default 60s — config da Phase 6). Esgotou favoritos → cascata no ranking automático. [travado ADR-007/RN-009]
- **D-02:** Ranking automático = distância em rota (OSRM) + score (placeholder Phase 13 — M1 sem peso financeiro, ADR-013) + carga atual + preço da tabela do entregador. [travado ADR-007]
- **D-03:** Cada oferta tem timer configurável por área (10–60s, default 20s); **Redis TTL é a fonte de verdade**; o cronômetro do app é só visual. Timeout/recusa → próximo da cascata. [travado ADR-104]
- **D-04:** Oferta mostra: origem (endereço completo da coleta), destino (**apenas BAIRRO + distância — RN-013**), valor da corrida, cronômetro. Endereço completo do destino só após coleta (Phase 9). [travado RN-013]
- **D-05:** Aceite usa **lock transacional** (Redis lock por entrega + SELECT FOR UPDATE no DB — reuso Phase 7). Dois aceites simultâneos → o segundo recebe "essa entrega acabou de ser aceita" sem penalidade (F-05 E3). Aceite → transição CRIADA→ACEITA (Phase 7); demais ofertas da cascata canceladas; nome/foto/placa/score do entregador visíveis para a loja. [travado ADR-007 + F-05 E3]
- **D-06:** `merchant_courier_favorites` e `merchant_courier_blocks` (pares loja↔entregador, SEPARADOS). Bloqueio privado, vale só para aquela loja, não afeta score (RN-014). Favoritos primeiro; bloqueados nunca recebem oferta. [travado RN-014]
- **D-07:** E1 cascata esgotada → loja notificada (aumentar frete/re-oferta, aguardar/re-cascata 2min, cancelar sem custo). E4 loja cancela durante cascata → ofertas canceladas, sem custo (RN-004). E2/E3 tratados. [F-05 E1-E4]
- **D-08:** OSRM atrás de adapter (Stub de dev; fallback haversine ×1.4 com flag `eta_degraded`). Push (Web Push VAPID) atrás de adapter; ambos com Stub nos testes. [integracoes.md §6/§8, DRV-006 pattern]

### Claude's Discretion
- Mecânica exata do agendamento da cascata (arq job vs loop com Redis) — provável arq job orquestrando ofertas sequenciais com Redis TTL.
- Estrutura do estado da oferta em Redis (`offer:{delivery_id}` com TTL, lista de candidatos).
- App do entregador: como receber a oferta (push + polling de oferta ativa).

### Deferred Ideas (OUT OF SCOPE)
- Coleta/comprovação foto+GPS/entrega/tracking (ACEITA→COLETADA→ENTREGUE) — **Phase 9**.
- "Aceitou e sumiu" (2× ETA sem chegar) cancelamento — comportamento na **Phase 9** (aqui só o aceite).
- Broadcast opt-in por entrega — pós-M1 (TD-011).
- Cobrança da corrida — Phase 10/11.
- Score com peso no ranking — v1.1 (ADR-013; M1 score sem peso).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-024 | Despacho em cascata (favoritos → ranking) com locks; cascata esgotada → opções da loja (E1); teste de concorrência 2 aceites; Redis TTL fonte de verdade; loja cancela → ofertas canceladas | Padrão de orquestração arq + estado em Redis `offer:{delivery_id}`; lock de aceite (redis-py `Lock` + `FOR UPDATE` reuso `transition()`); montagem de elegíveis reusa `eligible_online_prices_cents`/`is_eligible` (Phase 6) |
| REQ-025 | Oferta com privacidade do destino (RN-013): destino só BAIRRO + distância; endereço completo só após COLETADA; teste de contrato no payload | Modelo `Delivery` já separa estruturalmente `dropoff_address`/`number`/`complement` (FULL) de `dropoff_neighborhood_id`+`distance_m` (oferta). Serializer dedicado `OfferOut` constrói SEM os campos FULL por construção |
| REQ-012 (dados) | Favoritos/bloqueados da loja na elegibilidade | Migration 0007 cria `merchant_courier_favorites` / `merchant_courier_blocks` (pares area-scoped, UNIQUE por par). Filtro de bloqueados na montagem de elegíveis; favoritos antes do ranking |
| REQ-054 | OSRM/ETA `[ASSUMIDO]` para ranking e estimativa | Adapter `RoutingPort` (Protocol + httpx + Stub) + fallback haversine ×1.4 com flag `eta_degraded`. Contrato OSRM `/route/v1` e `/table/v1` verificado (duration s, distance m) |
</phase_requirements>

## Summary

Esta fase entrega o coração operacional do Jaxegô: transformar uma entrega `CRIADA` (Phase 7) em `ACEITA` através de uma **cascata sequencial** de ofertas (favoritos → ranking automático), cada uma com **timeout cuja fonte de verdade é o Redis TTL** (ADR-104, nunca o cronômetro do cliente), terminando em um **aceite único garantido por lock** que sobrevive a corrida de rede. Três pilares dominam o risco: (1) **concorrência** — dois aceites simultâneos não podem dupla-aceitar; (2) **privacidade** — o payload de oferta NUNCA expõe o endereço completo do destino (RN-013) nem a localização dos entregadores online à loja (ADR-007); (3) **resiliência de integração** — OSRM e push degradam sem bloquear o despacho.

A boa notícia: o código das Phases 6 e 7 já entrega quase toda a fundação. O modelo `Delivery` foi desenhado em Phase 7 **explicitamente para esta fase** — separa estruturalmente os campos FULL do destino dos campos de oferta (RN-013 by construction, comentado no model). O `transition()` já carrega a linha `FOR UPDATE` (lock pessimista) e é o único writer de `deliveries.state`, com idempotência de máquina de estados (segundo aceite cai em `assert_delivery_transition("ACEITA","ACEITA")` → 422). A elegibilidade espacial (`is_eligible`, cobertura coleta E entrega), a disponibilidade (`is_online`/`status=='active'`) e o cálculo de preço efetivo (`effective_price_cents`) já existem e devem ser **reusados, não reescritos**. Redis (`redis>=5`), arq (`>=0.26`) e o adapter pattern (Protocol + httpx + Stub + factory que devolve Stub em dev/test) já estão no projeto.

O trabalho novo é: (a) migration 0007 (favorites/blocks); (b) a **orquestração da cascata** — provável arq job que oferece sequencialmente, guardando o estado da oferta corrente em `offer:{delivery_id}` com TTL = `timeout_oferta_s` da área, avançando ao próximo candidato no expire/recusa; (c) o **endpoint de aceite** com a camada de lock (redis-py `Lock` por entrega + `FOR UPDATE`); (d) dois adapters novos (`RoutingPort` OSRM, `PushPort` VAPID) com Stub; (e) o app do entregador (home online/offline + sheet de oferta com cronômetro). O ranking M1 combina ETA (OSRM) + carga + preço; o **score entra como placeholder sem peso** (ADR-013).

**Primary recommendation:** Orquestrar a cascata com **um arq job re-agendável** (`dispatch_offer_task(delivery_id)`) cujo estado vive em Redis (`offer:{delivery_id}` com TTL da área + `dispatch:{delivery_id}:candidates` como fila ordenada); o aceite é um endpoint síncrono protegido por **redis-py `Lock(name=f"accept:{delivery_id}")` + `SELECT ... FOR UPDATE`**, com a transição CRIADA→ACEITA idempotente já existente decidindo o vencedor (segundo aceite → 409 amigável, sem penalidade). Testar a corrida de verdade com `@pytest.mark.mysql` + fakeredis (ou Redis real).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Orquestração da cascata (oferta sequencial, timeout, avanço) | API / arq worker | Redis (estado + TTL) | Lógica de negócio + temporização; Redis TTL é a fonte de verdade do timer (ADR-104), nunca o cliente |
| Montagem de elegíveis (online + cobertura + carga + bloqueio) | API / Backend | MySQL (couriers, coverage, blocks) | Invariante de negócio (RN-003/009/014); reusa Phase 6 |
| Aceite único (lock) | API / Backend | Redis (lock) + MySQL (FOR UPDATE) | Concorrência distribuída + serialização transacional; defesa em profundidade |
| Estado da oferta + cronômetro autoritativo | Redis | API (lê/escreve) | TTL como verdade do timer (ADR-104); cronômetro do app é cosmético |
| Privacidade do payload de oferta (RN-013) | API / Backend (serializer) | — | Serializer constrói SEM endereço completo por construção; nunca filtro opcional |
| Ranking (ETA + score + carga + preço) | API / Backend | OSRM (adapter), MySQL (score/pricing) | Lógica pura sobre dados; OSRM atrás de adapter com fallback |
| Notificação de oferta/aceite | arq worker (fila) | Web Push (adapter VAPID) | Nunca push síncrono do endpoint; fila com idempotência; degrade silencioso |
| Receber oferta no app | Browser/Client (Ionic) | API (polling de oferta ativa) | Push acorda + polling busca a oferta ativa autoritativa do servidor |

## Project Constraints (from CLAUDE.md)

- **Gate 4 (Security baseline)** obrigatório: fase com endpoint/concorrência/privacidade exige `## Security Baseline` neste RESEARCH consultando `owasp-security`. (Esta fase: aceite concorrente + RN-013 + push.)
- **Gate 7 (Tests + Lint)**: `uv run pytest && uv run ruff check .` verde antes de fechar.
- **TD-010 (naive datetime, `urgency_class: pre_launch_high`)**: TODO timestamp de oferta/aceite/TTL é **aware UTC** (`datetime.now(UTC)`). Lint/teste custom proíbe naive datetime no domínio. Já praticado no código existente (`transition()`, `coverage.py`).
- **Regra 11 (tech debt na phase)**: consultar TDs com prazo nesta phase. TD-010 incide; TD-011 (broadcast opt-in) é deferido/pós-M1, fora de escopo.
- **Regra 12 (LOW confidence → task/TD)**: cada item LOW abaixo vira task explícita no PLAN ou TD com `urgency_class`.
- **DRV-002**: soft delete em domínio, FK RESTRICT em transacionais, utf8mb4, UTC no banco.
- **DRV-003**: API `/v1/`, erros RFC-7807, idempotência por header em escrita relevante.
- **A09/LGPD**: PII (endereço, telefone do destinatário, CPF) NUNCA em log de aplicação — só ids/states. Já praticado.
- **AreaScoped (ADR-001/RN-001)**: tudo carrega `area_id`; toda query filtra pelo escopo. Aceite valida posse na query (404, nunca 403).

## Standard Stack

### Core (já no projeto — REUSE, não adicionar)
| Library | Version (verificada) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| redis (redis-py) | `>=5,<6` (instalado; última 6.4.0) `[VERIFIED: pyproject.toml + ctx7 /redis/redis-py]` | Lock de aceite (`redis.asyncio.lock.Lock`) + estado da oferta `offer:{id}` com TTL | Cliente oficial; `Lock` distribuído nativo (SET NX + token + release seguro via Lua) |
| arq | `>=0.26,<0.27` `[VERIFIED: pyproject.toml]` | Job de orquestração da cascata (`dispatch_offer_task`) + fila de push | Já é o worker do projeto (`WorkerSettings`); suporta enqueue com `_defer_by`/agendamento |
| sqlalchemy | `>=2,<3` `[VERIFIED: pyproject.toml]` | `SELECT ... FOR UPDATE` no aceite (`.with_for_update()`) | Já usado em `transition()` — base do aceite único |
| httpx | `>=0.28.1` `[VERIFIED: pyproject.toml]` | Adapter OSRM (cliente HTTP async) | Padrão dos adapters existentes (`http.py`) |
| structlog | `>=24.1` `[VERIFIED]` | Log sem PII (só ids/states) | Padrão A09 do projeto |

### Supporting (NOVO — avaliar adição)
| Library | Version (verificada) | Purpose | When to Use |
|---------|---------|---------|-------------|
| pywebpush | `2.3.0` (última) `[VERIFIED: pip index]` | Envio Web Push VAPID (encripta payload aes128gcm + headers VAPID) | Apenas no **adapter real** de push (staging/prod). Em dev/test o factory devolve `PushStubAdapter` (sem rede). `webpush()` é síncrono → rodar no worker arq, não no request |
| py-vapid | `1.9.4` (dependência de pywebpush) `[VERIFIED: pip index]` | Geração/assinatura das claims VAPID | Transitivo de pywebpush; chave privada VAPID via env (secret) |
| fakeredis | `2.36.1` (última) `[VERIFIED: pip index]` | Redis em memória nos testes (lock + TTL) sem servidor | **dev-group** apenas. Alternativa a Redis real para o teste de corrida (ver LOW-2) |

**Alternativa considerada (NÃO adotar):** OSRM via SDK Python dedicado — não existe SDK oficial maduro; httpx cru contra a API REST do OSRM self-hosted é o padrão e mantém o adapter pattern. Distância em linha reta (haversine) é o **fallback**, não a fonte primária.

**Installation (somente o que faltar):**
```bash
# Runtime (apenas push real — adapter de prod):
uv add pywebpush
# Dev (testes de concorrência com Redis em memória):
uv add --group dev fakeredis
```

**Version verification:**
```bash
pip index versions pywebpush   # 2.3.0  [VERIFIED 2026-06-10]
pip index versions fakeredis   # 2.36.1 [VERIFIED 2026-06-10]
pip index versions py-vapid     # 1.9.4  [VERIFIED 2026-06-10]
```

## Architecture Patterns

### System Architecture Diagram (fluxo F-05)

```
  [Loja] POST /v1/.../deliveries (Phase 7) ── delivery CRIADA
                  │
                  ▼
        enqueue dispatch_offer_task(delivery_id)         (arq)
                  │
                  ▼
   ┌─────────────────────────────────────────────────────┐
   │  dispatch_offer_task (arq worker)                    │
   │   1. monta candidatos (uma vez): online + active     │
   │      + cobertura coleta E entrega (is_eligible)      │
   │      + carga < max_concurrent + NÃO bloqueado        │
   │      → ordena: FAVORITOS primeiro, depois RANKING    │
   │        (ETA OSRM + score[placeholder] + carga+preço) │
   │      → grava dispatch:{id}:candidates (fila Redis)   │
   │   2. próximo candidato → grava offer:{id} (Redis,    │
   │      TTL = timeout_oferta_s da área) ──── ADR-104     │
   │      → enqueue push "nova oferta" (fila, idempotente) │
   │   3. re-agenda a si mesmo p/ TTL+ε (avanço no expire) │
   └─────────────────────────────────────────────────────┘
        │ push acorda            │ TTL expira / recusa
        ▼                        ▼
  [App entregador]        próximo candidato (volta ao passo 2)
  GET /v1/offers/active   (esgotou favoritos → ranking;
        │                  esgotou tudo → notifica loja E1)
        ▼
  POST /v1/offers/{delivery_id}/accept   ◄── DOIS chegam juntos (corrida)
        │
        ▼
   ┌─────────────────────────────────────────────────────┐
   │  accept_offer (endpoint síncrono)                    │
   │   a. authz: este courier é o ALVO de offer:{id}? (A01)│
   │   b. redis Lock(f"accept:{id}", blocking_timeout=2)  │
   │   c. SELECT delivery ... FOR UPDATE (Phase 7)        │
   │   d. transition CRIADA→ACEITA (idempotente):         │
   │        2º aceite → 422/409 "já aceita" SEM penalidade │
   │   e. DEL offer:{id}; cancela demais ofertas pendentes │
   │   f. enqueue push "aceito" p/ loja + destinatário    │
   └─────────────────────────────────────────────────────┘
                  │
                  ▼
           delivery ACEITA  →  Phase 9 (coleta)
```

### Recommended Project Structure (novos arquivos)
```
apps/api/app/
├── dispatch/                    # NOVO módulo da Phase 8
│   ├── service.py               # accept_offer (lock + FOR UPDATE), cancel_pending_offers
│   ├── cascade.py               # montagem de candidatos (favoritos→ranking), ordenação
│   ├── ranking.py               # score combinado ETA+score+carga+preço (função pura)
│   ├── offer_state.py           # wrapper Redis: offer:{id}, candidates, TTL helpers
│   ├── schemas.py               # OfferOut (RN-013: SEM endereço completo), AcceptResponse
│   ├── router.py                # GET /offers/active, POST /offers/{id}/accept, /decline
│   └── exceptions.py            # OfferAlreadyTakenError(409), NotOfferTargetError(404)
├── merchants/
│   ├── favorites.py             # NOVO: CRUD favorites/blocks (RN-014)
│   └── models.py                # + MerchantCourierFavorite / MerchantCourierBlock
├── integrations/
│   ├── routing.py               # NOVO: RoutingHttpAdapter (OSRM httpx)
│   ├── routing_stub.py          # NOVO: RoutingStubAdapter (haversine determinístico)
│   ├── push.py                  # NOVO: PushVapidAdapter (pywebpush, só prod)
│   ├── push_stub.py             # NOVO: PushStubAdapter (registra envios, sem rede)
│   └── base.py                  # + RoutingPort, PushPort (Protocols) + RouteResult
├── workers/
│   ├── dispatch.py              # NOVO: dispatch_offer_task (arq, re-agendável)
│   └── settings.py              # + registrar dispatch_offer_task + send_push_task
alembic/versions/
└── 0007_dispatch_favorites_blocks.py   # NOVO
```

### Pattern 1: Estado da oferta em Redis com TTL autoritativo (ADR-104)
**What:** O timer do cronômetro vive no servidor. `offer:{delivery_id}` guarda o candidato corrente + deadline, com TTL = `timeout_oferta_s` da área. O expire do Redis é o evento que avança a cascata; o app só lê o tempo restante.
**When to use:** Toda oferta. O app NUNCA decide o timeout.
**Example:**
```python
# app/dispatch/offer_state.py  — Redis é a fonte de verdade do timer (ADR-104)
# Source: ctx7 /redis/redis-py (async set with ex / get / delete)
from __future__ import annotations
import json
from datetime import UTC, datetime, timedelta
import redis.asyncio as redis

def _offer_key(delivery_id: int) -> str:
    return f"offer:{delivery_id}"

async def open_offer(
    r: redis.Redis, *, delivery_id: int, courier_id: int, timeout_s: int
) -> datetime:
    """Abre a oferta corrente; TTL do Redis = janela do cronômetro (ADR-104)."""
    expires_at = datetime.now(UTC) + timedelta(seconds=timeout_s)  # AWARE — TD-010
    payload = json.dumps(
        {"courier_id": courier_id, "expires_at": expires_at.isoformat()}
    )
    # SET com expiração atômica: a chave SOME sozinha no fim da janela.
    await r.set(_offer_key(delivery_id), payload, ex=timeout_s)
    return expires_at

async def current_offer(r: redis.Redis, delivery_id: int) -> dict | None:
    """A oferta ativa, ou None se já expirou (TTL do Redis decidiu)."""
    raw = await r.get(_offer_key(delivery_id))
    return json.loads(raw) if raw else None

async def close_offer(r: redis.Redis, delivery_id: int) -> None:
    await r.delete(_offer_key(delivery_id))
```

### Pattern 2: Aceite único — redis Lock + SELECT FOR UPDATE (D-05, peça crítica)
**What:** Defesa em profundidade. O `Lock` do Redis serializa os requests entre processos/instâncias; o `FOR UPDATE` serializa dentro da transação do DB; a máquina de estados idempotente decide o vencedor.
**When to use:** O endpoint de aceite, sempre.
**Example:**
```python
# app/dispatch/service.py — aceite único (D-05). Reusa transition() (Phase 7).
# Source: ctx7 /redis/redis-py docs/lock.md (Lock acquire/release) +
#         app/deliveries/service.py transition() (FOR UPDATE existente)
from __future__ import annotations
import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deliveries.models import Delivery
from app.deliveries.service import transition
from app.deliveries.state_machine import InvalidTransitionError
from app.dispatch.exceptions import NotOfferTargetError, OfferAlreadyTakenError
from app.dispatch.offer_state import current_offer, close_offer

async def accept_offer(
    session: AsyncSession,
    r: redis.Redis,
    *,
    area_id: int,
    delivery_id: int,
    courier_id: int,
    ip: str | None,
) -> Delivery:
    """Aceite único. Lock Redis + FOR UPDATE + transição idempotente.

    O 2º aceite simultâneo cai num destes pontos e recebe 409 SEM penalidade:
      - lock não adquirido em 2s, OU
      - estado já != CRIADA após o FOR UPDATE, OU
      - assert_delivery_transition('ACEITA','ACEITA') → InvalidTransitionError.
    """
    # A01: só o courier-alvo da oferta corrente pode aceitar (autorização, não 403).
    offer = await current_offer(r, delivery_id)
    if offer is None or offer["courier_id"] != courier_id:
        raise NotOfferTargetError()  # 404 — não vaza que a oferta existe p/ outro

    lock = r.lock(f"accept:{delivery_id}", timeout=10, blocking_timeout=2)
    acquired = await lock.acquire()
    if not acquired:
        raise OfferAlreadyTakenError()  # outro está aceitando agora
    try:
        # FOR UPDATE: serializa no DB; o 2º re-lê o estado já comitado.
        locked = (
            await session.execute(
                select(Delivery)
                .where(Delivery.id == delivery_id, Delivery.area_id == area_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if locked is None:
            raise NotOfferTargetError()
        if locked.state != "CRIADA":
            raise OfferAlreadyTakenError()  # já aceita/cancelada — SEM penalidade
        try:
            locked.courier_id = courier_id  # set antes da transição
            await transition(
                session, delivery=locked, to_state="ACEITA",
                actor_id=None, ip=ip,  # actor = user do courier no router
            )
        except InvalidTransitionError as exc:
            raise OfferAlreadyTakenError() from exc
        await close_offer(r, delivery_id)
        # cancelar ofertas pendentes da cascata + enqueue push (fila) no router/service
        return locked
    finally:
        await lock.release()  # release seguro: redis-py confere o token (Lua)
```

### Pattern 3: Adapter OSRM com fallback haversine (D-08)
**What:** `RoutingPort` (Protocol) + impl httpx (OSRM `/route/v1`) + Stub (haversine determinístico). Se OSRM falha, o serviço cai no haversine ×1.4 e seta `eta_degraded=True` — **nunca bloqueia o despacho**.
**Example:**
```python
# app/integrations/base.py  (+ ao existente)
# Source: project-osrm.org/docs api (route: duration s, distance m) [CITED]
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class RouteResult:
    distance_m: int        # metros (OSRM: float meters)
    duration_s: int        # segundos (OSRM: float seconds)
    degraded: bool = False # True quando veio do fallback haversine (eta_degraded)

class RoutingPort(Protocol):
    """Distância/ETA em rota. NUNCA levanta p/ o caller — degrada (D-08)."""
    async def route(
        self, *, origin: tuple[float, float], dest: tuple[float, float]
    ) -> RouteResult: ...
```

### Pattern 4: Ranking como função pura (testável em SQLite, padrão Phase 6/7)
**What:** A ordenação do ranking é uma função pura sobre tuplas (eta_s, score, carga, preço_cents). Score entra com **peso zero** no M1 (ADR-013) — presente na assinatura, multiplicado por 0, documentado.
```python
# app/dispatch/ranking.py — score SEM peso no M1 (ADR-013). Determinístico, puro.
def rank_key(eta_s: int, load: int, price_cents: int, score: float) -> tuple:
    """Chave de ordenação (menor é melhor). M1: score com peso 0 (ADR-013).

    Ordena por ETA (mais perto primeiro), depois carga (menos ocupado),
    depois preço (mais barato). `score` fica na assinatura para a v1.1 ligar
    o peso sem mudar o call-site (ADR-013); hoje NÃO entra na ordem.
    """
    _SCORE_WEIGHT_M1 = 0.0  # ADR-013 — sem consequência no M1
    return (eta_s, load, price_cents, -score * _SCORE_WEIGHT_M1)
```

### Anti-Patterns to Avoid
- **Cronômetro do cliente como verdade:** decidir expiração no app (ADR-104 proíbe). O Redis TTL decide; o app só exibe.
- **Broadcast / oferta paralela:** oferecer a vários ao mesmo tempo (RN-009 proíbe no M1). Sempre 1 por vez.
- **Filtro de endereço opcional no serializer:** confiar que alguém lembrou de tirar o `dropoff_address`. Use um schema `OfferOut` que **não tem o campo** (RN-013 por construção — o model já separa).
- **Aceite sem lock confiando só no FOR UPDATE entre instâncias:** com múltiplos workers/instâncias o FOR UPDATE basta no DB, mas o Redis Lock dá curto-circuito barato e evita trabalho duplicado de cancelamento de ofertas. Defesa em profundidade (D-05).
- **Push síncrono no request:** bloqueia a resposta e não tem retry. Sempre via fila arq (skill push §"fila de envio").
- **Localização do entregador em qualquer payload da loja:** ADR-007 proíbe. A loja só vê nome/foto/placa/score APÓS o aceite.
- **Bloqueado afetando score:** RN-014 — bloqueio é privado, não é evento de score.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Lock distribuído de aceite | `SET NX` manual + release com `DEL` | `redis-py` `r.lock(name, timeout, blocking_timeout)` | release ingênuo com `DEL` apaga o lock de OUTRO dono se o seu já expirou; redis-py confere o token via Lua antes de liberar |
| Serialização da transição no DB | flag booleana `accepted` + UPDATE | `SELECT ... FOR UPDATE` (já em `transition()`) | lost update / TOCTOU; o lock pessimista do row já é usado e testado na Phase 7 |
| Idempotência do segundo aceite | comparar timestamps / "quem chegou antes" | máquina de estados `assert_delivery_transition` (Phase 7) | o 2º aceite vira transição inválida CRIADA-já-saiu → 422; lógica única, sem caso especial |
| Distância/ETA em rota | calcular rota você mesmo | OSRM `/route/v1` (adapter) + fallback haversine | roteamento real exige grafo viário; haversine é só o degrade |
| Encriptação do payload Web Push | montar aes128gcm + ECDH + VAPID JWT na mão | `pywebpush.webpush()` | criptografia Web Push (RFC 8188 + VAPID RFC 8292) é fácil de errar; A02/A06 — não hand-roll cripto |
| Timer/expiração da oferta | thread/loop contando segundos | Redis TTL (`SET ex=...`) + re-agendamento arq | TTL atômico no Redis é a fonte de verdade (ADR-104) e sobrevive a restart do worker |
| Estado online/carga/cobertura | reconsultar do zero | `availability.compute_busy`, `coverage.is_eligible`, `estimate.effective_price_cents` (Phase 6) | já implementados, testados e area-scoped — REUSE |

**Key insight:** Quase tudo de risco nesta fase JÁ existe no código (FOR UPDATE, elegibilidade, preço, máquina de estados, adapter pattern, Redis no projeto). O erro caro seria reimplementar concorrência/cobertura em vez de compor o que está pronto. O genuinamente novo é a **orquestração** (arq + TTL) e o **wrapping de lock** no aceite.

## Runtime State Inventory

> Fase tem componente de migração leve (novas tabelas) + estado vivo em Redis. Categorias abaixo respondidas explicitamente.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Migration 0007 cria `merchant_courier_favorites` / `merchant_courier_blocks` (novas, sem dados legados a migrar). `deliveries.courier_id` (já existe, nullable) passa a ser preenchido no aceite. | Migration 0007 (code + schema); nenhum backfill |
| Live service config | `area.config.timeout_oferta_s` (10–60s) e `timeout_favoritos_s` (30–180s) já existem (Phase 6, `AreaConfig` tipada). A cascata LÊ esses valores — não cria config nova. | Nenhuma migração de config; apenas consumo |
| OS-registered state | Nenhum. arq worker já roda (`WorkerSettings`); registra-se o novo `dispatch_offer_task` na lista `functions`. | Adicionar job à `functions` (code) — sem registro de OS |
| Secrets/env vars | NOVOS: `VAPID_PRIVATE_KEY` / `VAPID_PUBLIC_KEY` / `VAPID_CLAIM_SUB` (push, só prod), `OSRM_BASE_URL` + `OSRM_ALLOWLIST_HOSTS` (SSRF guard, padrão dos adapters). Em dev/test o factory devolve Stubs → não consultados. | Adicionar a `Settings` (default None p/ secrets — Gate 8); `.env.example` com placeholders |
| Build artifacts | `pywebpush` é dependência runtime NOVA (entra no lock). `fakeredis` entra no dev-group. | `uv add` regenera `uv.lock`; reinstalar no CI |

**Nada encontrado em "OS-registered state":** verificado — o único processo de longa duração é o arq worker já existente; a Phase 8 só adiciona uma função à lista, sem novo serviço de SO.

## Common Pitfalls

### Pitfall 1: O segundo aceite recebe penalidade
**What goes wrong:** Tratar o 2º aceite como "cancelamento-pós-aceite" do entregador, manchando o histórico de quem só perdeu a corrida de rede.
**Why it happens:** Reusar o caminho de cancelamento sem distinguir "perdi a corrida" de "aceitei e desisti".
**How to avoid:** O 2º aceite é `OfferAlreadyTakenError` → **409, mensagem amigável, ZERO efeito no histórico** (F-05 E3 explícito). É um não-evento, não um cancelamento.
**Warning signs:** Teste de corrida que verifica só "1 venceu" sem assertar "perdedor sem penalidade".

### Pitfall 2: Vazamento de endereço completo no payload de oferta (RN-013)
**What goes wrong:** O serializer da oferta inclui `dropoff_address`/`dropoff_number`/`dropoff_complement`.
**Why it happens:** Reusar o schema de detalhe da entrega (loja) para a oferta (entregador).
**How to avoid:** `OfferOut` é um schema **separado** que expõe só `dropoff_neighborhood` (nome do bairro) + `distance_m` + origem completa + valor + cronômetro. O model `Delivery` já isola os campos FULL — construir o `OfferOut` a partir dos campos permitidos, nunca via `from_orm` do model inteiro. Teste de contrato: `assert "dropoff_address" not in offer_payload`.
**Warning signs:** `OfferOut(**delivery.__dict__)` ou `model_config = from_attributes` sobre o model completo.

### Pitfall 3: Cascata avança duas vezes (double-advance)
**What goes wrong:** No expire da oferta, tanto o re-agendamento do arq quanto uma recusa do app disparam o avanço → pula um candidato ou oferece a dois.
**Why it happens:** Dois caminhos (timeout + decline) mutam o mesmo estado sem coordenação.
**How to avoid:** O avanço é idempotente por "geração" da oferta: a recusa só avança se o `offer:{id}` corrente ainda for daquele candidato (compare-and-advance); o re-agendamento confere se a oferta ainda existe antes de avançar. Um pequeno lock `r.lock(f"cascade:{id}")` em torno do avanço serializa timeout vs decline.
**Warning signs:** Logs com dois `dispatch.offer.opened` para o mesmo `delivery_id` no mesmo instante.

### Pitfall 4: OSRM fora derruba o despacho
**What goes wrong:** Exceção do OSRM propaga e a cascata nunca monta o ranking.
**Why it happens:** Adapter levanta em vez de degradar.
**How to avoid:** `RoutingHttpAdapter` captura timeout/erro e devolve `RouteResult(degraded=True)` via haversine ×1.4; a fase loga `eta_degraded` (observabilidade) mas continua. Nunca `raise` no caller do ranking.
**Warning signs:** Despacho que falha em ambiente sem OSRM; teste que não cobre o caminho degradado.

### Pitfall 5: Lock do Redis liberando o cadeado de outro
**What goes wrong:** `await r.delete(f"accept:{id}")` no finally apaga o lock que já expirou e foi readquirido por outro request.
**Why it happens:** Release manual sem checar dono.
**How to avoid:** Usar `Lock.release()` do redis-py (confere o token via script Lua). Não fazer `DEL` manual.
**Warning signs:** `r.delete` em torno de seção crítica de aceite.

### Pitfall 6: Naive datetime no TTL/aceite (TD-010)
**What goes wrong:** `datetime.utcnow()` ou `.replace(tzinfo=None)` em `accepted_at`/`expires_at`.
**How to avoid:** Sempre `datetime.now(UTC)` (aware). Já é o padrão do código (`transition()`). O lint/teste custom de TD-010 deve cobrir o módulo `dispatch/`.
**Warning signs:** `utcnow()` em qualquer arquivo novo.

## Code Examples

### Montagem de elegíveis reusando Phase 6 (favoritos→ranking, exclui bloqueados)
```python
# app/dispatch/cascade.py (esboço) — REUSA is_eligible + effective_price_cents (Phase 6)
# Source: app/couriers/coverage.py, app/deliveries/estimate.py (existentes)
from sqlalchemy import select
from app.couriers.coverage import is_eligible
from app.couriers.models import Courier, CourierCoverageArea, CourierPricingTable
from app.merchants.models import MerchantCourierBlock, MerchantCourierFavorite

async def build_candidates(session, *, area_id, merchant_id, pickup_nbhd_id,
                           dropoff_nbhd_id, distance_m):
    """Online + active + cobertura(coleta E entrega) + NÃO bloqueado.
    Favoritos primeiro; resto ordenado por ranking (em ranking.py)."""
    blocked = {
        r[0] for r in (await session.execute(
            select(MerchantCourierBlock.courier_id).where(
                MerchantCourierBlock.area_id == area_id,
                MerchantCourierBlock.merchant_id == merchant_id)
        )).all()
    }
    favorites = {
        r[0] for r in (await session.execute(
            select(MerchantCourierFavorite.courier_id).where(
                MerchantCourierFavorite.area_id == area_id,
                MerchantCourierFavorite.merchant_id == merchant_id)
        )).all()
    }
    online = (await session.execute(
        select(Courier).where(
            Courier.area_id == area_id, Courier.is_online.is_(True),
            Courier.status == "active", Courier.deleted_at.is_(None))
    )).scalars().all()
    # ... carrega coverage/pricing em lote (sem N+1, como em estimate.py),
    #     filtra is_eligible + NÃO bloqueado + carga<max_concurrent,
    #     particiona favoritos vs resto; resto ordenado por rank_key.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| GCM key auth no Web Push | VAPID + aes128gcm (RFC 8188/8292) | pywebpush desabilitou GCM em jun/2024 `[VERIFIED: WebSearch]` | Usar `content_type="aes128gcm"` (default); não passar `gcm_key` |
| Timer no cliente | Redis TTL autoritativo | ADR-104 (M1) | Cronômetro do app é cosmético |
| Broadcast | Cascata sequencial | RN-009 (M1); broadcast opt-in só pós-M1 (TD-011) | 1 oferta por vez sempre |

**Deprecated/outdated:**
- `aesgcm` (sem 128) no Web Push: deprecado; nem todo User Agent decripta. Default `aes128gcm`.
- `datetime.utcnow()`: proibido (TD-010) — `datetime.now(UTC)`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | OSRM self-hosted expõe `/route/v1/{profile}/{coords}` com `duration` (s) e `distance` (m) | Stack / Pattern 3 | Contrato OSRM é estável e público `[CITED: project-osrm.org]`, MAS o deploy self-hosted (perfil `driving`, versão) não foi confirmado — adapter precisa ser robusto a 404/erro (já degrada) |
| A2 | arq suporta re-agendamento do próprio job para implementar o avanço por timeout | Pattern 1 / orquestração | Se o mecanismo escolhido (defer/cron/poll) não couber, cai para o LOW-1 (arq vs loop) |
| A3 | Push é via Web Push VAPID (navegador/PWA), não FCM/APNs | Stack / Push | A skill `push-notifications-architecture` cobre FCM/APNs; o projeto (integracoes.md §6) usa **Web Push VAPID** (`pywebpush`). O app é Ionic/Capacitor (ADR-003) — no Android via APK pode exigir FCM no futuro; M1 usa Web Push. Confirmar com dono se APK exige FCM |
| A4 | `merchant_courier_favorites`/`_blocks` são area-scoped com UNIQUE(area_id, merchant_id, courier_id) | Migration 0007 | Modelagem padrão; se houver necessidade cross-área, revisar (improvável — RN-001) |
| A5 | Score placeholder pode ser lido como `couriers.score` valor já existente | Pattern 4 / ranking | Se a coluna de score ainda não estiver populada na Phase 8, usar default 0 — peso 0 torna inócuo (ADR-013) |

## Open Questions

1. **arq job re-agendável vs loop de orquestração (LOW-1)**
   - What we know: arq é o worker; Redis TTL é a verdade do timer.
   - What's unclear: a mecânica exata de avanço no expire (job que se re-enfileira com `_defer_by`, vs um poller, vs keyspace notifications do Redis).
   - Recommendation: virar **task explícita** no PLAN (decidir e implementar `dispatch_offer_task` re-agendável com `_defer_by=timeout_oferta_s`; documentar). Não deixar como "verificar depois" (Regra 12).

2. **fakeredis vs Redis real no teste de corrida (LOW-2)**
   - What we know: o teste de 2 aceites simultâneos é o critério de aceite nº 1 (REQ-024).
   - What's unclear: fakeredis 2.36.1 implementa `Lock`/`SET NX`/TTL com fidelidade suficiente para o teste de corrida; pode ser necessário Redis real via `@pytest.mark.mysql`-equivalente (marker de integração).
   - Recommendation: task no PLAN — preferir Redis real (docker compose já tem) sob um marker de integração; fakeredis como fallback rápido para o caminho não-concorrente.

3. **Web Push VAPID vs FCM no APK (LOW-3)**
   - What we know: integracoes.md §6 diz Web Push VAPID; ADR-003 diz APK Capacitor.
   - What's unclear: se o APK Android M1 entrega push via Web Push (service worker) ou exigirá FCM.
   - Recommendation: M1 implementa `PushPort` + adapter VAPID + Stub; se o APK exigir FCM, é troca de adapter (contrato isola). Registrar como TD se não confirmado no piloto.

4. **Contrato OSRM exato e perfil (LOW-4)** — confirmar URL/perfil do OSRM self-hosted; adapter já degrada, mas a task deve validar contra o deploy real em integration_check.

5. **Formato do payload de push (LOW-5)** — definir o payload mínimo (sem PII — só `delivery_id`, deep link, "Nova oferta"); RN-013 e skill push §"Zero PII em payload" aplicam.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Redis | Lock de aceite + TTL de oferta | ✓ (compose) | redis-py `>=5` | — (essencial; sem Redis não há aceite seguro) |
| arq worker | Orquestração da cascata | ✓ (Phase 1) | `>=0.26` | — |
| MySQL 8 | FOR UPDATE no aceite | ✓ | 8 | — (SQLite no dev não testa FOR UPDATE → marker mysql) |
| OSRM self-hosted | Ranking ETA/distância | ✗ (a provisionar) | — | **haversine ×1.4 + `eta_degraded`** (não bloqueia) |
| Web Push (browser push service) | Notificar oferta/aceite | ✗ (externo, prod) | — | **degrade silencioso p/ e-mail/in-app** (skill push) |
| fakeredis | Teste rápido de lock/TTL | ✗ (a adicionar dev) | 2.36.1 | Redis real (compose) |

**Missing dependencies with no fallback:** nenhum bloqueante — Redis/arq/MySQL já existem.
**Missing dependencies with fallback:** OSRM (haversine), Web Push (e-mail/in-app), fakeredis (Redis real).

## Validation Architecture

> `nyquist_validation` não está em config.json (ausente) → tratado como habilitado.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio (`asyncio_mode = "auto"`) `[VERIFIED: pyproject.toml]` |
| Config file | `apps/api/pyproject.toml` (`[tool.pytest.ini_options]`, markers `mysql`) |
| Quick run command | `cd apps/api && uv run pytest -m "not mysql" -x` |
| Full suite command | `cd apps/api && uv run pytest` (com `-m mysql` contra MySQL real no CI) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-024 | 2 aceites simultâneos → 1 vence, outro 409 sem penalidade | integração (concorrência) | `uv run pytest -m mysql tests/dispatch/test_accept_race.py -x` | ❌ Wave 0 |
| REQ-024 | Cascata esgotada → opções da loja (E1) | unit/integração | `uv run pytest tests/dispatch/test_cascade.py -x` | ❌ Wave 0 |
| REQ-024 | Loja cancela durante cascata → ofertas canceladas (E4) | integração | `uv run pytest tests/dispatch/test_cancel_during_cascade.py -x` | ❌ Wave 0 |
| REQ-024 | Redis TTL fonte de verdade; timeout → próximo | integração | `uv run pytest tests/dispatch/test_offer_ttl.py -x` | ❌ Wave 0 |
| REQ-025 | Payload de oferta SEM endereço completo (RN-013) | contrato | `uv run pytest tests/dispatch/test_offer_privacy.py -x` | ❌ Wave 0 |
| REQ-012 | Bloqueado nunca recebe oferta; favoritos primeiro | unit | `uv run pytest tests/dispatch/test_eligibility.py -x` | ❌ Wave 0 |
| REQ-054 | OSRM fora → haversine + `eta_degraded` (não bloqueia) | unit (Stub) | `uv run pytest tests/integrations/test_routing.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest -m "not mysql" -x`
- **Per wave merge:** `uv run pytest` (inclui `-m mysql` no CI com Redis + MySQL reais)
- **Phase gate:** suíte completa verde antes de `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/dispatch/conftest.py` — fixtures: Redis (fakeredis ou real), seed de couriers online/elegíveis, delivery CRIADA, favoritos/blocks
- [ ] `tests/dispatch/test_accept_race.py` — corrida real (2 coroutines/clients aceitando) — **o teste mais importante da fase**
- [ ] `tests/dispatch/test_offer_privacy.py` — RN-013 contrato
- [ ] `tests/integrations/test_routing.py` + `test_push.py` — Stubs + caminho degradado
- [ ] dependência: `uv add pywebpush` (runtime), `uv add --group dev fakeredis`

## Security Baseline

> **Gate 4 — OBRIGATÓRIO.** Threat model consultando `owasp-security` (A01/A03/A04/A05/A09/A10) e `mobile/push-notifications-architecture`. Cada ameaça → mitigação citando a skill. O `threat_model` do PLAN herda desta seção (Regra 7).

### Threat Model

| # | Ameaça (STRIDE) | Vetor | Mitigação | Citação |
|---|-----------------|-------|-----------|---------|
| **TH-1** | **Race no aceite → dupla-aceitação** (Tampering / lost update) | 2 entregadores aceitam no mesmo instante (corrida de rede) | redis-py `Lock(f"accept:{id}", blocking_timeout=2)` + `SELECT ... FOR UPDATE` + transição idempotente CRIADA→ACEITA. 2º → 409 "já aceita" SEM penalidade. Defesa em profundidade (Redis entre instâncias; FOR UPDATE no DB; máquina de estados decide) | owasp A04 "Invariantes de negócio no backend, recalculados no servidor SEMPRE" + A01 |
| **TH-2** | **Vazamento de PII do destino na oferta (RN-013)** (Information Disclosure) | `OfferOut` inclui `dropoff_address`/número/complemento antes da coleta | Schema `OfferOut` separado, sem os campos FULL por construção (model já isola); só `dropoff_neighborhood` + `distance_m`. Teste de contrato `assert "dropoff_address" not in payload`. Endereço completo só após COLETADA (Phase 9) | owasp A01 "404, não vaze que o recurso existe" + LGPD (A09 "PII nunca onde não é necessária") + RN-013 |
| **TH-3** | **Localização dos entregadores online exposta à loja** (Information Disclosure) | Endpoint da loja vaza POINT/coords dos candidatos | Nenhum payload destinado à loja inclui localização de courier; a loja só vê nome/foto/placa/score APÓS o aceite. A localização ao vivo (Phase 9) é só do entregador aceito, na janela ACEITA→FINALIZADA | ADR-007 (não-negociável) + owasp A01 (ownership na query) |
| **TH-4** | **IDOR / autorização de oferta** (Elevation of Privilege) | Entregador B aceita oferta destinada a A; ou aceita entrega de outra área | Autorização: só o `courier_id` igual ao `offer:{id}.courier_id` corrente aceita (404 `NotOfferTargetError`, não 403); query do aceite filtra `area_id` (AreaScoped). Posse no WHERE, não em `if` | owasp A01 "tenant_id no WHERE de todo repositório; 404 (não 403)" |
| **TH-5** | **Bloqueado recebe oferta (RN-014)** (violação de regra) | Filtro de bloqueados esquecido na montagem de elegíveis | Bloqueados removidos na query de candidatos (`MerchantCourierBlock` set-difference, area+merchant scoped) ANTES de favoritos/ranking. Teste: courier bloqueado nunca aparece em `build_candidates` | owasp A04 "invariante de negócio no backend" + RN-014 |
| **TH-6** | **Replay / abuso de aceite** (Tampering) | Mesmo aceite reenviado várias vezes; aceite após expiração | Idempotência via máquina de estados (2º+ aceite → 409); aceite só válido enquanto `offer:{id}` existe e aponta para o courier; após `close_offer` ou expiração TTL → 404/409. Sem efeito colateral duplicado | owasp A08 "chave de idempotência; reentrega não duplica" + A04 |
| **TH-7** | **Push token / VAPID key vazando** (Information Disclosure / Spoofing) | Chave privada VAPID no repo; PII no payload de push | `VAPID_PRIVATE_KEY` só via env (`Field(default=None)`; segredo no repo = Gate 8 FAIL-BLOCK; se commitado → ROTACIONAR). Payload de push SEM PII (só `delivery_id` + deep link + "Nova oferta"). Subscription do push tratada como dado sensível | owasp A02/Gestão de Segredos "segredo no código = FAIL-BLOCK" + skill push "Zero PII em payload; tokens vazam às vezes" |
| **TH-8** | **DoS na cascata** (Denial of Service) | OSRM lento trava o worker; loja cria muitas entregas; oferta nunca expira | OSRM com `httpx` timeout curto + fallback haversine (nunca bloqueia); rate limit de criação já existe (Phase 7, `delivery_create_limiter` 30/min/loja); TTL atômico garante que a oferta SEMPRE expira (worker pode reiniciar). Cascata tem janela máxima (`timeout_favoritos_s` + nº candidatos finito) | owasp A04 "rate limit derivado do contexto; endpoints caros com timeout" |
| **TH-9** | **SSRF via OSRM URL** (Server-Side Request Forgery) | `OSRM_BASE_URL` apontado para metadata endpoint / IP interno | Allowlist de hosts (`OSRM_ALLOWLIST_HOSTS`) no adapter — mesmo padrão dos adapters existentes (`_hosts()` no factory, guard SSRF em `http.py`); rejeitar IP privado/link-local | owasp A10 "allowlist de hosts de saída; rejeitar IPs privados; revalidar pós-redirect" |
| **TH-10** | **PII em log durante o despacho** (Information Disclosure) | Logar endereço/telefone do destinatário ao montar candidatos | Log só com ids/states (`delivery_id`, `courier_id`, `area_id`, contagem de candidatos) — padrão já praticado em `transition()`/`create_delivery`. Redação estrutural central | owasp A09 "NUNCA logar CPF/telefone/endereço; redação estrutural, não disciplina" + LGPD |

### ASVS / OWASP Categories aplicáveis

| Categoria | Aplica | Controle padrão |
|-----------|--------|-----------------|
| A01 Broken Access Control | **sim** | Autorização da oferta (courier-alvo); AreaScoped no WHERE; 404 não 403 (TH-2/3/4) |
| A02 Cryptographic Failures | **sim** | VAPID key como segredo via env; `Lock.release` seguro (não `DEL`) (TH-7) |
| A03 Injection / Input Validation | **sim** | Pydantic v2 nos bodies de aceite/favoritos (`extra="forbid"`); ids tipados (`conint`) |
| A04 Insecure Design | **sim** | Invariante de aceite único no backend; rate limit; timeouts (TH-1/8) |
| A05 Security Misconfiguration | parcial | Headers/CORS já no middleware global (Phase 2); adapters com allowlist |
| A07 AuthN Failures | sim (herdado) | Aceite exige `get_current_user` + papel de entregador; nenhuma rota sem decisão de auth |
| A08 Integrity Failures | **sim** | Idempotência do aceite / não-duplicação (TH-6) |
| A09 Logging Failures | **sim** | Sem PII em log; logar aceite/recusa/expiração com `request_id` (TH-10) |
| A10 SSRF | **sim** | Allowlist do OSRM (TH-9) |

### Known Threat Patterns for FastAPI + Redis + MySQL (esta stack)

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Lost update no aceite concorrente | Tampering | `FOR UPDATE` + redis `Lock` + máquina de estados idempotente |
| Release de lock de outro dono | Tampering | `Lock.release()` (token via Lua), nunca `DEL` manual |
| Over-fetch de PII no serializer | Information Disclosure | Schema de saída dedicado, sem campos sensíveis por construção |
| Cross-tenant via id na rota | Elevation | `area_id`/posse no WHERE; 404 |
| Webhook/push payload com segredo/PII | Information Disclosure | env-only secrets; payload mínimo sem PII |

## Sources

### Primary (HIGH confidence)
- `app/deliveries/service.py` `transition()` — FOR UPDATE existente, base do aceite `[VERIFIED: código]`
- `app/deliveries/models.py` — separação estrutural FULL vs oferta (RN-013 by construction) `[VERIFIED]`
- `app/couriers/coverage.py` `is_eligible`, `app/deliveries/estimate.py` `effective_price_cents` — elegibilidade/preço reusáveis `[VERIFIED]`
- `app/integrations/base.py` + `factory.py` — adapter Protocol+Stub pattern `[VERIFIED]`
- `app/areas/config_schema.py` — `timeout_oferta_s`/`timeout_favoritos_s` já tipados `[VERIFIED]`
- ctx7 `/redis/redis-py` (docs/lock.md, connections.md, asyncio examples) — `Lock` API, async `set ex`, release seguro `[CITED]`
- `project-osrm.org/docs` API — route/table: `duration` (s), `distance` (m) `[CITED]`
- `.claude/skills/owasp-security/SKILL.md` (A01/A02/A03/A04/A08/A09/A10) `[VERIFIED]`
- `.claude/skills/mobile/push-notifications-architecture/SKILL.md` (fila, idempotência, zero-PII payload) `[VERIFIED]`
- ADR-007/ADR-104/ADR-013, RN-003/004/009/013/014, F-05 `[VERIFIED: docs do projeto]`

### Secondary (MEDIUM confidence)
- pywebpush 2.3.0 / py-vapid 1.9.4 / fakeredis 2.36.1 versões `[VERIFIED: pip index]`; uso de `webpush()` / aes128gcm `[CITED: github web-push-libs/pywebpush]`
- GCM desabilitado jun/2024 `[VERIFIED: WebSearch]`

### Tertiary (LOW confidence)
- Mecânica de re-agendamento do arq para avanço por timeout `[ASSUMED — A2/LOW-1]`
- Contrato exato do OSRM self-hosted (perfil/versão do deploy) `[ASSUMED — A1/LOW-4]`
- Fidelidade do fakeredis ao `Lock` real no teste de corrida `[ASSUMED — LOW-2]`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — quase tudo já no `pyproject.toml`; novos pacotes com versões verificadas
- Concorrência (aceite único): HIGH — FOR UPDATE já em produção (Phase 7); `Lock` redis-py documentado
- Privacidade (RN-013): HIGH — model já separa estruturalmente; serializer dedicado
- Orquestração da cascata: MEDIUM — arq existe, mas a mecânica exata de re-agendamento é LOW-1
- OSRM: MEDIUM — contrato público verificado, deploy self-hosted não confirmado (degrada sempre)
- Push: MEDIUM — Web Push VAPID confirmado em integracoes.md; relação com APK/FCM é LOW-3

**Research date:** 2026-06-10
**Valid until:** 2026-07-10 (stack estável; reconfirmar versões de pywebpush/fakeredis se a fase atrasar)
