# Skill: design-to-code

> **Protocolo obrigatório de tradução design → código para o {PROJETO}**
> Categoria: `meta` · Stack: Angular 19 + Ionic 8 + Design System {PROJETO} · Versão: 1.0 · 2026-04-22

---

## Propósito

Quando Claude Code implementa UI sem seguir um protocolo, o resultado é inconsistente: cores hardcoded, tokens ignorados, copy improvisado, estados faltando, acessibilidade zero. Esta skill define a sequência obrigatória de 6 passos que **todo** componente de UI deve seguir — do intent à implementação.

## Quando usar esta skill (triggers)

- Qualquer tarefa que crie ou modifique componente visual
- `/gsd-ui-phase` — invocado automaticamente
- Code review de PR com mudança em template `.html` ou `.scss`
- Implementar nova tela no admin ou mobile
- Refatorar componente existente por motivo visual

## Quando NÃO usar

- Endpoints API sem UI — `api-design-contracts`
- Lógica de negócio pura — `services/`
- Migrations de banco — `mysql-schema-design`

---

## Sequência obrigatória: 6 passos

### Passo 1 — INTENT: entender o objetivo e contexto

Antes de qualquer código, responder:

```
1. Qual tela/componente está sendo implementado?
2. Qual o objetivo do usuário nesta tela? (ex: "ver suas propostas ativas")
3. Qual plataforma? admin (Angular Material) ou mobile (Ionic 8)?
4. Quais skills são relevantes? (verificar SKILLS_INDEX.md)
5. Existe referência visual? (docs/identidade-visual/prototipos-html/ ou screenshots-referencia/)
```

**Gate de entrada:** se não souber responder 1 e 2, não avançar. Perguntar ao usuário.

---

### Passo 2 — TOKENS: verificar e usar design tokens

```typescript
// PROIBIDO — hex hardcoded no SCSS
.card { background: #1565C0; color: #FFFFFF; }

// CORRETO — tokens do sistema
.card { background: var(--color-primary); color: var(--color-on-primary); }
```

**Tokens {PROJETO} obrigatórios a verificar:**

```css
/* Paleta de cores */
--color-primary: #1565C0;          /* Azul {PROJETO} */
--color-primary-dark: #003c8f;
--color-secondary: #00897B;        /* Verde */
--color-accent: #FFD600;           /* Amarelo */

/* Semânticos */
--color-success: #2E7D32;
--color-warning: #F57F17;
--color-error: #C62828;

/* Tipografia */
--text-xs: 11px;
--text-sm: 13px;
--text-base: 15px;
--text-lg: 18px;
--text-xl: 22px;

/* Espaçamento */
--space-1: 4px;   --space-2: 8px;   --space-3: 12px;  --space-4: 16px;
--space-5: 20px;  --space-6: 24px;  --space-8: 32px;  --space-10: 40px;

/* Bordas */
--radius-sm: 4px;  --radius-md: 8px;  --radius-lg: 12px;  --radius-xl: 20px;

/* Sombras */
--shadow-sm: 0 1px 3px rgba(0,0,0,.08);
--shadow-md: 0 2px 8px rgba(0,0,0,.12);
--shadow-lg: 0 4px 16px rgba(0,0,0,.16);
```

**Gate Passo 2:** Se algum hex hardcoded aparecer no SCSS, rejeitar. Verificar `design-tokens-system`.

---

### Passo 3 — COPY: definir textos antes de codar

Antes de escrever template:

```typescript
// Definir todas as strings visíveis
const STRINGS = {
  title: 'Minhas propostas',
  empty: {
    title: 'Nenhuma proposta ainda',
    body: 'Quando clientes enviarem orçamentos, eles aparecerão aqui.',
    cta: 'Cadastrar serviço',
  },
  loading: 'Carregando propostas...',
  error: {
    title: 'Não foi possível carregar',
    body: 'Verifique sua conexão e tente novamente.',
    retry: 'Tentar novamente',
  },
};
```

**Verificar com:** `ux-copywriting-ptbr` (tom, voz, microcopy pt-BR).

**Gate Passo 3:** Se template tem strings inline em inglês ou genéricas ("Loading...", "Error"), rejeitar.

---

