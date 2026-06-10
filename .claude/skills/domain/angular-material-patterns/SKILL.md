# Skill: angular-material-patterns

> Padrões Angular 19 + Material M3 para o admin do {PROJETO}: MatTable server-side, MatDialog, MatSnackBar, MatDatepicker ptBR, OnPush com signals, theming M3.
> Categoria: `domain` · 2026-04-18

## Propósito

Padronizar uso de Angular Material 19 no admin do {PROJETO}. Foco em componentes que exigem mais boilerplate (tabela paginada server-side, diálogos com resultado tipado, forms com erro inline) e no uso moderno (standalone + signals + OnPush).

## Quando usar (triggers)

- Qualquer componente em `apps/admin/`
- Tabelas com paginação/filtro/ordenação server-side
- Diálogos de confirmação, criação, edição
- Formulários do admin (CRUD de categorias, serviços, etc.)
- Theming do admin (cores do {PROJETO} + Material M3)

---

## 1. Setup M3 + paleta {PROJETO}

```scss
// apps/admin/src/styles.scss
@use '@angular/material' as mat;

html {
  color-scheme: light;

  @include mat.theme((
    color: (
      primary: mat.$azure-palette,
      tertiary: mat.$cyan-palette,
    ),
    typography: Inter,
    density: 0,
  ));
}

// Override para bater com paleta {PROJETO} exata
:root {
  --mat-sys-primary: #1565C0;
  --mat-sys-on-primary: #FFFFFF;
  --mat-sys-tertiary: #00BCD4;
  --mat-sys-error: #FF1744;

  --app-gradient-header: linear-gradient(135deg, #0D3B66, #2196F3);
  --app-gradient-cta: linear-gradient(135deg, #00BCD4, #4FC3F7);
}
```

---

## 2. Locale ptBR

```typescript
// apps/admin/src/app/app.config.ts
import { LOCALE_ID } from '@angular/core';
import { registerLocaleData } from '@angular/common';
import localePt from '@angular/common/locales/pt';
import { MAT_DATE_LOCALE, provideNativeDateAdapter } from '@angular/material/core';

registerLocaleData(localePt);

export const appConfig: ApplicationConfig = {
  providers: [
    { provide: LOCALE_ID, useValue: 'pt-BR' },
    { provide: MAT_DATE_LOCALE, useValue: 'pt-BR' },
    provideNativeDateAdapter(),
    // ...
  ],
};
```

---

## 3. MatTable server-side (paginação + ordenação + filtro)

Padrão completo para lista de profissionais no admin:

```typescript
import { Component, inject, signal, viewChild, effect } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { debounceTime, distinctUntilChanged } from 'rxjs';
import { FormControl, ReactiveFormsModule } from '@angular/forms';

type LoadState = 'idle' | 'loading' | 'success' | 'error';

@Component({
  selector: 'app-professionals-list',
  standalone: true,
  imports: [
    MatTableModule, MatPaginatorModule, MatSortModule,
    MatFormFieldModule, MatInputModule, MatProgressBarModule,
    ReactiveFormsModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-form-field appearance="outline">
      <mat-label>Buscar profissional</mat-label>
      <input matInput [formControl]="searchCtrl" placeholder="Nome, CPF, cidade" />
    </mat-form-field>

    @if (state() === 'loading') {
      <mat-progress-bar mode="indeterminate" />
    }

    <table mat-table [dataSource]="items()" matSort (matSortChange)="onSortChange($event)">
      <ng-container matColumnDef="name">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Nome</th>
        <td mat-cell *matCellDef="let p">{{ p.name }}</td>
      </ng-container>
      <ng-container matColumnDef="status">
        <th mat-header-cell *matHeaderCellDef mat-sort-header>Status</th>
        <td mat-cell *matCellDef="let p">
          <span class="badge" [class.approved]="p.status === 'approved'">
            {{ p.status | statusLabel }}
          </span>
        </td>
      </ng-container>
      <!-- mais colunas -->

      <tr mat-header-row *matHeaderRowDef="displayedCols"></tr>
      <tr mat-row *matRowDef="let row; columns: displayedCols" (click)="goToDetail(row)"></tr>
    </table>

    @if (state() === 'success' && items().length === 0) {
      <app-empty-state icon="group_off" message="Nenhum profissional encontrado" />
    }

    <mat-paginator
      [length]="total()"
      [pageSize]="20"
      [pageSizeOptions]="[10, 20, 50]"
      (page)="onPageChange($event)"
    />
  `,
})
export class ProfessionalsListComponent {
  private api = inject(ProfessionalsAdminService);

