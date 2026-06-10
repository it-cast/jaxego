# Phase 7: Criação de entrega + máquina de estados (modalidade direta) — Research

**Researched:** 2026-06-10
**Domain:** Máquina de estados transacional (FastAPI/SQLAlchemy/MySQL), criação de entrega (F-03), schema append-only, PII de destinatário (LGPD)
**Confidence:** HIGH (padrões reusáveis já existem no código das Phases 2/4/5/6; o que é novo é modelagem, não tecnologia)

---

<user_constraints>
## User Constraints (from 07-CONTEXT.md)

### Locked Decisions (D-01..D-08)
- **D-01:** Form de nova entrega (tela 12): coleta (pré-preenchida com a loja, editável), entrega (CEP/autocomplete → bairro do catálogo Phase 6), destinatário (nome, telefone E.164), itens (descrição, qtd, valor declarado opcional), observações, método de comprovação (foto default; foto+referência; OTP selecionável mas **DESABILITADO** badge "em breve").
- **D-02:** Forma de pagamento da corrida POR ENTREGA (RN-023): nesta phase **só `direct`** habilitado; `card`/`pix` selecionáveis mas marcados "em breve" (Phase 10). No direto, a entrega nasce sem cobrança online; a taxa de plataforma acumula na fatura mensal (Phase 11).
- **D-03:** Exatamente **7 estados** (CRIADA, ACEITA, COLETADA, ENTREGUE, RECUSADA_NO_DESTINO, CANCELADA, FINALIZADA). Transições SÓ via máquina explícita; transição inválida → **422**. Novo estado exige ADR. Nesta phase a entrega só chega a CRIADA (e CANCELADA pela loja antes do aceite); ACEITA+ vêm nas Phases 8/9, mas a MÁQUINA inteira é definida aqui.
- **D-04:** `delivery_state_transitions` **append-only** (INSERT-only via TRIGGER MySQL como audit_log — RN-012), com timestamp, ator, motivo, GPS quando houver, IP. Trigger nega UPDATE/DELETE.
- **D-05:** Estimativa mostrada à loja = **MEDIANA** das tabelas dos entregadores online elegíveis (cobertura coleta E entrega — Phase 6). Valor final = tabela do entregador que aceitar (Phase 8), nunca acima do teto exibido +10%. `[ASSUMIDO]` — implementar simples.
- **D-06:** Exceção F-03 E2: nenhum entregador online cobre origem E destino → criação **permitida** com aviso "0 entregadores disponíveis agora"; loja decide. Endereço fora da área (E1) → "fora da cobertura" + captura de interesse.
- **D-07:** Loja no limite do plano (Free 2/mês, contador zera dia 1º) → 3ª entrega **bloqueada** com modal de upgrade (sem dark pattern, "agora não" visível). Contador de uso em merchant_subscriptions. Fatura vencida >7 dias bloquearia (RN-025) — fatura é Phase 11; aqui deixar o **gancho**.
- **D-08:** `recipients` — identidade separada do endereço (nome, telefone, email opcional); **hash de CPF** para antifraude (nunca CPF puro). Contadores de entregas/recusas. [LGPD].

### Claude's Discretion
- Biblioteca/abordagem da máquina de estados (enum + tabela de transições válidas vs lib).
- Estrutura exata de `deliveries` (muitos campos — ver entidades.md).
- Como calcular elegíveis para a mediana (reuso da elegibilidade espacial da Phase 6).

### Deferred Ideas (OUT OF SCOPE)
- Despacho/oferta/aceite/cascata (CRIADA → ACEITA) — **Phase 8**.
- Comprovação foto+GPS, COLETADA→ENTREGUE→FINALIZADA, confirmação de pagamento direto, tracking — **Phase 9**.
- Cobrança online cartão/PIX (Safe2Pay split) — **Phase 10**.
- Fatura mensal de taxas + bloqueio por fatura vencida (RN-025) — **Phase 11**.
- OTP de comprovação (RN-007) — pós-M1 (TD-003).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-021 | F-03 criação de entrega (pagamento direto primeiro; cartão/PIX na Phase 10) | §Abordagem técnica (criação F-03), §Standard Stack (Pydantic schema `direct`-only) |
| REQ-022 | 7 estados append-only | §Abordagem técnica (máquina de estados + trigger), padrão `couriers/state_machine.py` + trigger 0002 |
| REQ-023 | Estimativa de frete `[ASSUMIDO RN-030]` | §Abordagem técnica (mediana reusando `is_eligible` + `point_in_polygon` da Phase 6) |
| REQ-011 (parcial) | Limite do plano | §Abordagem técnica (contador em `merchant_subscriptions`, COUNT de deliveries do mês) |
</phase_requirements>

## Summary

Phase 7 é majoritariamente **modelagem + composição de padrões já existentes**, não introdução de tecnologia nova. Os quatro mecanismos centrais — máquina de estados explícita (enum + dict de transições → 422), trigger MySQL append-only, AreaScoped multi-tenant, elegibilidade espacial — já estão implementados e testados nas Phases 2/4/5/6. O trabalho é (a) definir a tabela canônica de transições dos **7 estados** completos (mesmo as que só rodam nas Phases 8/9), (b) modelar `deliveries`/`delivery_state_transitions`/`recipients` na migration 0006, (c) replicar o trigger de `audit_log` em `delivery_state_transitions`, (d) compor a mediana de frete sobre `is_eligible`/`point_in_polygon` da Phase 6, e (e) o gate de limite de plano via COUNT no mês corrente.

O risco de segurança real está concentrado em três pontos: **integridade da máquina** (transição inválida server-side, concorrência de duas transições simultâneas), **imutabilidade do histórico** (trigger — antifraude), e **PII do destinatário** (telefone/endereço fora de log, hash de CPF, RN-013 controlando o que será exposto na Phase 8). A modalidade `direct` simplifica: não há integração de pagamento online nesta phase (zero superfície Safe2Pay).

