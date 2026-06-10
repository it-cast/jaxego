# Push Notifications Architecture — APNs/FCM, opt-in UX, deep linking

> Skill obrigatória para fases que introduzem push mobile. Decisões mal tomadas aqui causam opt-out em massa e degradação de retenção.

## Princípio central

Push é privilégio, não direito. Cada notificação gasta goodwill do usuário. Enviar demais = opt-out permanente. Enviar pouco e certeiro = canal de alta conversão. Arquitetura deve facilitar o certeiro, não o "mandar tudo pra todo mundo".

## Stack

### iOS
- **APNs** (Apple Push Notification service) via certificado ou token
- Token recomendado (rotação mais simples)

### Android
- **FCM** (Firebase Cloud Messaging) — também roteia para iOS, simplifica backend
- Endpoint único HTTP v1

### Orquestração recomendada
- **FCM como broker** unificado (envia para iOS e Android)
- **OneSignal / Airship / Braze** como alternativa enterprise (UI de campanha, segmentação)
- Para time pequeno: FCM cru + backend próprio é suficiente

## Token lifecycle

### Registro

```typescript
// mobile/src/services/push.service.ts
import { PushNotifications, Token } from '@capacitor/push-notifications';

async init(userId: string) {
  // 1. Solicitar permissão (timing crítico — ver "Opt-in UX")
  const perm = await PushNotifications.requestPermissions();
  if (perm.receive !== 'granted') {
    return this.handleDenied();
  }
  
  // 2. Registrar com APNs/FCM
  await PushNotifications.register();
  
  // 3. Receber token FCM e enviar pro backend
  PushNotifications.addListener('registration', async (token: Token) => {
    await this.api.post('/api/v1/devices/register', {
      fcm_token: token.value,
      platform: Capacitor.getPlatform(),  // 'ios' | 'android'
      app_version: env.appVersion,
      os_version: await Device.getInfo().then(i => i.osVersion),
    });
  });
  
  // 4. Handler de erro de registro
  PushNotifications.addListener('registrationError', (error) => {
    Sentry.captureException(new Error(`Push registration failed: ${error.error}`));
  });
}
```

### Refresh

Token pode mudar (reinstalação, restore, etc). Registrar novamente **a cada abertura do app**:

```typescript
// Idempotente — backend deduplica por (user_id, fcm_token)
await this.push.init(user.id);
```

Backend:
```python
@router.post("/devices/register")
async def register_device(body: DeviceRegisterBody, user: CurrentUser):
    # Upsert — mesmo device registrado novamente atualiza metadata
    await db.execute(
        """INSERT INTO user_devices (user_id, fcm_token, platform, app_version, os_version, last_seen_at)
           VALUES (:user_id, :token, :platform, :app_version, :os_version, NOW())
           ON CONFLICT (user_id, fcm_token) DO UPDATE
           SET platform = :platform, app_version = :app_version,
               os_version = :os_version, last_seen_at = NOW()""",
        {...}
    )
```

### Expiração

Tokens invalidados (user desinstalou, reset device) causam FCM retornar `UNREGISTERED` no envio. Backend remove do banco:

```python
async def send_push(user_id: UUID, payload: PushPayload):
    devices = await db.fetch("SELECT * FROM user_devices WHERE user_id = $1", user_id)
    for d in devices:
        try:
            await fcm.send(token=d.fcm_token, ...)
        except FcmUnregisteredError:
            await db.execute("DELETE FROM user_devices WHERE id = $1", d.id)
        except FcmError as e:
            logger.warning("push_send_failed", device_id=d.id, error=str(e))
```

## Opt-in UX

### Nunca pedir ao abrir o app

```typescript
// ❌ no app.component onInit
await PushNotifications.requestPermissions();
```

Usuário sem contexto → "Não" 70% das vezes. iOS e Android não dão segunda chance fácil.

### Pedir no momento certo

Contextual, após valor entregue:

```typescript
// Após primeira ação significativa do usuário
async onFirstOrderCompleted() {
  // Primeiro: pré-prompt na UI (próprio do app, não modal do sistema)
  const shouldAsk = await this.modalService.show({
    title: 'Avisar quando seu pedido chegar?',
    body: 'Enviamos uma notificação quando o pedido for confirmado e sai para entrega.',
    cta: 'Sim, avisar',
    secondary: 'Agora não',
  });
  
  // Só se aceitar, mostra o prompt nativo
  if (shouldAsk === 'primary') {
    await PushNotifications.requestPermissions();
  }
  // Se recusou o pré-prompt, não mostra o nativo — preserva chance futura
}
```

Bons momentos:
- Após primeira ação de valor (primeiro pedido, primeira mensagem, conclusão de onboarding)
- Antes de funcionalidade que depende (ex: "ativar lembrete")
- Em contexto claro: "seu pedido está a caminho — quer atualizações?"