  state = signal<LoadState>('idle');
  items = signal<Professional[]>([]);
  total = signal(0);

  page = signal(0);
  pageSize = signal(20);
  sort = signal<{ active: string; direction: 'asc' | 'desc' }>({ active: 'name', direction: 'asc' });

  searchCtrl = new FormControl('', { nonNullable: true });
  displayedCols = ['name', 'cpf', 'city', 'status', 'rating'];

  constructor() {
    // Debounce de busca
    this.searchCtrl.valueChanges
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed())
      .subscribe(() => {
        this.page.set(0);  // reset para primeira página
        this.reload();
      });

    // Effect recarrega quando page/pageSize/sort mudam
    effect(() => {
      this.page(); this.pageSize(); this.sort();
      this.reload();
    });
  }

  private async reload() {
    this.state.set('loading');
    try {
      const { items, total } = await this.api.list({
        q: this.searchCtrl.value,
        page: this.page(),
        pageSize: this.pageSize(),
        sort: this.sort().active,
        order: this.sort().direction,
      });
      this.items.set(items);
      this.total.set(total);
      this.state.set('success');
    } catch (error) {
      this.state.set('error');
    }
  }

  onPageChange(e: PageEvent) {
    this.page.set(e.pageIndex);
    this.pageSize.set(e.pageSize);
  }

  onSortChange(e: Sort) {
    if (e.direction === '') return;
    this.sort.set({ active: e.active, direction: e.direction });
  }
}
```

---

## 4. MatDialog com resultado tipado

```typescript
// Evita `any` no result do afterClosed
export interface ApproveDialogResult {
  approved: boolean;
  notes?: string;
}

export interface ApproveDialogData {
  professionalName: string;
}

@Component({
  standalone: true,
  imports: [MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule, ReactiveFormsModule],
  template: `
    <h2 mat-dialog-title>Aprovar {{ data.professionalName }}?</h2>
    <mat-dialog-content>
      <p>O profissional poderá receber solicitações de orçamento após aprovação.</p>
      <mat-form-field appearance="outline">
        <mat-label>Observações (opcional)</mat-label>
        <textarea matInput [formControl]="notesCtrl" rows="3"></textarea>
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button [mat-dialog-close]="{ approved: false }">Cancelar</button>
      <button mat-flat-button color="primary"
              [mat-dialog-close]="{ approved: true, notes: notesCtrl.value }">
        Aprovar
      </button>
    </mat-dialog-actions>
  `,
})
export class ApproveDialogComponent {
  data = inject<ApproveDialogData>(MAT_DIALOG_DATA);
  notesCtrl = new FormControl('', { nonNullable: true });
}

// Uso:
const ref = this.dialog.open<ApproveDialogComponent, ApproveDialogData, ApproveDialogResult>(
  ApproveDialogComponent,
  { data: { professionalName: prof.name }, width: '480px' },
);
const result = await firstValueFrom(ref.afterClosed());
if (result?.approved) {
  await this.api.approve(prof.id, result.notes);
}
```

---

## 5. MatSnackBar com ptBR e ações

```typescript
@Injectable({ providedIn: 'root' })
export class ToastService {
  private sb = inject(MatSnackBar);

  success(message: string) {
    this.sb.open(message, 'OK', {
      duration: 3000,
      panelClass: ['snack-success'],
      horizontalPosition: 'end',
      verticalPosition: 'top',
    });
  }

  error(message: string) {
    this.sb.open(message, 'Fechar', {
      duration: 6000,
      panelClass: ['snack-error'],
    });
  }