**Primary recommendation:** Replicar `couriers/state_machine.py` (enum-de-estados + `dict[str, set[str]]` de transições + `assert_transition` → `InvalidTransitionError(422)`) e a função de serviço `transition(...)` que valida e grava em `delivery_state_transitions` com `SELECT ... FOR UPDATE` na linha da entrega (lock pessimista de transição). Trigger append-only idêntico ao da migration 0002. Mediana = compor `is_eligible` (já existe) sobre entregadores online da área, ordenar preços e tirar a mediana. NÃO usar biblioteca de state machine (transitions/python-statemachine): o padrão dict-de-sets do projeto já é o canônico e testado.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Validação de transição de estado | API / Backend | — | Invariante de negócio: cliente nunca decide transição (A04). Cliente só PEDE; servidor valida contra o dict. |
| Persistência append-only do histórico | Database / Storage | API / Backend | Trigger MySQL é a autoridade de integridade (RN-012); o serviço grava, o trigger garante que ninguém edita. |
| Cálculo de mediana de frete | API / Backend | Database (spatial) | Elegibilidade é `ST_Contains` no MySQL; mediana é agregação Python sobre as linhas elegíveis. |
| Gate de limite de plano | API / Backend | Database | COUNT de deliveries do mês contra `deliveries_per_month` do plano; invariante recalculada server-side (A04). |
| Captura de PII do destinatário | API / Backend | Database | Minimização (LGPD): só nome+telefone obrigatórios; CPF opcional e só como hash. Máscara nos outputs. |
| Form de criação (tela 12) | Frontend (Angular) | API | Reactive forms + autocomplete CEP; estimativa exibida vem do backend (frontend é sugestão, não autoridade de preço). |
| Controle do que é exposto ao entregador | API / Backend | — | RN-013: endereço completo do destino NÃO entra no payload de oferta da Phase 8; nota de design registrada aqui. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | já no projeto (Phase 1) | endpoints `/v1/deliveries` | DRV-003; padrão de todas as phases [VERIFIED: codebase apps/api] |
| SQLAlchemy 2.x (async) | já no projeto | ORM, `select().with_for_update()` p/ lock de transição | A03: ORM/parametrizado, nunca f-string [VERIFIED: codebase] |
| Pydantic v2 | já no projeto | schemas de criação com `extra="forbid"`, enums estreitos | A03: validação de entrada; previne mass assignment [CITED: owasp-security A03] |
| Alembic | já no projeto | migration 0006 (deliveries, transitions, recipients) | convenção 0001-0005 [VERIFIED: alembic/versions] |
| MySQL 8 | já no compose | trigger append-only + `ST_Contains` | autoridade de integridade e spatial [VERIFIED: compose tem log_bin_trust_function_creators] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| structlog | já no projeto | logs estruturados (PII mascarada) | toda operação; `mask_phone`/`mask_document` já existem em `core/logging.py` [VERIFIED] |
| hashlib (stdlib) | stdlib | SHA-256 do CPF do destinatário | hash de CPF (D-08); mesmo algoritmo das api_keys (RN-020) [VERIFIED: padrão do projeto] |
| `core/ratelimit.py` (SlidingWindowLimiter) | já no projeto | rate limit de criação de entrega (abuso) | reusar o padrão `signup_limiter` para um `delivery_create_limiter` [VERIFIED] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| dict-de-sets manual | `transitions` / `python-statemachine` (lib) | A lib adiciona dependência e abstração para algo que o projeto já resolve em ~30 linhas testáveis. Padrão `couriers/state_machine.py` é canônico, conhecido pelo plan-checker e trivial de testar exaustivamente. **NÃO adotar lib.** [ASSUMED] |
| Lock pessimista (`FOR UPDATE`) | Lock otimista (coluna `version` + retry) | Pessimista é mais simples e correto para o volume do piloto (Pádua). Otimista evita lock de linha mas exige loop de retry. Ver LOW-1. |
| COUNT por query no mês | Contador denormalizado em `merchant_subscriptions` | COUNT é sempre correto (sem drift); contador denormalizado é mais rápido mas precisa de reset no dia 1º e pode dessincronizar. Ver LOW-3. |

**Installation:** Nenhuma dependência nova. Tudo já está em `apps/api/pyproject.toml` desde a Phase 1.

**Version verification:** Sem pacotes novos a verificar — Phase 7 não adiciona dependências. [VERIFIED: codebase — todos os imports usados já existem]

## Architecture Patterns

### System Architecture Diagram

```
[Loja / tela 12]  POST /v1/deliveries  (Idempotency-Key)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ FastAPI router  (area_scope dep + merchant ownership)    │
│   Pydantic body: payment_method=='direct' (enum estreito)│
└───────┬─────────────────────────────────────────────────┘
        ▼
┌─────────────────────────────────────────────────────────┐
│ delivery service                                         │
│  1. resolve bairro coleta+entrega (catálogo Phase 6)     │
│  2. point_in_polygon → bairro destino  (E1: fora → 422)  │
│  3. limite de plano: COUNT deliveries do mês < plan.dpm  │
│       └─ atingiu → 402/409 upgrade (E4)                  │
│  4. estimativa = MEDIANA(preços de entregadores online   │
│       elegíveis p/ trecho)  ── is_eligible (Phase 6)     │
│       └─ 0 elegíveis → cria com aviso (E2, D-06)         │
│  5. upsert recipient (hash CPF se vier) ── minimização   │
│  6. INSERT delivery (estado CRIADA, courier_id NULL)     │
│  7. transition(None→CRIADA)  ── grava transição inicial  │
└───────┬───────────────────────────────┬─────────────────┘
        ▼                               ▼
   deliveries                  delivery_state_transitions
   (AreaScoped)                (append-only — TRIGGER nega
                                UPDATE/DELETE, RN-012)
        │
        ▼
   entrega CRIADA pronta p/ DESPACHO (Phase 8 consome)
```

