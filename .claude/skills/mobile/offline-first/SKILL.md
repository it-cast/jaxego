# Offline-First Mobile — queue, cache, sync, UX de rede intermitente

> Skill obrigatória para qualquer app mobile operando em condições reais (profissional em obra, usuário em metrô, turista com sinal fraco).

## Princípio central

Rede não é uma garantia. Tratar "online" como estado default e "offline" como erro é raiz de bugs de UX. **Offline é estado normal** — o app precisa funcionar degradadamente, enfileirar ações, sincronizar quando voltar, e ser transparente sobre o que não funciona sem rede.

Hierarquia de degradação:
1. **Read-only totalmente offline** — últimas listas, últimos detalhes, cache local
2. **Write enfileirado** — ação salva local, processada ao reconectar
3. **Write bloqueado com modal explicativo** — para operações sensíveis (pagamento, confirmação crítica)

## Detecção de conectividade

### NÃO confiar apenas em `navigator.onLine`

`navigator.onLine` retorna `true` mesmo com Wi-Fi sem internet real. Detecção robusta combina:

```typescript
// services/network.service.ts
import { Network } from '@capacitor/network';

export class NetworkService {
  private status$ = new BehaviorSubject<NetworkStatus>({ connected: true, type: 'unknown' });
  
  async init() {
    // Capacitor nativo (mais preciso que navigator.onLine)
    const nativeStatus = await Network.getStatus();
    this.status$.next(nativeStatus);
    
    Network.addListener('networkStatusChange', (s) => {
      this.status$.next(s);
      if (s.connected) this.onReconnect();
    });
    
    // Ping real a cada 30s quando "connected" mas suspeito
    setInterval(() => this.verifyRealConnectivity(), 30000);
  }
  
  private async verifyRealConnectivity() {
    if (!this.status$.value.connected) return;
    try {
      const ctrl = new AbortController();
      setTimeout(() => ctrl.abort(), 3000);
      const r = await fetch(`${env.apiBase}/healthz`, { signal: ctrl.signal });
      if (!r.ok) this.status$.next({ connected: false, type: 'none' });
    } catch {
      this.status$.next({ connected: false, type: 'none' });
    }
  }
  
  get isOnline$() { return this.status$.pipe(map(s => s.connected)); }
  get isOnline() { return this.status$.value.connected; }
  
  private async onReconnect() {
    await this.queueService.processAll();
  }
}
```

## Queue de ações pendentes

Toda mutation que não é bloqueante passa por uma queue:

```typescript
// services/sync-queue.service.ts
import { Preferences } from '@capacitor/preferences';

interface QueuedAction {
  id: string;  // UUID local
  endpoint: string;
  method: 'POST' | 'PATCH' | 'DELETE';
  body: unknown;
  idempotency_key: string;  // server-side dedup
  created_at: string;
  attempts: number;
  last_attempt_at?: string;
  last_error?: string;
}

const QUEUE_KEY = 'sync_queue_v1';

export class SyncQueueService {
  async enqueue(action: Omit<QueuedAction, 'id' | 'created_at' | 'attempts' | 'idempotency_key'>) {
    const queued: QueuedAction = {
      ...action,
      id: crypto.randomUUID(),
      idempotency_key: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      attempts: 0,
    };
    const queue = await this.getQueue();
    queue.push(queued);
    await Preferences.set({ key: QUEUE_KEY, value: JSON.stringify(queue) });
    
    // Tenta imediatamente se online
    if (this.networkService.isOnline) this.processAll();
    
    return queued.id;
  }
  
  async processAll() {
    const queue = await this.getQueue();
    const remaining: QueuedAction[] = [];
    
    for (const action of queue) {
      try {
        await this.execute(action);
        // sucesso: remove da queue, notifica observers
        this.events$.next({ type: 'synced', action });
      } catch (err) {
        action.attempts++;
        action.last_attempt_at = new Date().toISOString();
        action.last_error = String(err);
        
        if (action.attempts >= 10) {
          // desistiu — mover para dead letter
          await this.moveToDeadLetter(action);
          this.events$.next({ type: 'failed_permanently', action, err });
        } else {
          remaining.push(action);
        }
      }
    }
    
    await Preferences.set({ key: QUEUE_KEY, value: JSON.stringify(remaining) });
  }
  
  private async execute(action: QueuedAction) {
    return await this.http.request(action.method, action.endpoint, {
      body: action.body,
      headers: { 'Idempotency-Key': action.idempotency_key },
    });
  }
}
```