  info(message: string) {
    this.sb.open(message, 'OK', { duration: 3000 });
  }
}
```

---

## 6. Form com MatFormField (appearance outline + ptBR)

```typescript
@Component({
  template: `
    <form [formGroup]="form" (ngSubmit)="save()">
      <mat-form-field appearance="outline">
        <mat-label>Nome da categoria</mat-label>
        <input matInput formControlName="name" />
        @if (form.controls.name.hasError('required') && form.controls.name.touched) {
          <mat-error>Nome é obrigatório</mat-error>
        }
        @if (form.controls.name.hasError('maxlength')) {
          <mat-error>Máximo 50 caracteres</mat-error>
        }
        <mat-hint align="end">{{ form.controls.name.value.length }}/50</mat-hint>
      </mat-form-field>

      <mat-form-field appearance="outline">
        <mat-label>Cor</mat-label>
        <input matInput type="color" formControlName="color" />
      </mat-form-field>

      <button mat-flat-button color="primary" type="submit" [disabled]="form.invalid">
        Salvar
      </button>
    </form>
  `,
})
```

---

## 7. OnPush + signals (obrigatório no {PROJETO} admin)

```typescript
@Component({
  // ...
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent {
  private api = inject(DashboardService);

  stats = signal<Stats | null>(null);
  state = signal<LoadState>('loading');

  // Computed derivado
  totalRevenue = computed(() => this.stats()?.payments?.total ?? 0);
  usersDelta = computed(() => {
    const s = this.stats();
    if (!s) return 0;
    return ((s.users.thisMonth - s.users.lastMonth) / s.users.lastMonth) * 100;
  });

  constructor() {
    this.load();
  }

  async load() {
    this.state.set('loading');
    try {
      const stats = await this.api.getStats();
      this.stats.set(stats);
      this.state.set('success');
    } catch {
      this.state.set('error');
    }
  }
}
```

---

## 8. Empty / Loading / Error states — padrão LoadState machine

```typescript
export type LoadState = 'idle' | 'loading' | 'success' | 'error';
```

```html
@switch (state()) {
  @case ('loading') {
    <div class="skeleton-list">
      <ngx-skeleton-loader count="5" />
    </div>
  }
  @case ('error') {
    <app-error-state (retry)="load()" />
  }
  @case ('success') {
    @if (items().length === 0) {
      <app-empty-state icon="inbox" message="Nada por aqui ainda" />
    } @else {
      <table mat-table>...</table>
    }
  }
}
```

Detalhe em `empty-states-polish`.

---

## Anti-patterns

1. ❌ **Usar `NgModules`** — admin {PROJETO} é 100% standalone
2. ❌ **`ChangeDetectionStrategy.Default`** em componente novo — performance ruim
3. ❌ **`dataSource = new MatTableDataSource(arr)`** com array grande — carrega tudo, ignora paginação; use API server-side
4. ❌ **Dialog sem tipo no `MAT_DIALOG_DATA`** — vira `any`, perde type safety
5. ❌ **Filtro de busca sem debounce** — dispara request em cada tecla
6. ❌ **`panelClass: 'snack-error'`** sem CSS correspondente em `styles.scss` — nada aparece
7. ❌ **Hardcode de cor** (`color="#1565C0"`) em vez de usar var CSS do tema
8. ❌ **`mat-error` fora de `mat-form-field`** — não renderiza
9. ❌ **`[formGroup]` sem `.invalid` check no botão submit** — permite clicar com form inválido
10. ❌ **Formulário sem `trackBy`** em `*ngFor` — relayout desnecessário

---

## Checklist de review

- [ ] `changeDetection: ChangeDetectionStrategy.OnPush`
- [ ] Component standalone, não NgModule
- [ ] Signals para estado local, não `BehaviorSubject`
- [ ] MatTable com paginação server-side (`length`, `pageSize`, `(page)`)
- [ ] Filtro/busca com `debounceTime(300)`
- [ ] Dialog tipado (generics no `open<C, D, R>`)
- [ ] SnackBar chamada via `ToastService` centralizado
- [ ] Estados loading/empty/error visíveis
- [ ] Locale ptBR configurado
- [ ] Erros de form dentro de `mat-form-field > mat-error`
- [ ] Cores vêm de CSS vars (`var(--mat-sys-primary)`)

<!-- Skill aplicada: toda tela em apps/admin/ -->
