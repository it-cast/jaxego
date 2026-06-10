---
name: loading-states
category: ux-advanced
description: Padrões completos de loading — spinner, skeleton, progressive reveal, optimistic updates, com mapping de cada padrão a contexto de uso, snippets prontos React/Angular, decisão por tempo perceptual, anti-patterns frequentes e como integrar com error/empty states. Resolve "tela em branco enquanto carrega" e "dupla submissão por falta de feedback".
---

# Loading States — Estados de Carregamento

> Tela em branco = travou. Spinner = aceitável. Skeleton = profissional. Progressive = excelente. Optimistic = mágico.

Esta skill define qual padrão usar em cada contexto, como implementar concretamente, e como evitar os 7 anti-patterns clássicos.

---

## 1. Quando esta skill é obrigatória

| Momento | Por quê |
|---|---|
| Toda phase com fetch async (API call) | Sem feedback = parece travado |
| Toda phase com lista, dashboard, feed | Skeletons são esperados |
| Toda phase com submit de form | Spinner + disable obrigatórios |
| Toda phase com upload de arquivo | Progress bar |
| Após `quality/performance-web-vitals` identificar gargalo | Pelo menos suavizar visual |

## 2. Quando NÃO usar

- Phase backend sem UI
- Operações <100ms (não precisa de feedback visual)
- Phases de infra

---

## 3. Tempos perceptuais (decisão começa aqui)

| Tempo | Percepção | Resposta UX |
|---|---|---|
| <100ms | Instantâneo | Sem feedback |
| 100ms-1s | Notável mas tolerável | Spinner sutil OU optimistic |
| 1-3s | Precisa feedback claro | Skeleton ou progress |
| 3-10s | Precisa progress real ou ETA | Progress bar com %, mensagem |
| >10s | Precisa explicação + cancelar | "Processando relatório... pode levar 1min. Cancelar" |
| >30s | Precisa async com notificação | Email/push quando pronto |

**Regra prática:** medir tempo real (P95, não P50) com analytics. Otimizar UX para P95.

---

## 4. Os 4 níveis de loading state

### 4.1 Nível 1 — Spinner (mínimo aceitável)

**Quando usar:**
- Ação rápida (<2s)
- Operação atômica (não dá pra mostrar parcial)
- Submit de formulário
- Botão clicado

**Implementação:**

```jsx
// React
function SaveButton({ onSave }) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      await onSave();
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleClick} disabled={loading}>
      {loading ? <Spinner size="sm" /> : 'Salvar'}
    </button>
  );
}
```

```typescript
// Angular 19 com signals
@Component({
  selector: 'save-button',
  template: `
    <button (click)="handleSave()" [disabled]="loading()">
      @if (loading()) {
        <ion-spinner name="crescent" />
      } @else {
        Salvar
      }
    </button>
  `
})
export class SaveButtonComponent {
  loading = signal(false);

  async handleSave() {
    this.loading.set(true);
    try {
      await this.saveService.save();
    } finally {
      this.loading.set(false);
    }
  }
}
```

**Boas práticas:**
- Spinner inline no botão (não fora)
- Disable do botão simultaneamente
- Texto muda ("Salvando..." em vez de "Salvar")
- Tamanho proporcional ao botão (16px em botão sm, 20px em md)

**❌ NÃO fazer:**
- Spinner full-screen para ação de 500ms
- Spinner sem disable do botão (permite duplo click)
- Spinner por mais de 5s sem mensagem adicional

### 4.2 Nível 2 — Skeleton screens

**Quando usar:**
- Layout previsível (sabemos onde vai aparecer texto, imagem)
- Tempo de carregamento >500ms
- Lista, card, perfil, dashboard

**Princípio:** mostrar a "casca" do conteúdo final, com animação shimmer suave.

**Implementação:**

```jsx
// React + Tailwind
function CardSkeleton() {
  return (
    <div className="rounded-lg border border-slate-200 p-4 animate-pulse">
      <div className="flex items-center gap-3 mb-4">
        <div className="rounded-full bg-slate-200 h-12 w-12" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-3/4" />
          <div className="h-3 bg-slate-200 rounded w-1/2" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-slate-200 rounded" />
        <div className="h-3 bg-slate-200 rounded" />
        <div className="h-3 bg-slate-200 rounded w-5/6" />
      </div>
    </div>
  );
}

function CardList() {
  const { data, isLoading } = useQuery(['cards'], fetchCards);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => <CardSkeleton key={i} />)}
      </div>
    );
  }

  return data.map(card => <Card key={card.id} {...card} />);
}
```

