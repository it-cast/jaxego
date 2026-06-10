# Skill: empty-states-polish

> Estados vazios, loading, erro e offline com polish de nível Linear/Stripe: skeleton loaders, CTAs em empty states, retry em erro, offline banner.
> Categoria: `ux-advanced` · 2026-04-18

## Propósito

Uma tela nunca é só "dados". Ela tem 5 estados possíveis, e cada um precisa de tratamento específico. Skills genéricas de UI focam no "estado feliz" — esta cobre os outros 4 que quebram a experiência se ignorados.

## Quando usar (triggers)

- Nova tela com lista, cards, tabela, busca
- Componente que consome API
- Revisão de tela existente
- Feedback de "tá meio vazio / confuso"

## Quando NÃO usar

- Tela estática (landing page de marketing) → não tem os 5 estados
- Formulário puro → usa outros padrões

---

## Os 5 estados obrigatórios

| Estado | Quando | O que mostrar |
|---|---|---|
| **Loading** | Dados chegando pela primeira vez | Skeleton screens (melhor que spinner) |
| **Empty** | API retornou array vazio | Ilustração + explicação + CTA concreto |
| **Success** | Dados renderizados | Conteúdo normal |
| **Error** | API falhou | Ícone + mensagem clara + botão "Tentar de novo" |
| **Offline** | Sem internet | Banner persistente + ação para retry automático |

---

## State machine padrão

```typescript
export type LoadState = 'idle' | 'loading' | 'success' | 'empty' | 'error' | 'offline';

export function deriveState<T>(
  items: T[] | null,
  isLoading: boolean,
  error: unknown,
  isOnline: boolean,
): LoadState {
  if (!isOnline) return 'offline';
  if (error) return 'error';
  if (isLoading && !items) return 'loading';
  if (items && items.length === 0) return 'empty';
  if (items && items.length > 0) return 'success';
  return 'idle';
}
```

---

## 1. Loading — Skeleton, não spinner

**Spinner** (`<ion-spinner>`, `<mat-spinner>`) é OK para ação pontual (botão salvando). Para **carregamento de tela**, use skeleton — dá previsibilidade do layout e percepção de velocidade.

```typescript
// Ionic
@Component({
  template: `
    <ion-list>
      @for (_ of skeletonItems; track $index) {
        <ion-item>
          <ion-thumbnail slot="start">
            <ion-skeleton-text [animated]="true" />
          </ion-thumbnail>
          <ion-label>
            <h3><ion-skeleton-text [animated]="true" style="width: 60%" /></h3>
            <p><ion-skeleton-text [animated]="true" style="width: 80%" /></p>
          </ion-label>
        </ion-item>
      }
    </ion-list>
  `,
})
export class ProfessionalListSkeleton {
  skeletonItems = Array(6);  // quantos "fantasmas" mostrar
}
```

```typescript
// Angular Material
import { NgxSkeletonLoaderModule } from 'ngx-skeleton-loader';

@Component({
  template: `
    <div class="stats-grid">
      @for (_ of [1,2,3,4,5,6]; track $index) {
        <mat-card>
          <ngx-skeleton-loader [theme]="{ width: '40%', height: '14px' }" />
          <ngx-skeleton-loader [theme]="{ width: '60%', height: '32px' }" />
        </mat-card>
      }
    </div>
  `,
})
```

**Regra:** skeleton deve **bater na forma** do conteúdo final (3 linhas = 3 linhas de skeleton; grid 3x2 = 6 skeletons).

---

## 2. Empty state — sempre com CTA

**Regra de ouro:** empty state sem ação é abandono. Toda tela vazia precisa de:
- Ícone ou ilustração (não exagerar)
- Título curto ("Nenhum orçamento ainda")
- Subtítulo explicativo 1 frase
- CTA claro ("Criar primeiro orçamento")

```typescript
// Componente reutilizável
@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [IonIcon, IonButton],
  template: `
    <div class="empty">
      <ion-icon [name]="icon" />
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
      @if (ctaLabel) {
        <ion-button fill="solid" color="primary" (click)="ctaClick.emit()">
          {{ ctaLabel }}
        </ion-button>
      }
    </div>
  `,
  styles: [`
    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 48px 24px;
      gap: 16px;
    }
    ion-icon {
      font-size: 64px;
      color: var(--ion-color-medium);
      opacity: 0.5;
    }
    h2 { margin: 0; font-size: 18px; font-weight: 600; }
    p { margin: 0; color: var(--ion-color-medium); max-width: 280px; }
  `],
})
export class EmptyStateComponent {
  @Input() icon = 'inbox';
  @Input() title = 'Nada por aqui ainda';
  @Input() description = '';
  @Input() ctaLabel = '';
  @Output() ctaClick = new EventEmitter<void>();
}
```

### Exemplos no {PROJETO}

| Tela | Título | Descrição | CTA |
|---|---|---|---|
| Orçamentos cliente vazio | "Você ainda não solicitou orçamento" | "Encontre um profissional e conte o que precisa." | "Buscar profissional" |
| Portfólio profissional vazio | "Mostre seu trabalho" | "Adicione fotos de serviços anteriores para atrair clientes." | "Adicionar foto" |
| Busca sem resultado | "Nenhum profissional encontrado" | "Tente outra categoria ou amplie a região." | "Limpar filtros" |
| Admin dashboard sem contratações | "Aguardando primeira contratação" | "Os KPIs aparecem aqui quando as primeiras transações acontecerem." | (sem CTA — é informativo) |
| Chat sem mensagens | "Começar a conversa" | "Diga oi e pergunte o que precisar." | (input de mensagem fica visível) |

---