A transição é o único caminho de mudança de estado. Cancelamento pela loja (CRIADA→CANCELADA, custo zero RN-004 antes do aceite) passa pela mesma função `transition(...)`.

### Recommended Project Structure
```
apps/api/app/deliveries/
├── __init__.py
├── models.py          # Delivery, DeliveryStateTransition, Recipient
├── state_machine.py   # DELIVERY_TRANSITIONS dict + assert_delivery_transition (espelha couriers/state_machine.py)
├── schemas.py         # CreateDeliveryBody (extra="forbid", payment_method enum), DeliveryOut (PII mascarada)
├── estimate.py        # median_estimate() — compõe is_eligible (Phase 6)
├── service.py         # create_delivery(), transition(), check_plan_limit()
└── router.py          # POST /v1/deliveries, POST /v1/deliveries/{id}/cancel, GET /v1/deliveries
apps/api/alembic/versions/0006_deliveries.py
```

### Pattern 1: Máquina de estados explícita (espelhar o padrão do projeto)
**What:** `dict[str, set[str]]` de transições válidas + `assert_*_transition` que levanta `InvalidTransitionError(422)`. Estados como constantes string.
**When to use:** TODA mudança de estado de entrega — incluindo as que só rodam nas Phases 8/9 (definir a máquina inteira agora, D-03).
**Example:**
```python
# Source: espelha apps/api/app/couriers/state_machine.py [VERIFIED: codebase]
DELIVERY_STATES = (
    "CRIADA", "ACEITA", "COLETADA", "ENTREGUE",
    "RECUSADA_NO_DESTINO", "CANCELADA", "FINALIZADA",
)

# Transições válidas (RN-019). Definir TODAS agora; só CRIADA/CANCELADA são
# exercidas nesta phase, o resto é coberto por testes e habilitado nas Phases 8/9.
DELIVERY_TRANSITIONS: dict[str, set[str]] = {
    "CRIADA": {"ACEITA", "CANCELADA"},                  # Phase 7: cria + cancela pré-aceite (RN-004 custo zero)
    "ACEITA": {"COLETADA", "CANCELADA"},                # Phase 8/9 (cancelamento pós-aceite: 50% RN-004)
    "COLETADA": {"ENTREGUE", "RECUSADA_NO_DESTINO", "CANCELADA"},  # Phase 9
    "ENTREGUE": {"FINALIZADA"},                         # Phase 9 (job 24h)
    "RECUSADA_NO_DESTINO": {"FINALIZADA"},              # Phase 9
    "CANCELADA": set(),                                 # terminal
    "FINALIZADA": set(),                                # terminal
}

class InvalidTransitionError(AppError):
    status_code = 422
    code = "invalid_transition"

def assert_delivery_transition(current: str, target: str) -> None:
    if target not in DELIVERY_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target)
```
> Nota: as transições ACEITA+/cancelamento pós-aceite com custo (RN-004) serão exercidas nas Phases 8/9. A **forma** da máquina é travada aqui; o cálculo de custo de cancelamento (50%/100%) é Phase 9. Confirmar o conjunto exato com o planner — ver Assumptions A1.

### Pattern 2: Função `transition()` com lock de transição
**What:** Carrega a entrega `FOR UPDATE`, valida com `assert_delivery_transition`, atualiza `deliveries.state`, grava 1 linha em `delivery_state_transitions`, registra timestamp por transição.
**When to use:** Único ponto de escrita de estado. Criação chama `transition(delivery, None→"CRIADA")`; cancelamento chama `transition(delivery, "CRIADA"→"CANCELADA", actor, reason)`.
**Example:**
```python
# Source: compõe write_audit (apps/api/app/audit/service.py) + FOR UPDATE [VERIFIED]
async def transition(
    session, *, delivery, to_state, actor_id, reason=None, gps=None, ip=None,
):
    # Lock pessimista da linha da entrega (concorrência — TH-01).
    locked = (await session.execute(
        select(Delivery).where(Delivery.id == delivery.id).with_for_update()
    )).scalar_one()
    assert_delivery_transition(locked.state, to_state)   # 422 se inválida
    from_state = locked.state
    locked.state = to_state
    session.add(DeliveryStateTransition(
        area_id=locked.area_id,
        delivery_id=locked.id,
        from_state=from_state,
        to_state=to_state,
        actor_user_id=actor_id,
        reason=reason,
        gps_lat=gps[0] if gps else None,
        gps_lng=gps[1] if gps else None,
        ip=ip,
        created_at=datetime.now(UTC),   # AWARE — TD-010
    ))
    await session.flush()
```

### Pattern 3: Trigger append-only (replicar migration 0002)
**What:** Dois triggers MySQL `BEFORE UPDATE`/`BEFORE DELETE` em `delivery_state_transitions` que dão `SIGNAL SQLSTATE '45000'`. Emitidos só quando `dialect.name == "mysql"` (guard de dialeto LOW-3 da Phase 2).
**Example:**
```python
# Source: apps/api/alembic/versions/0002_core_auth_multiarea.py [VERIFIED]
_TRG_NO_UPDATE = (
    "CREATE TRIGGER trg_dst_no_update BEFORE UPDATE ON delivery_state_transitions "
    "FOR EACH ROW SIGNAL SQLSTATE '45000' "
    "SET MESSAGE_TEXT = 'delivery_state_transitions is append-only (RN-012)'"
)
# (idem _TRG_NO_DELETE). downgrade dropa os triggers ANTES da tabela.
# log_bin_trust_function_creators=1 já está no compose (RECONCILIATION Phase 2).
```