Maus momentos:
- Primeira tela do app
- Em onboarding antes de qualquer valor
- Toda vez que abre (não insistir)

### Se user recusou

- **Não implorar** — respeitar
- Oferecer canal alternativo (email, SMS, in-app)
- Mostrar "Ativar notificações" nas configurações do app para usuários que mudarem de ideia

## Categorização de notificações

Agrupar por tipo permite:
- User desabilitar **apenas marketing**, manter transacionais
- Backend aplicar rate limit por categoria
- Métricas separadas (CTR, conversão por categoria)

### Categorias sugeridas

| Categoria | Prioridade | Rate limit / user | Exemplo |
|-----------|------------|---------------------|---------|
| **Transactional** | alta | sem limite (mas dedup) | "Pedido confirmado", "Pagamento aprovado" |
| **Actionable** | alta | 5/dia | "Nova mensagem", "Alguém respondeu" |
| **Informational** | média | 2/dia | "Novo recurso disponível" |
| **Marketing** | baixa | 1/semana, opt-in separado | "Promoção de Black Friday" |
| **Silent** | sistema | ilimitado | Atualizar dados em background |

Payload inclui categoria:
```json
{
  "notification": { "title": "...", "body": "..." },
  "data": {
    "category": "actionable",
    "event_type": "message.new",
    "deep_link": "app://conversations/abc123"
  }
}
```

### Android — Notification Channels

Obrigatório no Android 8+:

```typescript
// app.module.ts ou bootstrap
await PushNotifications.createChannel({
  id: 'transactional',
  name: 'Transações',
  description: 'Confirmações de pedidos, pagamentos e alterações de status',
  importance: 4,  // IMPORTANCE_HIGH
  visibility: 1,
  sound: 'default',
  vibration: true,
});

await PushNotifications.createChannel({
  id: 'marketing',
  name: 'Promoções e novidades',
  description: 'Ofertas, promoções e novidades do app',
  importance: 2,  // IMPORTANCE_LOW
  sound: null,
  vibration: false,
});
```

User desabilita canal específico em settings → não incomoda com marketing, mantém transacional.

### iOS — Rich notifications

```json
{
  "aps": {
    "alert": {"title": "Pedido a caminho", "body": "Chegada prevista em 15 min"},
    "sound": "default",
    "mutable-content": 1,
    "category": "ORDER_UPDATE"
  },
  "image_url": "https://cdn.app.com/orders/abc/preview.jpg",
  "data": {
    "deep_link": "app://orders/abc"
  }
}
```

Com `mutable-content: 1`, Notification Service Extension (Swift) baixa imagem e anexa antes de exibir.

## Deep linking

Notificação **sempre** leva a lugar específico, não à home do app.

### Schema

```
app://orders/abc123
app://conversations/xyz/messages
app://profile
```

### Handler universal

```typescript
PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
  const deepLink = action.notification.data?.deep_link;
  if (deepLink) {
    this.navService.navigateByDeepLink(deepLink);
  }
});

// src/core/nav.service.ts
navigateByDeepLink(link: string) {
  const url = new URL(link);
  const parts = url.pathname.split('/').filter(Boolean);
  
  switch (url.host) {
    case 'orders':
      this.router.navigate(['/orders', parts[0]]);
      break;
    case 'conversations':
      this.router.navigate(['/conversations', parts[0]], { queryParams: { focus: parts[1] } });
      break;
    // ...
  }
}
```

### Universal Links (iOS) / App Links (Android)

Para abrir via URL web:
- `https://app.acme.com/orders/abc` abre o app se instalado
- Configuração: `apple-app-site-association` (iOS), `assetlinks.json` (Android)
- Fallback: se app não instalado, abre web

## Silent push (background sync)

Sem UI — apenas acorda o app para atualizar dados:

```json
// iOS
{
  "aps": {"content-available": 1},
  "data": {"sync_type": "orders_updated"}
}

// Android
{
  "data": {"sync_type": "orders_updated"}
}
```

Casos de uso:
- Invalidar cache local quando dados mudam no servidor
- Badge de contador sem notificação visível
- Refresh de dados críticos em background

Limite iOS: ~3 silent push por hora por app (Apple aplica).

## Backend: fila de envio

Nunca enviar push direto do endpoint HTTP:

