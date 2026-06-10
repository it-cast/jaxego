# Skill: saas-dashboard-patterns

> Padrões de dashboard SaaS moderno (Linear, Stripe, Vercel, Linear, Retool): sidebar colapsável, KPI cards com delta, charts com cores semânticas, empty states de dashboard, filter bars, command palette, tables pro-level.
> Categoria: `ux-advanced` · 2026-04-18

## Propósito

O admin Angular do {PROJETO} tem dashboard com 6 KPIs (já existe) e vai evoluir pra gráficos de receita, contratações, dashboards financeiros do profissional (Fase 2). Esta skill é o playbook específico de padrões SaaS — não "como fazer gráfico" em geral.

## Quando usar (triggers)

- Qualquer tela do tipo "dashboard" (admin ou profissional)
- KPIs, gráficos, tabelas paginadas
- Layout com sidebar + main area
- Relatórios, analytics
- Filtros complexos (date range, múltiplos campos)

## Quando NÃO usar

- Tela simples sem dados agregados → skills básicas bastam
- Mobile puro → padrões são desktop-first; adaptar com responsive-breakpoint-strategy
- Componentes fundamentais → use angular-material-patterns

---

## 1. Layout — sidebar + main

```typescript
@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [MatSidenavModule, MatListModule, MatIconModule, RouterLink, RouterOutlet],
  template: `
    <mat-sidenav-container class="shell">
      <mat-sidenav
        #sidenav
        [mode]="isDesktop() ? 'side' : 'over'"
        [opened]="isDesktop()"
        [class.collapsed]="collapsed()"
      >
        <div class="sidenav-header">
          <img src="/assets/logo.svg" alt="{PROJETO}" />
          <button mat-icon-button (click)="collapsed.update(c => !c)">
            <mat-icon>{{ collapsed() ? 'chevron_right' : 'chevron_left' }}</mat-icon>
          </button>
        </div>

        <mat-nav-list>
          @for (item of navItems; track item.path) {
            <a mat-list-item [routerLink]="item.path" routerLinkActive="active">
              <mat-icon matListItemIcon>{{ item.icon }}</mat-icon>
              <span matListItemTitle>{{ item.label }}</span>
              @if (item.badge) {
                <span class="badge">{{ item.badge() }}</span>
              }
            </a>
          }
        </mat-nav-list>

        <div class="sidenav-footer">
          <button mat-button (click)="openCommandPalette()">
            <mat-icon>search</mat-icon>
            <span>Buscar</span>
            <kbd>⌘K</kbd>
          </button>
        </div>
      </mat-sidenav>

      <mat-sidenav-content>
        <header class="topbar">
          <button mat-icon-button (click)="sidenav.toggle()">
            <mat-icon>menu</mat-icon>
          </button>
          <app-breadcrumbs />
          <div class="topbar-actions">
            <button mat-icon-button><mat-icon>notifications</mat-icon></button>
            <button mat-icon-button [matMenuTriggerFor]="userMenu">
              <img [src]="user().avatar" alt="" class="avatar" />
            </button>
          </div>
        </header>

        <main class="content">
          <router-outlet />
        </main>
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
})
export class ShellComponent {
  collapsed = signal(false);
  isDesktop = toSignal(
    inject(BreakpointObserver).observe(['(min-width: 1024px)']).pipe(map(r => r.matches)),
    { initialValue: true },
  );
}
```

### Nav items (hierarquia)

```typescript
navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
  { label: 'Profissionais', path: '/professionals', icon: 'engineering', badge: this.pendingModeration },
  { label: 'Solicitações', path: '/requests', icon: 'description' },
  { label: 'Pagamentos', path: '/payments', icon: 'account_balance_wallet' },
  { label: 'Categorias', path: '/categories', icon: 'category' },
  { label: 'Configurações', path: '/settings', icon: 'settings' },
];
```

---

## 2. KPI cards com delta

Padrão universal de dashboard moderno: número grande + delta vs período anterior + mini sparkline (opcional).

```typescript
@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [MatCardModule, MatIconModule, CommonModule],
  template: `
    <mat-card>
      <div class="kpi-header">
        <span class="kpi-label">{{ label }}</span>
        <mat-icon class="kpi-icon" [style.color]="iconColor">{{ icon }}</mat-icon>
      </div>

      <div class="kpi-value">{{ formattedValue() }}</div>

      <div class="kpi-delta" [class.positive]="delta() > 0" [class.negative]="delta() < 0">
        <mat-icon>{{ delta() > 0 ? 'trending_up' : 'trending_down' }}</mat-icon>
        <span>{{ deltaFormatted() }}</span>
        <span class="kpi-period">vs {{ comparisonLabel }}</span>
      </div>
    </mat-card>
  `,
  styles: [`
    mat-card { padding: 20px; }
    .kpi-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
    .kpi-label { color: var(--mat-sys-on-surface-variant); font-size: 13px; }
    .kpi-icon { opacity: 0.7; }
    .kpi-value { font-size: 28px; font-weight: 600; line-height: 1.2; }
    .kpi-delta { display: flex; align-items: center; gap: 4px; margin-top: 8px; font-size: 13px; }
    .kpi-delta.positive { color: #00C853; }
    .kpi-delta.negative { color: #FF1744; }
    .kpi-period { color: var(--mat-sys-on-surface-variant); margin-left: 4px; }
  `],
})
export class KpiCardComponent {
  @Input({ required: true }) label!: string;
  @Input({ required: true }) value!: number;
  @Input() previousValue = 0;
  @Input() format: 'number' | 'currency' | 'percent' = 'number';
  @Input() icon = 'bar_chart';
  @Input() iconColor = 'var(--mat-sys-primary)';
  @Input() comparisonLabel = 'mês anterior';