### Pattern 4: Mediana de frete compondo a elegibilidade da Phase 6
**What:** Encontrar entregadores **online** (`is_online=True`, `status=active`) da área cuja cobertura inclui bairro de coleta E destino (`is_eligible`), coletar o preço de cada um para o trecho, ordenar e tirar a mediana. 0 elegíveis → cria com aviso (E2/D-06).
**Example:**
```python
# Source: compõe apps/api/app/couriers/coverage.py is_eligible [VERIFIED]
def median_cents(prices: list[int]) -> int | None:
    if not prices:
        return None                       # E2: 0 entregadores (D-06)
    s = sorted(prices); n = len(s); m = n // 2
    return s[m] if n % 2 else (s[m-1] + s[m]) // 2   # mediana inteira em centavos
```
> O "preço de cada entregador para o trecho" depende do modo da tabela (por bairro vs por km — `couriers/pricing.py`). Ver LOW-2 para o formato exato.

### Anti-Patterns to Avoid
- **Confiar no estado/preço enviado pelo cliente:** o cliente PEDE criar; servidor decide estado inicial (CRIADA) e calcula a estimativa. Preço final é da tabela do entregador (Phase 8), nunca do payload (A04 — invariante de negócio no backend).
- **UPDATE em `deliveries.state` fora de `transition()`:** burla a máquina e o histórico. Toda mudança de estado passa por `transition()`.
- **CPF puro em `recipients`:** só hash SHA-256 (D-08). CPF cru nunca persiste nem aparece em log/output.
- **Endereço/telefone do destinatário em log:** usar `mask_phone`/`mask_document` (já existem). PII em log = FAIL-BLOCK (A09).
- **Float para dinheiro:** corrida/taxa em **centavos inteiros** (`Integer`), como `plans` (`price_cents`/`fee_cents`). Nunca `Float` para R$.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Máquina de estados | Lib externa (transitions) OU if/elif espalhado | dict-de-sets + `assert_delivery_transition` (padrão `couriers/state_machine.py`) | Já é o canônico do projeto; testável exaustivamente; plan-checker conhece |
| Imutabilidade do histórico | Checagem em código de app | Trigger MySQL `SIGNAL 45000` (migration 0002) | Integridade na camada que ninguém burla; antifraude |
| Isolamento multi-área | `if area_id ==` no corpo | `AreaScopedMixin` + `area_scope` dep + `WHERE area_id` no repo | 3 camadas estruturais já existentes (A01) |
| Elegibilidade espacial | Reimplementar point-in-polygon | `point_in_polygon` + `is_eligible` (Phase 6) | Axis order lat/lng tem um único dono (`neighborhoods/spatial.py`) |
| Mascaramento de PII em log | `email[:2]+"***"` ad-hoc | `mask_phone`/`mask_email`/`mask_document` (`core/logging.py`) | Já existem e são consistentes |
| Rate limit | Contador caseiro novo | `SlidingWindowLimiter` (`core/ratelimit.py`) | Padrão `signup_limiter` reusável |
| Timestamp UTC | `datetime.utcnow()` (naive) | `datetime.now(UTC)` + `UTC_DATETIME` mixin | TD-010 — naive datetime foi lição de campo da v1.0 |

**Key insight:** Phase 7 é 80% composição. A tentação de "buscar a melhor lib de state machine" é o erro — o projeto já tem o padrão, e introduzir abstração nova quebra a uniformidade que o plan-checker e os testes assumem.

## Runtime State Inventory

> Phase 7 é greenfield de schema (cria tabelas novas via migration 0006) — não é rename/refactor/migration de dados existentes. Inventário de estado runtime **não se aplica**.

- Stored data: **None** — só CREATE TABLE novas; nenhum dado existente é renomeado.
- Live service config: **None** — sem integração externa nesta phase (has_external_integration: false).
- OS-registered state: **None**.
- Secrets/env vars: **None** novos — modalidade `direct` não toca Safe2Pay.
- Build artifacts: **None**.

## Security Baseline (OBRIGATÓRIA — Gate 4)

> Fonte: `.claude/skills/owasp-security/SKILL.md` (OWASP Top 10:2025 / ASVS 5.0) + `.claude/skills/br/lgpd-compliance/SKILL.md`. A phase coleta PII do destinatário (nome/telefone/endereço/CPF-hash) e a máquina de estados é crítica para integridade financeira/antifraude → threat model de 15 min obrigatório (A04).

### Threat Model — 8 ameaças

**TH-01 — Integridade da máquina de estados (tampering de transição + concorrência)** → STRIDE: Tampering / Elevation
- *Quem abusa, o que ganha:* loja ou cliente API tenta forçar uma transição inválida (ex.: CRIADA→ENTREGUE pulando aceite/coleta) para fraudar fatura ou histórico; ou duas requisições simultâneas (cancelar + aceitar) causam estado inconsistente.
- *Mitigação (owasp A04 — "invariantes de negócio no backend SEMPRE; frontend é sugestão"):* transição validada **server-side** contra `DELIVERY_TRANSITIONS`; transição inválida → 422 (D-03). O estado-alvo **nunca** vem do cliente como verdade — o servidor decide o estado inicial (CRIADA) e valida cada passo. Concorrência: `SELECT ... FOR UPDATE` na linha da entrega dentro da transação (lock pessimista) garante que duas transições simultâneas serializam — a segunda revalida contra o estado já mudado e falha com 422 se inválida. Teste de corrida obrigatório (mesmo padrão que a Phase 8 fará no aceite).

**TH-02 — Tampering do histórico de transições** → STRIDE: Tampering / Repudiation
- *Quem abusa, o que ganha:* qualquer acesso ao banco (app comprometido, insider) tenta UPDATE/DELETE em `delivery_state_transitions` para apagar prova de fraude (ex.: cancelamento pós-coleta sem pagar).
- *Mitigação (owasp A08 — integridade de dados; RN-012):* trigger MySQL `BEFORE UPDATE`/`BEFORE DELETE` com `SIGNAL SQLSTATE '45000'` (idêntico a `audit_log`, migration 0002). A tabela é **append-only** — a aplicação só faz INSERT. Cada transição grava ator, motivo, timestamp aware-UTC, IP e GPS quando houver (D-04). Teste de aceite: `UPDATE delivery_state_transitions` → erro MySQL 1644.