```typescript
// Angular 19 com signals + resource API
@Component({
  selector: 'card-list',
  template: `
    @if (cards.isLoading()) {
      @for (i of [1,2,3,4,5]; track i) {
        <div class="card-skeleton">
          <div class="avatar-skeleton"></div>
          <div class="text-skeleton" style="width: 75%"></div>
          <div class="text-skeleton" style="width: 50%"></div>
        </div>
      }
    } @else {
      @for (card of cards.value(); track card.id) {
        <app-card [card]="card" />
      }
    }
  `,
  styles: `
    .card-skeleton {
      background: var(--color-surface-raised);
      border: 1px solid var(--color-border-default);
      padding: 16px;
      border-radius: 8px;
      animation: pulse 2s ease-in-out infinite;
    }

    .avatar-skeleton, .text-skeleton {
      background: var(--color-surface-sunken);
      border-radius: 4px;
    }

    .avatar-skeleton {
      width: 48px;
      height: 48px;
      border-radius: 50%;
    }

    .text-skeleton {
      height: 12px;
      margin-bottom: 8px;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `
})
export class CardListComponent {
  cards = resource({
    loader: () => this.cardService.fetchCards()
  });
}
```

**Boas práticas de skeleton:**
- Animação shimmer **suave** (pulse 2s, não pulsing agressivo a 500ms)
- Tamanhos próximos ao conteúdo real (não exagerar)
- Quantidade certa (não 50 skeletons se média é 5 itens)
- Cor neutra (`surface.sunken`, não brand color)
- Forma do skeleton corresponde ao conteúdo (avatar é círculo, texto é retângulo)

**❌ NÃO fazer:**
- Skeleton que pisca/agrida visualmente
- Skeleton totalmente diferente da UI final (causa shift visual)
- Skeleton perpétuo se erro
- Skeleton em página inteira quando só uma seção carrega

### 4.3 Nível 3 — Progressive loading

**Quando usar:**
- Conteúdo tem hierarquia (estrutura primeiro, dados depois)
- Imagens pesadas
- Seções independentes

**Princípio:** carregar em estágios, mostrando o que já está pronto.

**Estágios:**

```
Estágio 1: estrutura aparece imediatamente (header, layout, sidebar)
Estágio 2: dados textuais (titles, names, numbers)
Estágio 3: imagens (com blur placeholder primeiro)
Estágio 4: dados secundários (related items, comments, recommendations)
```

**Implementação React (Suspense):**

```jsx
function DashboardPage() {
  return (
    <div>
      {/* Estágio 1 — estrutura */}
      <Header />
      <Sidebar />

      <main>
        {/* Estágio 2 — dados textuais (rápido) */}
        <Suspense fallback={<KPISkeleton />}>
          <KPISummary />
        </Suspense>

        {/* Estágio 3 — gráficos (médio) */}
        <Suspense fallback={<ChartSkeleton />}>
          <RevenueChart />
        </Suspense>

        {/* Estágio 4 — secundário (lento, OK demorar) */}
        <Suspense fallback={<TableSkeleton />}>
          <RecentTransactions />
        </Suspense>
      </main>
    </div>
  );
}
```

**Implementação para imagens (LQIP — Low Quality Image Placeholder):**

```jsx
function ProgressiveImage({ src, lqip, alt }) {
  const [loaded, setLoaded] = useState(false);

  return (
    <div style={{ position: 'relative' }}>
      {/* Imagem blur de baixíssima qualidade (~500 bytes inline base64) */}
      <img
        src={lqip}
        alt={alt}
        style={{
          filter: 'blur(20px)',
          opacity: loaded ? 0 : 1,
          transition: 'opacity 300ms'
        }}
      />

      {/* Imagem real */}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        style={{
          position: 'absolute',
          inset: 0,
          opacity: loaded ? 1 : 0,
          transition: 'opacity 300ms'
        }}
      />
    </div>
  );
}
```

**Boas práticas:**
- Estágios independentes (1 lento não bloqueia outros)
- LQIP base64 inline (zero request extra)
- Usar `loading="lazy"` em imagens abaixo da dobra
- SSR/SSG para estrutura (HTML chega pronto)

### 4.4 Nível 4 — Optimistic updates

**Quando usar:**
- Ação de baixo risco (curtir, marcar como lido, toggle)
- Network confiável esperada
- Reversão é fácil
- Feedback precisa ser <16ms

**Princípio:** UI atualiza ANTES da resposta do servidor. Se servidor falhar, reverte.

**Implementação React Query:**

```jsx
function LikeButton({ post }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => api.toggleLike(post.id),

    // Optimistic update
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['post', post.id] });
      const previous = queryClient.getQueryData(['post', post.id]);

      queryClient.setQueryData(['post', post.id], old => ({
        ...old,
        liked: !old.liked,
        likeCount: old.liked ? old.likeCount - 1 : old.likeCount + 1
      }));

      return { previous };
    },

    // Reverte se erro
    onError: (err, variables, context) => {
      queryClient.setQueryData(['post', post.id], context.previous);
      toast.error('Não foi possível atualizar. Tente novamente.');
    },

    // Sincroniza no fim
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['post', post.id] });
    }
  });

  return (
    <button onClick={() => mutation.mutate()}>
      {post.liked ? '❤️' : '🤍'} {post.likeCount}
    </button>
  );
}
```

**Boas práticas:**
- Animação sutil para confirmar mudança (heart pop, número incrementa)
- Toast com botão "Desfazer" se ação for surpreendente
- NUNCA usar para: pagamento, delete permanente, ações com side-effects irreversíveis

**❌ NÃO fazer:**
- Optimistic em pagamento (cliente pensa que pagou e não pagou)
- Optimistic em delete (já sumiu da UI, depois volta — confuso)
- Optimistic sem fallback de erro

---

## 5. Decisão por contexto (matriz completa)

| Contexto | Padrão recomendado | Notas |
|---|---|---|
| Submit de formulário | Spinner + disable | Sempre |
| Submit de pagamento | Spinner + disable + idempotência backend | Crítico |
| Submit de delete | Confirmação modal → spinner → toast | Não optimistic |
| Carregar lista/feed | Skeleton (5-10 cards) | Default |
| Carregar imagem em card | Blur placeholder (LQIP) | Performance |
| Aplicar filtro em tabela | Skeleton da tabela OU dim + spinner | Depende do tempo |
| Curtir post | Optimistic update | Comum |
| Marcar tarefa como done | Optimistic update | Comum |
| Excluir item | Confirmação → spinner → toast com Desfazer | Reversível |
| Pagamento online | Tela dedicada com mensagem progressiva | Crítico |
| Pull to refresh | Spinner customizado em cima | Mobile |
| Infinite scroll | Skeleton no final | Lista longa |
| Lazy load (rota) | Spinner full ou skeleton de rota | SPA navigation |
| Upload de arquivo | Progress bar com % | Sempre |
| Export longo (PDF, Excel) | "Processando... vai chegar por email" | >10s |
| Render de gráfico | Skeleton chart → fade in | Tipo dashboard |
| WebSocket reconnect | Banner sutil "Reconectando..." | Não bloqueia UI |

---

## 6. Loading vs empty vs error (não confundir)

Os 3 estados são diferentes e UI deve distinguir:

```jsx
function CardList() {
  const { data, isLoading, error } = useQuery(['cards'], fetchCards);

  // 1. LOADING — durante fetch
  if (isLoading) {
    return <SkeletonList count={5} />;
  }

  // 2. ERROR — fetch falhou
  if (error) {
    return (
      <ErrorState
        message="Não foi possível carregar os cards."
        action={<button onClick={refetch}>Tentar novamente</button>}
      />
    );
  }

  // 3. EMPTY — sucesso mas sem dados
  if (data.length === 0) {
    return (
      <EmptyState
        icon={<InboxIcon />}
        title="Sem cards ainda"
        description="Crie seu primeiro card para começar."
        action={<button onClick={createCard}>Criar primeiro card</button>}
      />
    );
  }

  // 4. SUCCESS — render dados
  return <CardGrid items={data} />;
}
```

**Anti-patterns:**

```
❌ Mostrar empty state durante loading (usuário pensa que está vazio)
❌ Mostrar skeleton perpétuo se erro
❌ Tratar erro como empty (esconde problema real)
❌ Não diferenciar "0 resultados de busca" vs "lista vazia"
```

---

## 7. Loading com timeout

Toda operação de loading deve ter timeout. Sem timeout = trava perpétua.

```jsx
function useFetchWithTimeout(url, timeoutMs = 30000) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    fetch(url, { signal: controller.signal })
      .then(r => r.json())
      .then(data => setState({ data, loading: false, error: null }))
      .catch(err => {
        if (err.name === 'AbortError') {
          setState({ data: null, loading: false, error: 'Timeout' });
        } else {
          setState({ data: null, loading: false, error: err.message });
        }
      })
      .finally(() => clearTimeout(timeout));

    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [url]);

  return state;
}
```

**Tempos recomendados:**
- API request normal: 30s
- Upload pequeno (<10MB): 60s
- Upload grande (>10MB): 5min
- Job assíncrono (relatório): 10min, depois muda para polling

---

## 8. Anti-patterns com correção

### Anti-pattern 1: Spinner full-screen para tudo

```
❌ ERRADO:
function App() {
  if (loading) return <FullScreenSpinner />;
  return <MainContent data={data} />;
}

✅ CORRETO:
function App() {
  return (
    <Layout>
      <Header /> {/* sempre visível */}
      <Sidebar /> {/* sempre visível */}
      <Suspense fallback={<ContentSkeleton />}>
        <MainContent />
      </Suspense>
    </Layout>
  );
}
```

### Anti-pattern 2: Loading sem timeout

```
❌ ERRADO:
const { data, loading } = useQuery(...); // sem timeout, pode ficar para sempre

✅ CORRETO:
const { data, loading, error } = useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  staleTime: 5 * 60 * 1000,
  retry: 3,
  retryDelay: 1000,
  // React Query tem timeout via abort
});
```

### Anti-pattern 3: Skeleton que pisca

```css
/* ❌ ERRADO — agressivo */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }  /* drop muito grande */
}
.skeleton { animation: pulse 0.5s infinite; }  /* muito rápido */

/* ✅ CORRETO — suave */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }  /* drop sutil */
}
.skeleton { animation: pulse 2s ease-in-out infinite; }
```

### Anti-pattern 4: Optimistic em pagamento

```
❌ ERRADO:
async function pay() {
  setStatus('paid'); // optimistic — usuário vê "pago"
  try {
    await api.charge();
  } catch (e) {
    setStatus('pending');
    toast.error('Falha no pagamento');
    // Tarde demais — usuário já saiu da página confiando que pagou
  }
}

✅ CORRETO:
async function pay() {
  setStatus('processing');
  try {
    const result = await api.charge(); // espera confirmação real
    setStatus('paid');
    toast.success('Pagamento confirmado');
  } catch (e) {
    setStatus('failed');
    toast.error('Falha no pagamento. Tente novamente.');
  }
}
```

### Anti-pattern 5: Hard reload em SPA

```
❌ ERRADO:
function refreshData() {
  window.location.reload(); // perde estado, é horrível
}

✅ CORRETO:
function refreshData() {
  queryClient.invalidateQueries(); // re-fetch sem perder estado
}
```

### Anti-pattern 6: Loading sem disable do botão

```jsx
// ❌ ERRADO — usuário clica 5x = 5 requests
<button onClick={handleSubmit}>
  {loading ? <Spinner /> : 'Enviar'}
</button>

// ✅ CORRETO
<button onClick={handleSubmit} disabled={loading}>
  {loading ? <><Spinner /> Enviando...</> : 'Enviar'}
</button>
```

### Anti-pattern 7: Skeleton diferente da UI final

```
❌ ERRADO:
Skeleton: 3 retângulos em coluna
UI final: card com avatar circular, título, texto em 2 colunas
→ Layout shift gigante quando carrega

✅ CORRETO:
Skeleton: avatar circular + título retangular + 2 colunas de texto
→ Mesma estrutura, sem shift
```

---

## 9. Casos práticos por contexto

### 9.1 Áugure — Simulação de mercado (15 min)

```
Estado 1 (0-2s): Spinner com mensagem "Iniciando simulação..."
Estado 2 (2s-15min): Progress bar com etapas:
  - "Coletando dados de mercado... (etapa 1/5)"
  - "Analisando concorrência... (etapa 2/5)"
  - "Calculando viabilidade financeira... (etapa 3/5)"
  - "Gerando cenários... (etapa 4/5)"
  - "Compilando relatório... (etapa 5/5)"
Estado 3 (após 15min): Toast "Pronto! [Ver relatório]"

Permitir: fechar e receber email quando pronto
```

### 9.2 SaaS dashboard

```
Estágio 1 (0ms): Layout (header, sidebar) — SSR
Estágio 2 (~200ms): KPIs principais (4 cards) — Suspense
Estágio 3 (~500ms): Gráficos (3 charts) — Suspense
Estágio 4 (~1s): Tabela de transações recentes — Suspense
Estágio 5 (lazy): Sidebar de notificações — quando user clicar
```

### 9.3 Mobile app — Lista de pedidos

```
Pull to refresh: spinner customizado top
Initial load: 5 skeletons de pedido
Scroll para fim: skeleton no final + "Carregando mais..."
Erro de rede: banner "Sem conexão" + cache local
Optimistic: marcar como visualizado (sem esperar API)
```

### 9.4 Checkout

```
Step 1 (carrinho): instant render (cache local)
Step 2 (endereço): CEP autocomplete com spinner inline
Step 3 (pagamento): submit com spinner + disable + texto "Processando pagamento..."
Step 4 (confirmação): page redirect com spinner curto
```

---

## 10. Bibliotecas e ferramentas

### 10.1 React

- **React Query / TanStack Query** — fetching com loading/error states
- **SWR** — alternativa do Vercel
- **React Suspense** — composable loading states
- **react-loading-skeleton** — componente de skeleton
- **react-content-loader** — SVG-based skeletons

### 10.2 Angular

- **Angular signals + resource API** (v19+) — moderno
- **rxjs operators** (`switchMap`, `tap`) para loading state
- **ngx-skeleton-loader** — componente de skeleton

### 10.3 Ionic

- **`<ion-skeleton-text>`** — skeleton built-in
- **`<ion-spinner>`** — spinner built-in
- **`<ion-progress-bar>`** — progress bar
- **`<ion-refresher>`** — pull to refresh nativo

---

## 11. Checklist de validação

```
□ Toda ação >100ms tem feedback visual?
□ Skeleton em listas/feeds (não spinner full-screen)?
□ Loading distingue de empty e error?
□ Submit de form tem disable + spinner?
□ Submit não permite duplo click?
□ Operações longas (>10s) têm progress real ou ETA?
□ Operações muito longas (>30s) têm modo async + notificação?
□ Optimistic updates só em ações reversíveis (não pagamento)?
□ Imagens pesadas têm LQIP placeholder?
□ Toda fetch tem timeout (não trava perpétuo)?
□ Loading state tem cor neutra (não brand vibrante)?
□ Skeleton tem mesma estrutura da UI final (sem shift)?
□ Erro de rede mostra retry button?
□ Backend tem idempotência em submits críticos?
□ Loading testado em conexão lenta (Chrome DevTools throttle 3G)?
```

---

## 12. Como integra com outras skills

### 12.1 → `ux-advanced/empty-states-polish`
Ambos são estados ausentes. Loading distingue de empty.

### 12.2 → `ux-advanced/feedback-patterns`
Loading é UM tipo de feedback. Toast/banner são outros.

### 12.3 → `quality/error-ux-patterns`
Loading e error são sequenciais (loading → success OU error).

### 12.4 → `quality/performance-web-vitals`
Identifica gargalos. Loading suaviza visual mas não substitui performance real.

### 12.5 → `ux-advanced/payment-checkout-ux`
Loading em pagamento é crítico (sem optimistic, sempre confirmar).

### 12.6 → PLAN.md de phase

```markdown
## Phase 5 — Lista de pedidos

### Skills Consultadas
- `ux-advanced/loading-states` — skeleton para list, optimistic em mark-as-read
- `ux-advanced/empty-states-polish` — caso de "sem pedidos"
- `quality/error-ux-patterns` — caso de erro de rede
```

---

## 13. Erros comuns

### Erro 1: "Spinner em tudo"
Spinner não é universal. Skeleton é melhor para layouts conhecidos.

### Erro 2: "Implementar depois"
Loading states adicionados depois = retrabalho enorme. Sempre desde o início.

### Erro 3: "Não testar em conexão lenta"
Em wi-fi gigabit, tudo carrega rápido. Em 3G, percebe os problemas. Sempre testar throttle.

### Erro 4: "Optimistic em todo lugar"
Optimistic só em ações reversíveis e baixo risco.

### Erro 5: "Skeleton sem shimmer"
Skeleton estático parece bug. Sempre animar (suave).

---

## 14. Referências

- **Refactoring UI** (Wathan, Schoger) — capítulo de loading
- **Nielsen Norman Group** — "Response Times: The 3 Important Limits"
- **React Query docs** — patterns de loading
- **Material Design — Progress indicators**

---

**Última atualização:** v0.7.0 (densificação)
**Densidade:** 14 seções, 4 níveis com snippets React+Angular, matriz completa de decisão por contexto, anti-patterns com correção, casos práticos