  delta = computed(() => {
    if (!this.previousValue) return 0;
    return ((this.value - this.previousValue) / this.previousValue) * 100;
  });

  deltaFormatted = computed(() => {
    const d = this.delta();
    return `${d > 0 ? '+' : ''}${d.toFixed(1)}%`;
  });

  formattedValue = computed(() => {
    switch (this.format) {
      case 'currency':
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(this.value);
      case 'percent':
        return `${this.value.toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('pt-BR').format(this.value);
    }
  });
}
```

### Uso no dashboard {PROJETO}

```html
<div class="kpi-grid">
  <app-kpi-card
    label="Profissionais ativos"
    [value]="stats().activeProfessionals"
    [previousValue]="stats().activeProfessionalsPrev"
    icon="engineering"
  />
  <app-kpi-card
    label="Contratações do mês"
    [value]="stats().serviceRequests"
    [previousValue]="stats().serviceRequestsPrev"
    icon="assignment_turned_in"
  />
  <app-kpi-card
    label="Receita retida (escrow)"
    [value]="stats().escrowAmount"
    [previousValue]="stats().escrowAmountPrev"
    format="currency"
    icon="lock"
  />
  <app-kpi-card
    label="Taxa da plataforma"
    [value]="stats().platformFees"
    [previousValue]="stats().platformFeesPrev"
    format="currency"
    icon="payments"
  />
</div>
```

---

## 3. Charts — cores semânticas, não arco-íris

Use **Chart.js 4** ou **Apex Charts** (não `ngx-charts` que está em manutenção limitada).

### Regras de cor

| Contexto | Cor |
|---|---|
| Receita / crescimento / sucesso | `#00C853` (verde) |
| Despesa / queda / erro | `#FF1744` (vermelho) |
| Neutro / principal | `var(--mat-sys-primary)` `#1565C0` |
| Secundário / informativo | `var(--mat-sys-tertiary)` `#00BCD4` |
| Alerta / pendente | `#FFD600` (amarelo) |
| Destaque / energia | `#FF6D00` (laranja) |

**Não** usar paleta arco-íris de 10 cores — confuso.

### Linha de tendência (receita ao longo do tempo)

```typescript
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

@Component({
  template: `<canvas #chart></canvas>`,
})
export class RevenueTrendComponent {
  @ViewChild('chart', { static: true }) chartRef!: ElementRef<HTMLCanvasElement>;
  @Input({ required: true }) data!: { date: string; revenue: number }[];

  ngAfterViewInit() {
    new Chart(this.chartRef.nativeElement, {
      type: 'line',
      data: {
        labels: this.data.map(d => d.date),
        datasets: [{
          label: 'Receita',
          data: this.data.map(d => d.revenue),
          borderColor: '#00C853',
          backgroundColor: 'rgba(0, 200, 83, 0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => `R$ ${new Intl.NumberFormat('pt-BR').format(ctx.parsed.y)}`,
            },
          },
        },
        scales: {
          y: {
            ticks: {
              callback: (v) => `R$ ${new Intl.NumberFormat('pt-BR', { notation: 'compact' }).format(v as number)}`,
            },
          },
        },
      },
    });
  }
}
```

### Quando usar qual chart

| Tipo | Use para | Evite |
|---|---|---|
| **Line** | Tendência no tempo (receita diária) | Comparar < 5 pontos |
| **Bar** | Comparar categorias (top 10 categorias por contratação) | Tendência (use line) |
| **Stacked bar** | Composição ao longo do tempo (Pix vs Cartão por mês) | > 5 camadas |
| **Pie/Donut** | Participação quando soma = 100% e ≤ 5 fatias | > 5 categorias (use bar horizontal) |
| **Sparkline** | Mini-trend em KPI card | Dado isolado |
| **Heatmap** | Padrão em 2 dimensões (dia da semana × horário) | Dado linear |
| **Gauge** | Meta % atingida | Múltiplos valores (use bar) |

---

## 4. Data tables pro-level

Ver `angular-material-patterns` para implementação base. Adições dashboard-specific:

### Column visibility toggle

```html
<button mat-button [matMenuTriggerFor]="colsMenu">
  <mat-icon>view_column</mat-icon>
  Colunas
</button>
<mat-menu #colsMenu>
  @for (col of allColumns; track col.key) {
    <mat-checkbox [checked]="isVisible(col.key)" (change)="toggleColumn(col.key)">
      {{ col.label }}
    </mat-checkbox>
  }
</mat-menu>
```

### Export CSV

```typescript
exportCsv() {
  const rows = this.items();
  const cols = this.visibleColumns();
  const csv = [
    cols.map(c => c.label).join(','),
    ...rows.map(r => cols.map(c => JSON.stringify(r[c.key] ?? '')).join(',')),
  ].join('\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });  // BOM para Excel ptBR
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${this.filename()}-${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
```

---

## 5. Filter bar padrão

```html
<div class="filter-bar">
  <mat-form-field appearance="outline">
    <mat-label>Período</mat-label>
    <mat-date-range-input [rangePicker]="picker">
      <input matStartDate [formControl]="startCtrl" />
      <input matEndDate [formControl]="endCtrl" />
    </mat-date-range-input>
    <mat-datepicker-toggle matIconSuffix [for]="picker" />
    <mat-date-range-picker #picker />
  </mat-form-field>

  <mat-form-field appearance="outline">
    <mat-label>Status</mat-label>
    <mat-select [formControl]="statusCtrl" multiple>
      <mat-option value="pending">Pendente</mat-option>
      <mat-option value="held">Retido</mat-option>
      <mat-option value="released">Liberado</mat-option>
      <mat-option value="refunded">Estornado</mat-option>
    </mat-select>
  </mat-form-field>

  <button mat-button (click)="clearFilters()" *ngIf="hasActiveFilters()">
    Limpar filtros
  </button>
  <span class="filter-count" *ngIf="hasActiveFilters()">
    {{ activeFiltersCount() }} filtro(s) ativo(s)
  </span>
</div>
```

---

## 6. Command Palette (Cmd+K)

Inspirado em Linear, Superhuman. Não crítico no MVP, mas eleva o framework:

```typescript
@Component({
  template: `
    <mat-dialog-content class="command-palette">
      <input
        matInput
        [formControl]="queryCtrl"
        placeholder="Digite um comando ou busque..."
        #input
      />
      <mat-divider />
      <mat-list>
        @for (cmd of results(); track cmd.id) {
          <mat-list-item (click)="execute(cmd)" [class.selected]="cmd === selected()">
            <mat-icon matListItemIcon>{{ cmd.icon }}</mat-icon>
            <span matListItemTitle>{{ cmd.label }}</span>
            <span matListItemMeta>{{ cmd.category }}</span>
          </mat-list-item>
        }
      </mat-list>
    </mat-dialog-content>
  `,
})
```

Binding global:

```typescript
@HostListener('document:keydown.meta.k', ['$event'])
@HostListener('document:keydown.control.k', ['$event'])
onCmdK(event: KeyboardEvent) {
  event.preventDefault();
  this.dialog.open(CommandPaletteComponent, { width: '600px' });
}
```

Comandos típicos: "Ir para profissionais", "Ir para pagamentos pendentes", "Aprovar profissional...", "Buscar por CPF".

---

## 7. Mobile-first dashboard

Admin é desktop-first mas tem que ser utilizável no mobile (Cadu vai conferir no celular).

- KPIs: 1 coluna abaixo de 640px, 2 colunas até 1024px, 3-4 acima
- Sidebar: overlay no mobile (modo "over"), persistente no desktop
- Tabela: scrolling horizontal + colunas prioritárias visíveis primeiro
- Filter bar: colapsa em accordion no mobile

---

## Anti-patterns

1. ❌ **Pizza com 10 fatias** — pie/donut só com ≤ 5
2. ❌ **KPI sem comparação** — número isolado não significa nada
3. ❌ **Gráfico sem formatação ptBR** — `1,234.56` em vez de `1.234,56`
4. ❌ **Arco-íris de cores** — usuário não decodifica o que cada cor significa
5. ❌ **Tabela sem loading/empty/error** — vazio confunde
6. ❌ **Dashboard denso sem breathing room** — Linear usa 24px+ de padding entre seções
7. ❌ **Sidebar que não fecha no mobile** — cobre metade da tela
8. ❌ **Breadcrumb com nomes técnicos** ("admin-dashboard-route") — use labels ptBR
9. ❌ **Export CSV sem BOM** — Excel ptBR vira caracteres estranhos
10. ❌ **Filtro sem indicação de estado ativo** — usuário esquece que filtrou e vê dados parciais

---

## Checklist de review

- [ ] KPI cards têm value + delta + período de comparação
- [ ] Charts usam cores semânticas (verde/vermelho para +/−)
- [ ] Todo valor BRL formatado `pt-BR` (`R$ 1.234,56`)
- [ ] Tabelas pro-level: sort, filter, paginação, column visibility, export
- [ ] Sidebar colapsa no mobile, persistente no desktop
- [ ] Filtros com indicação de estado ativo
- [ ] Breadcrumb visível
- [ ] Empty/loading/error states em todo componente de dados
- [ ] Command palette (Cmd+K) implementada (bonus)
- [ ] Responsive: KPIs em 1-2-3-4 colunas conforme viewport
- [ ] Export CSV com BOM para Excel ptBR
- [ ] Sem paleta arco-íris

<!-- Skill aplicada: apps/admin/src/app/**/*dashboard*, *stats*, *report* -->