### Passo 4 — IMPLEMENTATION: código com padrões do projeto

```typescript
// Estrutura canônica de componente de tela
@Component({
  selector: 'app-proposals',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    // Só imports necessários — nenhum NgModule
    CommonModule, // apenas se realmente necessário
    IonContent, IonList, IonItem,
    RouterLink,
    StatusBadgeComponent,
    OfflineBannerComponent,
  ],
  template: `...`,
})
export class ProposalsPage {
  private readonly svc = inject(ProposalService);
  private readonly network = inject(NetworkService);

  protected readonly state = signal<'loading' | 'success' | 'empty' | 'error' | 'offline'>('loading');
  protected readonly items = signal<ProposalResponse[]>([]);
  protected readonly strings = STRINGS;

  ionViewWillEnter(): void {
    this.load();
  }

  protected async load(): Promise<void> {
    this.state.set('loading');
    try {
      const data = await this.svc.listProposals();
      this.items.set(data);
      this.state.set(data.length ? 'success' : 'empty');
    } catch {
      this.state.set(this.network.online() ? 'error' : 'offline');
    }
  }
}
```

**Verificar com:** `ionic-patterns` (mobile) ou `angular-material-patterns` (admin).

---

### Passo 5 — STATES: implementar todos os 5 estados

Todo componente de tela que consome API deve ter os 5 estados:

```html
@switch (state()) {
  @case ('loading') {
    <!-- Skeleton — nunca spinner isolado para lista -->
    <ion-list>
      @for (i of [1,2,3]; track i) {
        <ion-item>
          <ion-skeleton-text [animated]="true" style="width: 60%"></ion-skeleton-text>
        </ion-item>
      }
    </ion-list>
  }

  @case ('empty') {
    <app-empty-state
      icon="document-text-outline"
      [title]="strings.empty.title"
      [body]="strings.empty.body"
      [ctaLabel]="strings.empty.cta"
      (ctaClick)="navigateToCadastro()"
    />
  }

  @case ('success') {
    <ion-list>
      @for (item of items(); track item.id) {
        <app-proposal-card [proposal]="item" />
      }
    </ion-list>
  }

  @case ('error') {
    <app-error-state
      [title]="strings.error.title"
      [body]="strings.error.body"
      [actionLabel]="strings.error.retry"
      (retry)="load()"
    />
  }

  @case ('offline') {
    <app-error-state
      icon="cloud-offline-outline"
      title="Você está offline"
      body="Conecte-se para ver suas propostas."
      actionLabel="Tentar novamente"
      (retry)="load()"
    />
  }
}
```

**Verificar com:** `empty-states-polish`.

**Gate Passo 5:** Se algum dos 5 estados estiver faltando, adicionar antes de avançar.

---

### Passo 6 — ACCESSIBILITY: verificação final

Antes de considerar o componente pronto:

```html
<!-- Imagens têm alt -->
<img [src]="avatar" [alt]="'Foto de ' + name" />

<!-- Botões têm label descritivo -->
<button [attr.aria-label]="'Ver proposta de ' + proposal.professional_name">
  Ver proposta
</button>

<!-- Ícones puramente decorativos têm aria-hidden -->
<ion-icon name="star" aria-hidden="true"></ion-icon>

<!-- Status dinâmico anuncia para screen reader -->
<div aria-live="polite">{{ status() }}</div>

<!-- Elementos interativos atingem 44x44px de touch target -->
<button style="min-height: 44px; min-width: 44px">...</button>
```

**Verificar com:** `accessibility-pro`.

**Gate Passo 6:** Executar checklist mínimo de a11y antes de marcar como concluído.

---

## Resumo dos gates

| Passo | Gate de saída |
|-------|---------------|
| 1 — Intent | Objetivo e plataforma definidos |
| 2 — Tokens | Zero hex hardcoded no SCSS |
| 3 — Copy | Zero strings inline em inglês ou genéricas |
| 4 — Implementation | OnPush + standalone + signals + lazy imports |
| 5 — States | 5 estados (loading/empty/success/error/offline) |
| 6 — A11y | alt, aria-label, aria-hidden, touch targets 44px |

**Nenhum PR de UI passa code review sem os 6 passos completos.**