**TH-03 — IDOR / Broken Access Control em entrega** → STRIDE: Information Disclosure / Elevation
- *Quem abusa, o que ganha:* loja A tenta ler/cancelar entrega da loja B (ou de outra área) enumerando IDs.
- *Mitigação (owasp A01 — "tenant_id no WHERE da query, não em if posterior"; 404 não 403):* `deliveries` é `AreaScopedMixin`; toda query passa por `AreaScopedRepository` (`WHERE area_id`) + checagem de posse pela loja (`merchant_id` do token). Recurso de outra loja/área → **404** (não vaza existência). Cancelamento exige ownership da loja dona. IDs: avaliar ULID/UUID em vez de sequencial para o que é exposto no tracking público (entra de fato na Phase 9, mas decidir o tipo do ID agora — ver A01 "IDs expostos não-sequenciais"). Ver LOW-4.

**TH-04 — Vazamento de PII do destinatário (telefone/endereço)** → STRIDE: Information Disclosure
- *Quem abusa, o que ganha:* PII do destinatário (telefone, endereço completo) vaza por log de aplicação, por output de API a quem não deveria, ou (futuro) ao entregador antes da coleta.
- *Mitigação (owasp A09 — "PII em log = FAIL-BLOCK"; RN-022; LGPD):* telefone/endereço/CPF do destinatário **nunca** em log — usar `mask_phone`/`mask_document` (já existem). Telefones acessíveis às partes **só na janela ACEITA→FINALIZADA** (RN-022) — nesta phase a entrega nasce CRIADA, então o telefone do destinatário **não** é exposto a nenhum entregador ainda. **RN-013** (ver seção dedicada abaixo): endereço completo do destino só após a coleta — a API de criação **guarda** o endereço completo, mas o que será exposto ao entregador na oferta (Phase 8) é só bairro+distância. Redação estrutural via filtro central de logging (A09), não disciplina por chamada.

**TH-05 — CPF do destinatário em claro (antifraude)** → STRIDE: Information Disclosure / Tampering
- *Quem abusa, o que ganha:* CPF do destinatário persistido/exposto em claro vira alvo de vazamento; sem hash, o antifraude (correlacionar recusas por CPF) exigiria CPF cru.
- *Mitigação (owasp A02 — dados sensíveis em repouso; LGPD minimização; D-08):* `recipients` guarda **apenas `cpf_hash` (SHA-256)**, nunca o CPF puro. CPF é **opcional** (minimização — só se a loja quiser antifraude). O hash permite contar recusas por destinatário sem reter o dado identificador cru. CPF nunca em URL (LGPD anti-pattern), nunca em log (mascarar com `mask_document` se algum dia precisar de hint de debug). Hash determinístico para correlação; documentar que não é base para re-identificação.

**TH-06 — Injection (SQL / mass assignment)** → STRIDE: Tampering / Elevation
- *Quem abusa, o que ganha:* payload malicioso na criação tenta SQL injection ou setar campos não previstos (mass assignment: forçar `state`, `courier_id`, `fee_cents`).
- *Mitigação (owasp A03):* TODO acesso via SQLAlchemy ORM / parâmetros nomeados — zero f-string em SQL. Pydantic v2 com `extra="forbid"` no body de criação (campo inesperado → erro, previne mass assignment). `payment_method` é **enum estreito** aceitando só `direct` nesta phase (`card`/`pix` rejeitados com mensagem "em breve"). Campos derivados pelo servidor (`state`, `area_id`, `corrida_cents`, `fee_cents`) **não** vêm do body. Spatial parametrizado (`point_in_polygon` já é A03-safe).

**TH-07 — Abuso de criação (DoS / contorno de limite de plano)** → STRIDE: Denial of Service / Elevation
- *Quem abusa, o que ganha:* loja automatiza criação em massa (custo de geocoding/spatial), ou tenta criar além do limite Free (2/mês) sem pagar.
- *Mitigação (owasp A04 — rate limit derivado do contexto; invariante de quota no backend):* (a) rate limit por loja no endpoint de criação reusando `SlidingWindowLimiter` (`core/ratelimit.py`) — derivar o número no PLAN ("ex.: 30/min por loja porque pico legítimo de uma loja movimentada é ~X"); (b) limite de plano: COUNT de deliveries da loja no mês corrente `< plan.deliveries_per_month` recalculado **server-side** (não confiar no contador do cliente) → 3ª no Free bloqueada (402/409 com payload de upgrade, D-07). Gancho de fatura vencida >7 dias (RN-025) deixado como ponto de extensão (Phase 11) — documentar, não implementar.

**TH-08 — LGPD (minimização, base legal, retenção)** → STRIDE: Information Disclosure / Compliance
- *Quem abusa, o que ganha:* coleta excessiva de PII do destinatário sem base legal vira passivo LGPD; histórico de entrega retém PII além do necessário.
- *Mitigação (LGPD skill — minimização, base legal por campo, RN-021):* coletar **mínimo** — nome + telefone obrigatórios (necessários para a entrega = base legal **execução de contrato**); email e CPF **opcionais**. Base legal documentada por campo no PLAN (checklist LGPD). RN-021: `deliveries` nunca é deletada — **anonimizada** após 12 meses (gancho do job da Phase 14; aqui só garantir que os campos PII sejam anonimizáveis — separados em `recipients` ajuda). Endereço do destino é PII vinculada à finalidade da entrega. Política de retenção declarada no PLAN.

### Resumo de mapeamento ASVS / OWASP