## 3. Error state — retry sempre visível

```typescript
@Component({
  selector: 'app-error-state',
  template: `
    <div class="error">
      <ion-icon name="alert-circle-outline" />
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
      <ion-button fill="solid" (click)="retry.emit()">
        Tentar de novo
      </ion-button>
      @if (showSupport) {
        <ion-button fill="clear" size="small">
          Reportar problema
        </ion-button>
      }
    </div>
  `,
})
export class ErrorStateComponent {
  @Input() title = 'Algo deu errado';
  @Input() description = 'Não conseguimos carregar os dados. Verifique sua conexão e tente novamente.';
  @Input() showSupport = false;
  @Output() retry = new EventEmitter<void>();
}
```

**Classificar erros:**

| HTTP | Mensagem amigável |
|---|---|
| `0` / network | "Sem conexão. Verifique sua internet." |
| `401` | Redirecionar pro login — não mostrar error state |
| `403` | "Você não tem permissão para ver isso." |
| `404` | "Página não encontrada." |
| `500+` | "Nosso sistema teve um problema. Tente de novo em instantes." |
| `503` | "Sistema em manutenção. Volte em alguns minutos." |

**Nunca** mostrar stack trace, JSON da API ou `Error: NetworkError at line 42`.

---

## 4. Offline state

Capacitor Network + Angular:

```typescript
import { Network } from '@capacitor/network';

@Injectable({ providedIn: 'root' })
export class ConnectivityService {
  isOnline = signal(true);

  constructor() {
    Network.addListener('networkStatusChange', status => {
      this.isOnline.set(status.connected);
    });
    Network.getStatus().then(s => this.isOnline.set(s.connected));
  }
}
```

```html
<!-- Banner no app.component.html -->
@if (!connectivity.isOnline()) {
  <div class="offline-banner" role="alert">
    <ion-icon name="cloud-offline" />
    <span>Sem conexão. Mudanças serão sincronizadas quando voltar online.</span>
  </div>
}
```

### Offline queue (operações que podem esperar)

```typescript
// Enviar mensagem no chat offline → enfileirar, re-tentar ao voltar online
async sendMessage(text: string) {
  if (!this.connectivity.isOnline()) {
    await this.offlineQueue.enqueue({ type: 'send_message', text, queuedAt: Date.now() });
    this.showLocalMessage({ text, status: 'queued' });
    return;
  }
  await this.api.sendMessage(text);
}
```

---

## 5. Loading dentro de um estado success (parcial)

Às vezes a lista já carregou, mas paginação puxa mais, ou item atualiza:

```html
<!-- Lista principal -->
<ion-list>
  @for (item of items(); track item.id) {
    <ion-item [class.updating]="updatingIds().has(item.id)">
      {{ item.name }}
      @if (updatingIds().has(item.id)) {
        <ion-spinner slot="end" name="dots" />
      }
    </ion-item>
  }

  @if (isLoadingMore()) {
    <ion-item>
      <ion-skeleton-text [animated]="true" />
    </ion-item>
  }
</ion-list>
```

---

## Template de uso completo

```typescript
@Component({
  template: `
    @switch (state()) {
      @case ('loading') {
        <app-professional-list-skeleton />
      }
      @case ('offline') {
        <app-empty-state
          icon="cloud-offline"
          title="Sem conexão"
          description="Conecte-se à internet para ver profissionais."
        />
      }
      @case ('error') {
        <app-error-state (retry)="load()" />
      }
      @case ('empty') {
        <app-empty-state
          icon="search"
          title="Nenhum profissional encontrado"
          description="Tente outra categoria ou amplie a região de busca."
          ctaLabel="Limpar filtros"
          (ctaClick)="clearFilters()"
        />
      }
      @case ('success') {
        <ion-list>
          @for (p of items(); track p.id) {
            <ion-item>{{ p.name }}</ion-item>
          }
        </ion-list>
      }
    }
  `,
})
export class SearchPage {
  // ...usando deriveState...
}
```

---

## Anti-patterns

1. ❌ **Tela em branco durante loading** — usuário pensa que travou
2. ❌ **"Loading..."** como texto puro — sem feedback visual
3. ❌ **Empty state sem CTA** — "Nenhum pedido encontrado." e pronto. Para onde o usuário vai?
4. ❌ **Mostrar JSON do erro** na tela — `{"detail": "..."}` vaza implementação
5. ❌ **Retry sem cooldown** — usuário clica 10x, gera 10 requests
6. ❌ **Spinner infinito sem timeout** — sem erro, sem feedback, sem escape
7. ❌ **Offline banner sem ação** — "Você está offline." e pronto; e agora?
8. ❌ **Empty state com ilustração genérica da internet** — inconsistente com marca
9. ❌ **Skeleton que não bate com layout final** — conteúdo "pula" quando chega
10. ❌ **Estado loading bloqueando interações válidas** — ex: header com filtro fica unclickable

---

## Checklist de review

- [ ] Tela trata os 5 estados: loading, success, empty, error, offline
- [ ] Loading usa skeleton, não spinner (para carregamento de tela)
- [ ] Empty state tem ícone + título + descrição + CTA (quando aplicável)
- [ ] Error state tem retry
- [ ] Mensagens de erro em português natural
- [ ] Stack trace / JSON nunca exibidos ao usuário
- [ ] Offline detection via Capacitor Network ou `navigator.onLine`
- [ ] Operações críticas têm queue offline (chat, criar orçamento)
- [ ] Skeleton bate com layout final (não pula ao trocar)
- [ ] `deriveState()` centralizado, não espalhado pela tela

<!-- Skill aplicada: toda tela consumidora de API -->