### Ordem de processamento

- **FIFO por default** — ações processadas na ordem criada
- **Dependências explícitas:** se ação B depende de resultado de A, B fica bloqueada até A sintetizar
- **Dedup:** se usuário criou 2 "comentários idênticos" offline, ambos têm idempotency_key diferente (duplicatas reais) mas se foi double-tap, a UI deve prevenir enqueue duplo

### Retry e backoff

- Primeira falha: retry imediato
- Falhas 2-5: backoff exponencial (1s, 5s, 15s, 1min, 5min)
- Falhas 6-10: backoff longo (15min, 1h, 3h, 6h, 12h)
- Após 10 falhas: dead letter (humano decide)

Erros **não-retriáveis** (não incrementa attempt counter, rejeita imediatamente):
- 401 (auth) — queue para após re-login
- 403 (sem permissão) — mover para dead letter
- 400/422 (validação) — mover para dead letter com detalhes
- 409 (conflito) — pode precisar de merge UX (avançado)

Erros **retriáveis:** 5xx, timeout, offline.

## Cache de listagens

Last-known-good per query:

```typescript
// services/cache.service.ts
interface CachedResponse {
  data: unknown;
  fetched_at: string;
  ttl_seconds: number;
  version: number;  // bump quando schema muda — invalida automático
}

export class CacheService {
  private readonly SCHEMA_VERSION = 3;
  
  async get<T>(key: string): Promise<T | null> {
    const raw = await Preferences.get({ key: `cache:${key}` });
    if (!raw.value) return null;
    
    const cached: CachedResponse = JSON.parse(raw.value);
    if (cached.version !== this.SCHEMA_VERSION) {
      await Preferences.remove({ key: `cache:${key}` });
      return null;
    }
    return cached.data as T;
  }
  
  async set(key: string, data: unknown, ttlSeconds = 3600) {
    const cached: CachedResponse = {
      data, ttl_seconds: ttlSeconds,
      fetched_at: new Date().toISOString(),
      version: this.SCHEMA_VERSION,
    };
    await Preferences.set({ key: `cache:${key}`, value: JSON.stringify(cached) });
  }
  
  async getStale<T>(key: string): Promise<{ data: T; is_stale: boolean } | null> {
    const raw = await this.getRaw(key);
    if (!raw) return null;
    const age = (Date.now() - new Date(raw.fetched_at).getTime()) / 1000;
    return { data: raw.data as T, is_stale: age > raw.ttl_seconds };
  }
}
```

### Padrão stale-while-revalidate

```typescript
// feature/orders/orders.service.ts
async getOrders(): Promise<Order[]> {
  const cached = await this.cache.getStale<Order[]>('orders');
  
  // Stream imediato do cache (mesmo stale) para UX responsiva
  if (cached) this.ordersSubject.next(cached.data);
  
  // Revalida em background se online
  if (this.network.isOnline) {
    try {
      const fresh = await this.http.get<Order[]>('/api/v1/orders');
      await this.cache.set('orders', fresh, 3600);
      this.ordersSubject.next(fresh);
      return fresh;
    } catch {
      // Mantém cache se revalidação falhou
      if (cached) return cached.data;
      throw new Error('OFFLINE_AND_NO_CACHE');
    }
  }
  
  if (!cached) throw new Error('OFFLINE_AND_NO_CACHE');
  return cached.data;
}
```

## UI: banner persistente, não toast

Estado offline é **persistente e informacional**. Toast desaparece — ruim para quem não viu na hora.

### Banner no topo