| Ameaça | OWASP | Mitigação (citação) | Verificação no plano |
|--------|-------|---------------------|----------------------|
| TH-01 | A04 | invariante server-side + FOR UPDATE | teste exaustivo de transições inválidas + teste de corrida |
| TH-02 | A08 / RN-012 | trigger SIGNAL 45000 | `UPDATE delivery_state_transitions` → erro MySQL |
| TH-03 | A01 | AreaScoped + ownership + 404 | query cross-loja/área → 404 |
| TH-04 | A09 / RN-013/022 | máscara + janela ACEITA→FINALIZADA | grep PII em logs = 0; telefone não exposto em CRIADA |
| TH-05 | A02 / D-08 | só cpf_hash SHA-256 | nenhum CPF cru no banco/output |
| TH-06 | A03 | ORM + Pydantic `extra="forbid"` + enum | payload com campo extra → 422; `payment_method=card` → "em breve" |
| TH-07 | A04 | rate limit + limite de plano server-side | 3ª entrega Free → bloqueio com upgrade |
| TH-08 | LGPD | minimização + base legal + anonimização | base legal por campo no PLAN; campos anonimizáveis |

## RN-013 — Privacidade do endereço do destino (nota de design para Phase 8)

**Regra (RN-013):** *"Endereço completo do destino só é revelado ao entregador APÓS a coleta confirmada. Antes: bairro + distância estimada."*

**O que Phase 7 faz:**
- A API de criação **persiste o endereço completo do destino** em `deliveries` (necessário para a entrega acontecer; base legal: execução de contrato).
- A entrega nasce **CRIADA** — nenhum entregador tem vínculo (`courier_id` é NULL até o aceite na Phase 8). Portanto, **nesta phase nenhum endereço de destino é exposto a entregador** — não há entregador na entrega ainda.
- O `DeliveryOut` (output da API) para a **loja** pode conter o endereço completo (a loja é quem digitou — é dona do dado). Para qualquer superfície de entregador (que só existirá na Phase 8), o contrato deve expor **apenas bairro + distância**.

**Nota de design registrada para Phase 8 (despacho):**
- O payload da **oferta** ao entregador (Phase 8, F-05) **NÃO pode** conter o endereço completo do destino — só `bairro_destino` + `distancia_estimada` (o ROADMAP da Phase 8 já lista "teste de contrato: payload de oferta sem endereço completo do destino — RN-013").
- Recomendação: ao modelar `deliveries` agora, separar claramente os campos de **endereço completo** (rua/número/complemento) dos campos **revelados antes da coleta** (`dropoff_neighborhood_id`, `distance_m`). Isso facilita o serializer da Phase 8 a montar a oferta sem o endereço completo por construção (não por filtro esquecível).
- O endereço completo só entra no contrato do entregador **após** a transição que marca a coleta (COLETADA — Phase 9).

**Ação nesta phase:** documentar a fronteira no PLAN e modelar `deliveries` com a separação acima. NÃO implementar o serializer de oferta (Phase 8).

## Common Pitfalls

### Pitfall 1: Definir só as transições desta phase
**What goes wrong:** Modelar apenas CRIADA→CANCELADA e deixar o resto para depois.
**Why it happens:** Escopo desta phase só exercita CRIADA/CANCELADA.
**How to avoid:** D-03 manda definir a **máquina inteira (7 estados)** agora, com testes exaustivos das transições inválidas — mesmo as exercidas nas Phases 8/9. A forma é travada aqui; novo estado exige ADR.
**Warning signs:** `DELIVERY_TRANSITIONS` com menos de 7 chaves.

### Pitfall 2: Naive datetime nos timestamps de transição (TD-010)
**What goes wrong:** `datetime.utcnow()` grava naive; comparações futuras misturam naive/aware e quebram (lição de campo da v1.0).
**How to avoid:** `datetime.now(UTC)` em todo timestamp; colunas via `UTC_DATETIME` mixin; ler de volta com `ensure_aware_utc` quando comparar. Padrão já estabelecido em `audit/service.py`, `coverage.py`, `pricing.py`.
**Warning signs:** qualquer `utcnow()` / `replace(tzinfo=None)` no diff.

### Pitfall 3: Trigger não nasce em produção (errno 1419)
**What goes wrong:** Em MySQL 8 com binlog, usuário de app sem SUPER não cria trigger sem `log_bin_trust_function_creators=1`.
**Why it happens:** Foi exatamente o bug pego no live da Phase 2 (RECONCILIATION).
**How to avoid:** A flag **já está** no serviço mysql do compose (corrigido na Phase 2). Para o VPS de produção, garantir a mesma flag. Guard de dialeto: trigger só em `dialect.name == "mysql"` (SQLite não tem o trigger; testes de integridade são `@pytest.mark.mysql`).

### Pitfall 4: Dinheiro em Float
**What goes wrong:** `corrida`/`taxa`/`distância×preço` em Float acumula erro de centavo.
**How to avoid:** Centavos inteiros (`Integer`) como `subscription_plans.price_cents`/`fee_cents`. Mediana retorna centavos inteiros.
**Warning signs:** `Float` em coluna de valor monetário.

### Pitfall 5: Contador de plano que dessincroniza
**What goes wrong:** Contador denormalizado em `merchant_subscriptions` que esquece de zerar dia 1º ou conta entregas canceladas.
**How to avoid:** Preferir COUNT por query no mês corrente (`WHERE merchant_id AND created_at >= início_do_mês`) — sempre correto. Decidir se entrega CANCELADA conta para o limite (recomendação: não conta, pois RN-004 custo zero pré-aceite). Ver LOW-3.

## Code Examples

### Hash de CPF do destinatário (D-08)
```python
# Source: padrão SHA-256 do projeto (api_keys RN-020) [VERIFIED: codebase usa hashlib]
import hashlib

def hash_cpf(cpf_digits: str) -> str:
    """SHA-256 do CPF normalizado (só dígitos). NUNCA persistir o CPF cru."""
    return hashlib.sha256(cpf_digits.encode()).hexdigest()
# Recipient guarda apenas cpf_hash; CPF cru é descartado após o hash.
```