```python
# ❌ bloqueia resposta, sem retry
@router.post("/orders/confirm")
async def confirm(order_id):
    await confirm_order(order_id)
    await send_push(user_id, ...)  # bloqueia
    return {"ok": True}

# ✅ fila async
@router.post("/orders/confirm")
async def confirm(order_id):
    await confirm_order(order_id)
    await queue.enqueue('send_order_confirmation_push', order_id=order_id)
    return {"ok": True}

# worker
async def send_order_confirmation_push(order_id: UUID):
    order = await db.get_order(order_id)
    user = await db.get_user(order.user_id)
    devices = await db.get_user_devices(user.id)
    
    payload = PushPayload(
        title=t('push.order.confirmed.title', locale=user.locale),
        body=t('push.order.confirmed.body', locale=user.locale, order_id=str(order_id)[:8]),
        category='transactional',
        deep_link=f'app://orders/{order_id}',
        idempotency_key=f'order_confirmed:{order_id}',
    )
    
    for device in devices:
        await fcm.send(token=device.fcm_token, payload=payload.to_fcm())
```

### Idempotency

Dedup para evitar duplicatas em retry:

```python
async def send_with_dedup(user_id: UUID, payload: PushPayload):
    dedup_key = f"push:sent:{user_id}:{payload.idempotency_key}"
    if await redis.exists(dedup_key):
        return
    await redis.setex(dedup_key, 86400, "1")
    await fcm.send(...)
```

### Métricas

Loggar cada envio:
```python
logger.info("push_sent",
  user_id=str(user_id),
  category=payload.category,
  event_type=payload.event_type,
  platform=device.platform,
  notification_id=str(payload.id),
)
```

Frontend loga recebimento + clique:
```typescript
PushNotifications.addListener('pushNotificationReceived', (notif) => {
  analytics.track('push_received', { id: notif.data.notification_id, category: notif.data.category });
});
PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
  analytics.track('push_clicked', { id: action.notification.data.notification_id });
});
```

Dashboard: delivered / opened / clicked / converted por categoria.

## Localização

Título e corpo no locale do usuário (guardado no `user.locale`):

```python
title = t('push.message.new.title', locale=user.locale, sender_name=sender.name)
# pt-BR: "{sender_name} te mandou uma mensagem"
# en-US: "{sender_name} sent you a message"
```

Nunca hardcode.

## Timing

Não mandar push às 3h da manhã salvo transacional crítica. Respeitar timezone do usuário:

```python
async def should_send_now(user: User, category: str) -> bool:
    if category == 'transactional':
        return True  # sempre, sem limitação de horário
    
    local_time = datetime.now(tz=ZoneInfo(user.timezone or 'America/Sao_Paulo'))
    if local_time.hour < 8 or local_time.hour >= 22:
        if category == 'marketing':
            return False  # nunca de noite
        if category in ('informational',):
            # postergar para 9h
            await schedule_for(user, category, local_time.replace(hour=9, minute=0))
            return False
    return True
```

## Testing

### Unit
```python
def test_push_payload_has_deep_link():
    p = build_order_confirmed_payload(order)
    assert p.deep_link.startswith('app://orders/')
    assert p.category == 'transactional'
```

### Integration
```python
async def test_order_confirmation_enqueues_push(client, db):
    order = await create_order()
    await client.post(f"/orders/{order.id}/confirm")
    jobs = await queue.list_jobs()
    assert any(j.name == 'send_order_confirmation_push' for j in jobs)
```

### Device real
- FCM permite ambiente de teste
- iOS TestFlight + sandbox APNs
- Checklist manual por release: envia teste → chega no device → deep link abre tela certa

## Anti-patterns

- Pedir permissão ao abrir o app pela primeira vez
- Pedir de novo após recusa (desrespeito)
- Título genérico: "Você tem uma notificação"
- Corpo sem contexto: "Algo aconteceu"
- Deep link para home em vez de recurso específico
- Todas as notificações em um canal Android (usuário não pode silenciar marketing sem perder transacional)
- Marketing às 3h da manhã
- Sem métricas por categoria (não sabe o que funciona)
- Push como única forma de entrega (e se user negou?) — sempre ter fallback in-app
- Payload com PII em cleartext — tokens FCM vazam às vezes, nunca colocar dados sensíveis
- Sem fila + retry — falha silenciosa em produção

## Checklist para PLAN.md

- [ ] Registro de token idempotente (roda em toda abertura)
- [ ] Pré-prompt UI antes do prompt nativo
- [ ] Pedido contextual, após valor entregue
- [ ] Categorias definidas no backend (transactional/actionable/informational/marketing)
- [ ] Notification Channels criados no Android
- [ ] Deep link em TODA notificação
- [ ] Handler de deep link testado nas rotas principais
- [ ] Fila backend com idempotency + retry
- [ ] Localização do título/corpo por `user.locale`
- [ ] Respeito ao timezone do usuário (não marketing à noite)
- [ ] Silent push apenas para casos justificados
- [ ] Métricas: sent / delivered / opened / clicked por categoria
- [ ] Tokens inválidos removidos automaticamente do banco
- [ ] Zero PII em payload
- [ ] Fallback in-app para users que negaram permissão