```html
<ion-toolbar *ngIf="!(network.isOnline$ | async)" color="warning">
  <ion-text>Sem conexão · {{ pendingCount$ | async }} ações em fila</ion-text>
  <ion-button slot="end" fill="clear" (click)="retry()">Tentar agora</ion-button>
</ion-toolbar>
```

Requisitos:
- Sempre visível quando offline (não minimizável por scroll)
- Mostra contagem de ações em fila (feedback do que vai sincronizar)
- Cor warning, não danger (offline não é erro — é estado)
- Desaparece suavemente ao reconectar (fade 300ms)

### Feedback de ação enfileirada

Ao clicar em "Salvar" offline:
- Botão continua respondendo (não travar UI)
- Toast curto: "Salvo localmente. Vai sincronizar quando voltar a conexão."
- Item na lista ganha badge "Pendente" (ícone nuvem-traço)
- Ao sincronizar com sucesso: badge some + toast opcional "Sincronizado"
- Ao falhar permanentemente: badge vermelho "Falha — toque para ver" abre modal com detalhes + opção "tentar de novo / remover"

### Otimismo visual

Salvar uma nova mensagem offline? Ela aparece na lista **imediatamente** com estado visual "sendo enviada" (opacidade 0.6, ícone relógio). Quando sincroniza, vira estado normal. Se falhar definitivamente, fica vermelha com CTA de retry.

```typescript
// pattern: optimistic update + rollback
async sendMessage(text: string) {
  const tempId = `temp_${crypto.randomUUID()}`;
  const optimistic: Message = { id: tempId, text, sent_at: new Date().toISOString(), status: 'pending' };
  this.messagesSubject.next([...this.messagesSubject.value, optimistic]);
  
  try {
    const actionId = await this.queue.enqueue({
      endpoint: '/api/v1/messages',
      method: 'POST',
      body: { text, client_temp_id: tempId },
    });
    // Observers da queue atualizam o estado do optimistic ao sincronizar
  } catch (err) {
    // Marca falha permanente na UI
    this.updateMessage(tempId, { status: 'failed' });
  }
}
```

## Casos bloqueados offline

Nem tudo pode ser enfileirado. Operações que exigem resposta síncrona do servidor:

| Operação | Motivo | UX offline |
|----------|--------|------------|
| Pagamento | Confirmação de cobrança exige token do gateway | Modal: "Precisa de conexão para pagar" + CTA voltar |
| Login | Token vem do servidor | Tela de login com mensagem + CTA tentar de novo |
| Confirmação de reserva crítica | Exclusividade do recurso | Modal explicativo |
| Upload de foto grande | Não é enfileirar amigável | Opção "salvar rascunho" + upload ao reconectar |

Sempre: **modal explicativo**, não erro genérico. Usuário entende que app está funcionando, apenas esta operação precisa de rede.

```typescript
// guard
@Injectable()
export class RequiresOnlineGuard implements CanActivate {
  canActivate(): boolean {
    if (!this.network.isOnline) {
      this.modalService.show({
        title: 'Sem conexão',
        body: 'Esta ação precisa de conexão com a internet. Seus dados estão seguros — tente novamente quando conectar.',
        cta: 'Entendi',
      });
      return false;
    }
    return true;
  }
}
```

## Primeira carga offline

Se usuário abre o app sem nunca ter conectado antes:
- **Impossível:** mostrar dados personalizados (nada em cache)
- **Possível:** mostrar UI esqueleto + mensagem clara

```html
<div *ngIf="firstLoadOffline">
  <h2>Primeira vez?</h2>
  <p>Precisamos de uma conexão inicial para baixar seus dados. Quando conectar, ficará tudo pronto para uso offline.</p>
  <ion-button (click)="retry()">Tentar conectar</ion-button>
</div>
```

## Storage budget

Capacitor Preferences tem limite em iOS (~1MB no UserDefaults antes de degradar). Para volumes maiores:

- **< 1MB total:** Capacitor Preferences (simples, rápido)
- **1-50MB:** Capacitor SQLite
- **> 50MB:** SQLite + estratégia de eviction (LRU nos caches, purge de logs antigos)