### Schema de criação `direct`-only com extra="forbid" (TH-06)
```python
# Source: owasp A03 (extra="forbid", enum estreito) [CITED: owasp-security A03]
from enum import Enum
from pydantic import BaseModel, ConfigDict

class PaymentMethod(str, Enum):
    direct = "direct"          # Phase 7: único habilitado (D-02)
    card = "card"              # "em breve" (Phase 10) — aceito no enum, rejeitado na regra
    pix = "pix"               # idem

class CreateDeliveryBody(BaseModel):
    model_config = ConfigDict(extra="forbid")   # mass-assignment guard
    # state / area_id / corrida_cents / fee_cents NÃO entram aqui (derivados pelo servidor)
    payment_method: PaymentMethod
    # ... endereços, destinatário, itens
    # validação de regra: if payment_method != direct → 422 "em breve" (D-02)
```

### Limite de plano (TH-07 / D-07)
```python
# Source: compõe plans/service.get_plan_by_code + COUNT server-side [VERIFIED]
async def deliveries_this_month(session, *, merchant_id, area_id) -> int:
    start = month_start_utc(datetime.now(UTC))   # AWARE — TD-010
    stmt = select(func.count(Delivery.id)).where(
        Delivery.area_id == area_id,
        Delivery.merchant_id == merchant_id,
        Delivery.created_at >= start,
        # decidir: excluir CANCELADA do count (recomendação: sim) — ver LOW-3
    )
    return (await session.execute(stmt)).scalar_one()
# se >= plan.deliveries_per_month e not plan.is_unlimited → 402/409 upgrade (sem dark pattern)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Lib de state machine (transitions) | dict-de-sets explícito (padrão do projeto) | estabelecido nas Phases 4/5 | menos dependência, testável, uniforme |
| `datetime.utcnow()` naive | `datetime.now(UTC)` aware (TD-010) | lição de campo v1.0 | evita bug naive/aware |
| Integridade em código de app | trigger MySQL `SIGNAL` | Phase 2 (audit_log) | integridade na camada inviolável |

**Deprecated/outdated:**
- Não usar `datetime.utcnow()` (deprecado no Python 3.12+ e naive). Usar `datetime.now(UTC)`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Conjunto exato de transições válidas (especialmente quem pode ir a CANCELADA e de onde) conforme RN-004/RN-019 | Pattern 1 | Máquina permissiva/restritiva demais; novo estado/transição exigiria ADR. Confirmar com planner contra fluxos F-05/F-06. |
| A2 | NÃO usar lib de state machine — dict-de-sets é o canônico | Standard Stack / Alternatives | Baixo: é o padrão já adotado e testado |
| A3 | Mediana simples (inteiro em centavos) é suficiente (RN-030 é `[ASSUMIDO]`, TD-009) | Pattern 4 | Estimativa imprecisa; mitigado pela regra do teto +10% no aceite (Phase 8) |
| A4 | Cancelamento de entrega CANCELADA não conta para o limite Free | Pitfall 5 / Code Examples | Loja poderia criar+cancelar para burlar contagem se contar errado |

## Open Questions

1. **Tipo do ID exposto (sequencial vs ULID/UUID)** — owasp A01 recomenda IDs não-sequenciais para recursos expostos. O tracking público (Phase 9) exporá um identificador de entrega.
   - What we know: padrão atual do projeto usa BIGINT autoincrement (PK interno).
   - What's unclear: se a entrega precisa de um `public_token` separado (ULID) já nesta phase ou só na Phase 9.
   - Recommendation: modelar `deliveries` com PK BIGINT interno + considerar um `public_token` (ULID) opaco para o tracking — decidir na Phase 9, mas reservar a coluna agora se barato. → vira task ou TD (Regra 12). Ver LOW-4.

2. **Formato da estimativa quando entregadores têm modos de tabela diferentes (bairro vs km)** — como normalizar o "preço para o trecho" entre um entregador que cobra por bairro e outro por km.
   - Recommendation: para a mediana, computar o preço efetivo de cada entregador para o trecho específico (bairro de destino conhecido; distância conhecida) e tirar a mediana dos efetivos. → task explícita no PLAN. Ver LOW-2.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| MySQL 8 | trigger append-only + `ST_Contains` | ✓ (compose) | 8.x | SQLite p/ testes não-spatial (`@pytest.mark.mysql` para os de integridade) |
| `log_bin_trust_function_creators=1` | criação de trigger pelo user de app | ✓ (já no compose, fix Phase 2) | — | garantir no VPS de produção |
| shapely | validação de polígono (reuso Phase 6) | ✓ | já instalado | — |

**Missing dependencies with no fallback:** Nenhuma — Phase 7 não adiciona dependência.
**Missing dependencies with fallback:** Testes de trigger e spatial exigem MySQL live (já é o padrão do projeto).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (já no projeto) |
| Config file | `apps/api/pyproject.toml` / `pytest.ini` (Phase 1) |
| Quick run command | `uv run pytest apps/api/tests/deliveries -x` |
| Full suite command | `uv run pytest && uv run ruff check .` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-022 | Toda transição inválida → 422 (exaustivo) | unit | `pytest tests/deliveries/test_state_machine.py -x` | ❌ Wave 0 |
| REQ-022 | UPDATE/DELETE em transitions → erro MySQL | integration (mysql) | `pytest -m mysql tests/deliveries/test_append_only.py -x` | ❌ Wave 0 |
| REQ-021 | F-03 cria entrega CRIADA (direct) | integration | `pytest tests/deliveries/test_create.py -x` | ❌ Wave 0 |
| REQ-021 | `payment_method=card` → 422 "em breve" | unit | `pytest tests/deliveries/test_create.py::test_card_em_breve -x` | ❌ Wave 0 |
| REQ-023 | Mediana de frete sobre elegíveis (E2: 0 → aviso) | unit | `pytest tests/deliveries/test_estimate.py -x` | ❌ Wave 0 |
| REQ-011 | 3ª entrega Free → bloqueio upgrade | integration | `pytest tests/deliveries/test_plan_limit.py -x` | ❌ Wave 0 |
| TH-01 | 2 transições simultâneas → 1 vence (lock) | integration (mysql) | `pytest -m mysql tests/deliveries/test_concurrency.py -x` | ❌ Wave 0 |
| TH-03 | Query cross-loja/área → 404 | integration | `pytest tests/deliveries/test_isolation.py -x` | ❌ Wave 0 |
| TH-04 | PII do destinatário não aparece em log | unit | `pytest tests/deliveries/test_pii_masking.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest apps/api/tests/deliveries -x`
- **Per wave merge:** `uv run pytest && uv run ruff check .`
- **Phase gate:** Full suite green antes de `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/deliveries/test_state_machine.py` — transições válidas + exaustivo das inválidas (REQ-022)
- [ ] `tests/deliveries/test_append_only.py` — trigger UPDATE/DELETE (REQ-022, `@pytest.mark.mysql`)
- [ ] `tests/deliveries/test_create.py` — F-03 happy path + card/pix "em breve" (REQ-021)
- [ ] `tests/deliveries/test_estimate.py` — mediana + E2 0 elegíveis (REQ-023)
- [ ] `tests/deliveries/test_plan_limit.py` — limite Free (REQ-011)
- [ ] `tests/deliveries/test_concurrency.py` — corrida de transição (TH-01, `@pytest.mark.mysql`)
- [ ] `tests/deliveries/test_isolation.py` — IDOR/área (TH-03)
- [ ] `tests/deliveries/test_pii_masking.py` — PII fora de log (TH-04)
- [ ] `tests/deliveries/conftest.py` — fixtures de entrega/destinatário/entregador online elegível

## Sources

### Primary (HIGH confidence)
- `apps/api/app/couriers/state_machine.py`, `merchants/state_machine.py` — padrão canônico de máquina de estados (dict-de-sets + 422) [VERIFIED: codebase]
- `apps/api/alembic/versions/0002_core_auth_multiarea.py` — trigger append-only `SIGNAL 45000` (RN-012) [VERIFIED]
- `apps/api/app/db/mixins.py` — `AreaScopedMixin`, `UTC_DATETIME`, `ensure_aware_utc` (TD-010) [VERIFIED]
- `apps/api/app/couriers/coverage.py` (`is_eligible`), `neighborhoods/spatial.py` (`point_in_polygon`) — elegibilidade espacial Phase 6 [VERIFIED]
- `apps/api/app/plans/service.py`, `merchants/models.py` — planos + `merchant_subscriptions` (limite) [VERIFIED]
- `apps/api/app/audit/service.py`, `core/logging.py` — `write_audit`, `mask_phone`/`mask_document` [VERIFIED]
- `apps/api/app/core/ratelimit.py` — `SlidingWindowLimiter` reusável [VERIFIED]
- `.claude/skills/owasp-security/SKILL.md` — A01/A02/A03/A04/A08/A09 (fonte do Security Baseline) [CITED]
- `.claude/skills/br/lgpd-compliance/SKILL.md` — minimização, base legal, retenção [CITED]
- `projeto/regras-negocio/regras.md` — RN-012/013/019/022/023/028/030 [CITED]
- `projeto/regras-negocio/entidades.md` §Transacional — deliveries/transitions/recipients [CITED]

### Secondary (MEDIUM confidence)
- `.planning/phases/02-.../RECONCILIATION.md` — bug do trigger (errno 1419 / log_bin_trust_function_creators) [VERIFIED: doc do projeto]

### Tertiary (LOW confidence)
- RN-030 mediana e formato exato — `[ASSUMIDO]` na origem (TD-009), confirmar abordagem simples [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero dependência nova; tudo já no codebase
- Architecture (máquina/trigger/AreaScoped/spatial): HIGH — padrões implementados e testados nas Phases 2/4/5/6
- Security Baseline: HIGH — mitigações mapeiam para padrões já existentes (trigger, AreaScoped, máscaras, rate limit)
- Pitfalls: HIGH — todos observados/corrigidos em campo no próprio projeto
- Mediana de frete (RN-030): MEDIUM — regra `[ASSUMIDO]`; abordagem simples recomendada mas formato exato é LOW (LOW-2)
- Concorrência de transição: MEDIUM — lock pessimista recomendado; otimista é alternativa (LOW-1)

**LOW confidence items (Regra 12 → viram task ou TD no PLAN):**
- **LOW-1:** Estratégia de concorrência na transição (lock pessimista `FOR UPDATE` vs otimista por `version`). Recomendação: pessimista nesta phase (Redis lock é mais relevante no aceite da Phase 8, ADR-104). → task explícita com critério de aceite (teste de corrida) OU TD com `urgency_class: pre_launch_high`.
- **LOW-2:** Formato exato do "preço para o trecho" na mediana quando entregadores misturam modo bairro/km. → task explícita no PLAN com critério verificável.
- **LOW-3:** COUNT por query vs contador denormalizado em `merchant_subscriptions`; e se CANCELADA conta para o limite. Recomendação: COUNT por query, CANCELADA não conta. → task ou TD.
- **LOW-4:** Índices de `deliveries` (mínimo: `(area_id, merchant_id, created_at)` p/ COUNT do limite e lista da tela 14; `(area_id, state)` p/ despacho Phase 8) e tipo de ID exposto (BIGINT interno + `public_token` ULID para tracking Phase 9). → task/TD.

**Research date:** 2026-06-10
**Valid until:** 2026-07-10 (stack estável, interno ao projeto)
