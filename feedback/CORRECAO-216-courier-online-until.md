# CORRECAO-216 — Entregador: online com prazo + expiração automática

**Data:** 2026-07-08

## Problema
Ao ativar o switch "Online" no app do entregador, ele ficava online indefinidamente sem forma de programar uma saída automática.

## Solução

### Backend

**Migration `0039_courier_online_until.py`**
- Adicionada coluna `online_until DATETIME(tz)` (nullable) na tabela `couriers`

**`couriers/models.py`**
- `online_until: Mapped[datetime | None]` adicionado após `is_online`

**`couriers/schemas.py`**
- `AvailabilityBody`: campo `online_until: datetime | None = None`
- `AvailabilityResponse`: campo `online_until: datetime | None = None`

**`couriers/availability.py`**
- `set_availability()` aceita `online_until`; salva quando `online=True`, limpa quando `online=False`

**`couriers/router.py`**
- Endpoint PATCH passa `online_until` para o service e retorna na resposta

**`workers/lifecycle.py`**
- Nova função `expire_online_couriers()`: single UPDATE sem loop Python
  ```sql
  UPDATE couriers SET is_online=false, online_until=null
  WHERE is_online=true AND online_until <= NOW()
  ```

**`workers/settings.py`**
- Cron registrado: `cron(expire_online_couriers, minute=set(range(0, 60)))` — todo minuto, junto com `absent_timeout`

### Frontend (app do entregador)

**`entregador.service.ts`**
- `AvailabilityResult` agora inclui `online_until: string | null`
- `setAvailability()` aceita `onlineUntil?: string` e envia `online_until` no body

**`inicio.page.ts`**
- `showOnlineModal = signal(false)` + `onlineUntil = signal<Date | null>(null)`
- Ao tocar o toggle para ir online → abre modal (bottom-sheet) perguntando a duração
- Opções: 1h, 2h, 4h, 8h ou "Ficar online sem prazo definido"
- `confirmOnline(hours)` calcula `online_until = now + hours` em ISO e envia
- Indicador "Online até HH:mm" exibido no header quando há prazo
- Ao ir offline → limpa `online_until`