Auditar periodicamente:
```typescript
async auditStorage() {
  const { keys } = await Preferences.keys();
  let totalBytes = 0;
  for (const k of keys) {
    const { value } = await Preferences.get({ key: k });
    totalBytes += new Blob([value || '']).size;
  }
  if (totalBytes > 5_000_000) this.evictOldest();
}
```

## Conflict resolution

Quando sync traz conflito (item foi editado localmente E no servidor enquanto offline):

### Estratégias, em ordem de simplicidade

1. **Last-write-wins** — default; simples; OK para casos não-críticos
2. **Server-wins** — para dados críticos (ex: preço, status de pagamento)
3. **Client-wins** — raro; só quando cliente tem informação autoritativa
4. **Merge automático** — campos independentes; ex: usuário editou nome, outro editou email → merge trivial
5. **UI de resolução** — avançado; mostrar as duas versões e deixar usuário escolher; reservado para documentos/colaboração

Documentar a escolha por tipo de recurso:
```yaml
# specs/sync.yaml
conflict_resolution:
  messages: last-write-wins
  orders: server-wins
  user_profile: client-wins
  documents: user-chooses
```

## Testing offline

Emular condições reais:

```typescript
// jest setup + integration tests
describe('offline flow', () => {
  beforeEach(async () => {
    // Desliga rede "fisicamente" para teste
    await Network.setStatus({ connected: false, type: 'none' });
  });
  
  it('enqueues actions while offline', async () => {
    const actionId = await service.createOrder({ amount: '100' });
    const queue = await service.getQueue();
    expect(queue).toContainEqual(expect.objectContaining({ id: actionId }));
  });
  
  it('processes queue on reconnect', async () => {
    await service.createOrder({ amount: '100' });
    
    // Reconecta
    await Network.setStatus({ connected: true, type: 'wifi' });
    await service.onReconnect();
    
    const queue = await service.getQueue();
    expect(queue).toHaveLength(0);
  });
  
  it('surfaces permanent failure after 10 attempts', async () => {
    jest.spyOn(http, 'request').mockRejectedValue(new Error('500'));
    const actionId = await service.createOrder({ amount: '100' });
    
    for (let i = 0; i < 10; i++) await service.processAll();
    
    expect(service.getDeadLetter()).toContainEqual(expect.objectContaining({ id: actionId }));
  });
});
```

Chaos testing manual:
- Modo avião durante uso (múltiplas telas)
- Rede lenta (DevTools throttling 3G)
- Toggle airplane mode 5x em 30s (detecção flaky?)
- Fechar app com queue pendente, reabrir → queue persiste?
- Força kill durante sync → não corromper queue

## Anti-patterns

- Toast "sem conexão" que desaparece (não persiste informação)
- Bloquear UI inteira com spinner ao perder rede
- Queue em memória (perde se app reinicia)
- Enfileirar ações críticas (pagamento) silenciosamente
- Retry infinito sem backoff → bate rate limit, queima bateria
- `navigator.onLine` como única fonte de verdade
- Cache sem versionamento → dados quebram em update do app
- Sem dead letter → queue cresce para sempre
- Assumir que reconexão é "volta ao normal" — sempre verificar integridade pós-reconexão

## Checklist para PLAN.md

- [ ] NetworkService usa Capacitor Network + ping real (não só navigator.onLine)
- [ ] Queue persistente (Preferences ou SQLite) com idempotency_key
- [ ] Retry com backoff exponencial + cap (10 tentativas)
- [ ] Dead letter para falhas permanentes
- [ ] Banner persistente de offline (não toast)
- [ ] Feedback visual de ação enfileirada (badge, opacidade)
- [ ] Otimismo UI com rollback em falha
- [ ] Guards `RequiresOnline` em operações bloqueantes (pagamento, login)
- [ ] Cache com TTL + schema_version (invalidação automática)
- [ ] Stale-while-revalidate em listagens
- [ ] Modal explicativo quando offline bloqueia ação
- [ ] Storage budget monitorado (< 5MB em Preferences)
- [ ] Conflict resolution documentada por tipo de recurso
- [ ] Testes: enfileiramento, sync ao reconectar, falha permanente, chaos
