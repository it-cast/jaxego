import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faChevronLeft, faChevronRight, faCheck, faPencil, faXmark } from '@fortawesome/free-solid-svg-icons';
import { EquipeZonasService, TeamZonaItem } from './equipe-zonas.service';

interface ZonaRow extends TeamZonaItem {
  editing: boolean;
  editValue: string;
  saving: boolean;
}

const PAGE_SIZE = 20;

@Component({
  selector: 'jx-equipe-zonas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, FaIconComponent],
  template: `
    <section class="jx-zonas">
      <header class="jx-zonas__head">
        <h1 class="jx-zonas__title">Zonas de entrega</h1>
        <input
          type="search"
          class="jx-zonas__search"
          placeholder="Filtrar por nome..."
          [value]="query()"
          (input)="onSearch($event)"
        />
      </header>

      @if (loading()) {
        <div class="jx-zonas__feedback">Carregando zonas...</div>
      } @else if (error()) {
        <div class="jx-zonas__feedback jx-zonas__feedback--error">
          Não foi possível carregar as zonas.
          <button class="jx-zonas__retry" (click)="reload()">Tentar novamente</button>
        </div>
      } @else if (view().length === 0) {
        <div class="jx-zonas__feedback">
          Nenhuma zona cadastrada na sua área ainda.
        </div>
      } @else {
        <div class="jx-zonas__card">
          <table class="jx-zonas__table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Nome</th>
                <th>Preço mínimo</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              @for (z of paged(); track z.zona_id) {
                <tr>
                  <td class="jx-zonas__cell-id">{{ z.zona_id }}</td>
                  <td class="jx-zonas__cell-nome">{{ z.zona_nome }}</td>
                  <td class="jx-zonas__cell-preco">
                    @if (!z.editing) {
                      @if (z.preco_minimo_cents !== null) {
                        <span class="jx-zonas__badge jx-zonas__badge--set">
                          {{ formatPreco(z.preco_minimo_cents!) }}
                        </span>
                      } @else {
                        <span class="jx-zonas__badge jx-zonas__badge--none">Não configurado</span>
                      }
                    } @else {
                      <input
                        class="jx-zonas__price-input"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0,00"
                        [ngModel]="z.editValue"
                        (ngModelChange)="z.editValue = $event"
                      />
                    }
                  </td>
                  <td class="jx-zonas__cell-actions">
                    @if (!z.editing) {
                      <button
                        class="jx-zonas__action"
                        title="Definir preço mínimo"
                        (click)="startEdit(z)"
                      >
                        <fa-icon [icon]="iconEdit" aria-hidden="true" />
                      </button>
                    } @else {
                      <button
                        class="jx-zonas__action jx-zonas__action--confirm"
                        title="Salvar"
                        [disabled]="z.saving"
                        (click)="save(z)"
                      >
                        <fa-icon [icon]="iconCheck" aria-hidden="true" />
                      </button>
                      <button
                        class="jx-zonas__action jx-zonas__action--cancel"
                        title="Cancelar"
                        (click)="cancelEdit(z)"
                      >
                        <fa-icon [icon]="iconCancel" aria-hidden="true" />
                      </button>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>

        @if (totalPages() > 1) {
          <nav class="jx-zonas__pager" aria-label="Paginação de zonas">
            <button class="jx-zonas__pager-btn" (click)="prevPage()" [disabled]="page() === 0">
              <fa-icon [icon]="iconPrev" aria-hidden="true" /> Anterior
            </button>
            <span class="jx-zonas__pager-info">Página {{ page() + 1 }} de {{ totalPages() }}</span>
            <button class="jx-zonas__pager-btn" (click)="nextPage()" [disabled]="page() >= totalPages() - 1">
              Próxima <fa-icon [icon]="iconNext" aria-hidden="true" />
            </button>
          </nav>
        }
      }
    </section>
  `,
  styles: [`
    .jx-zonas { display: flex; flex-direction: column; gap: var(--jx-space-4); }

    .jx-zonas__head { display: flex; align-items: center; justify-content: space-between; gap: var(--jx-space-3); flex-wrap: wrap; }
    .jx-zonas__title { font-family: var(--jx-font-display); font-size: var(--jx-text-2xl); margin: 0; }
    .jx-zonas__search { padding: var(--jx-space-2); border: 1px solid var(--border); border-radius: var(--jx-radius-md); background: var(--surface); color: var(--text); font-size: var(--jx-text-sm); min-width: 240px; }

    .jx-zonas__feedback { padding: var(--jx-space-4); color: var(--text-muted); display: flex; align-items: center; gap: var(--jx-space-3); }
    .jx-zonas__feedback--error { color: var(--error, #d32f2f); }
    .jx-zonas__retry { border: 1px solid var(--error, #d32f2f); background: transparent; color: var(--error, #d32f2f); border-radius: var(--jx-radius-sm); padding: 4px 12px; cursor: pointer; font-size: var(--jx-text-sm); }

    .jx-zonas__card { background: var(--surface-elevated, #fff); border: 1px solid var(--border, #e5e5e5); border-radius: var(--jx-radius-xl); overflow: hidden; }

    .jx-zonas__table { width: 100%; border-collapse: collapse; font-size: var(--jx-text-sm); }
    .jx-zonas__table thead tr { background: var(--surface-sunken, #f8f8f8); }
    .jx-zonas__table th { padding: var(--jx-space-3) var(--jx-space-4); text-align: left; font-size: 11px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--text-muted); border-bottom: 1px solid var(--border); white-space: nowrap; }
    .jx-zonas__table td { padding: var(--jx-space-3) var(--jx-space-4); border-bottom: 1px solid var(--border, #eee); color: var(--text); vertical-align: middle; }
    .jx-zonas__table tbody tr:last-child td { border-bottom: none; }
    .jx-zonas__table tbody tr:hover { background: var(--bg-hover, #fafafa); }

    .jx-zonas__cell-id { color: var(--text-muted); font-size: 12px; width: 60px; }
    .jx-zonas__cell-nome { font-weight: 500; }
    .jx-zonas__cell-preco { min-width: 180px; }
    .jx-zonas__cell-actions { white-space: nowrap; width: 90px; }

    .jx-zonas__badge { display: inline-flex; align-items: center; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
    .jx-zonas__badge--set { background: var(--success-wash, hsl(140 50% 92%)); color: var(--success, #1b7a3f); }
    .jx-zonas__badge--none { background: var(--surface-sunken, #f0f0f0); color: var(--text-muted); }

    .jx-zonas__price-input { width: 120px; min-height: 36px; padding: 0 var(--jx-space-2); border: 1px solid var(--brand, #e8722a); border-radius: var(--jx-radius-md); background: var(--surface); color: var(--text); font-size: var(--jx-text-sm); }

    .jx-zonas__action { width: 36px; height: 36px; border: 1px solid var(--border, #ddd); background: var(--surface); color: var(--text-muted); border-radius: var(--jx-radius-md); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; transition: background 120ms; }
    .jx-zonas__action + .jx-zonas__action { margin-left: var(--jx-space-1); }
    .jx-zonas__action:hover:not(:disabled) { background: var(--surface-sunken); color: var(--text); }
    .jx-zonas__action--confirm { border-color: var(--success, #1b7a3f); color: var(--success, #1b7a3f); }
    .jx-zonas__action--confirm:hover:not(:disabled) { background: var(--success-wash, hsl(140 50% 92%)); }
    .jx-zonas__action--cancel { border-color: var(--error, #d32f2f); color: var(--error, #d32f2f); }
    .jx-zonas__action--cancel:hover { background: var(--error-wash, hsl(0 70% 95%)); }
    .jx-zonas__action:disabled { opacity: 0.5; cursor: not-allowed; }

    .jx-zonas__pager { display: flex; align-items: center; justify-content: center; gap: var(--jx-space-3); padding: var(--jx-space-2) 0; }
    .jx-zonas__pager-btn { display: inline-flex; align-items: center; gap: var(--jx-space-2); min-height: 36px; padding: 0 var(--jx-space-3); background: var(--surface-elevated); border: 1px solid var(--border-strong); border-radius: var(--jx-radius-lg); color: var(--text); font-family: var(--jx-font-display); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-medium); cursor: pointer; transition: background 120ms ease; }
    .jx-zonas__pager-btn:hover:not(:disabled) { background: var(--surface-sunken); }
    .jx-zonas__pager-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .jx-zonas__pager-info { font-size: var(--jx-text-sm); color: var(--text-muted); min-width: 100px; text-align: center; }
  `],
})
export class EquipeZonasPage implements OnInit {
  private readonly svc = inject(EquipeZonasService);

  protected readonly iconEdit = faPencil;
  protected readonly iconCheck = faCheck;
  protected readonly iconCancel = faXmark;
  protected readonly iconPrev = faChevronLeft;
  protected readonly iconNext = faChevronRight;

  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  private readonly items = signal<ZonaRow[]>([]);
  protected readonly query = signal('');
  protected readonly page = signal(0);

  protected readonly view = computed<ZonaRow[]>(() => {
    const q = this.query().trim().toLowerCase();
    return q
      ? this.items().filter(z => z.zona_nome.toLowerCase().includes(q))
      : this.items();
  });

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil(this.view().length / PAGE_SIZE))
  );
  protected readonly paged = computed(() => {
    const s = this.page() * PAGE_SIZE;
    return this.view().slice(s, s + PAGE_SIZE);
  });

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    this.page.set(0);
    try {
      const list = await this.svc.listZonas();
      this.items.set(
        list.map(z => ({
          ...z,
          editing: false,
          editValue: z.preco_minimo_cents !== null ? String(z.preco_minimo_cents / 100) : '',
          saving: false,
        }))
      );
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected onSearch(e: Event): void {
    this.query.set((e.target as HTMLInputElement).value);
    this.page.set(0);
  }

  protected formatPreco(cents: number): string {
    return (cents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  protected prevPage(): void { this.page.update(p => Math.max(0, p - 1)); }
  protected nextPage(): void { this.page.update(p => Math.min(this.totalPages() - 1, p + 1)); }

  protected startEdit(z: ZonaRow): void {
    this.items.update(rows =>
      rows.map(r =>
        r.zona_id === z.zona_id
          ? { ...r, editing: true, editValue: r.preco_minimo_cents !== null ? String(r.preco_minimo_cents / 100) : '' }
          : { ...r, editing: false }
      )
    );
  }

  protected cancelEdit(z: ZonaRow): void {
    this.items.update(rows =>
      rows.map(r => r.zona_id === z.zona_id ? { ...r, editing: false } : r)
    );
  }

  protected async save(z: ZonaRow): Promise<void> {
    const parsed = typeof z.editValue === 'number'
      ? z.editValue
      : parseFloat(String(z.editValue).replace(',', '.'));
    if (isNaN(parsed) || parsed < 0) return;
    const cents = Math.round(parsed * 100);

    this.items.update(rows =>
      rows.map(r => r.zona_id === z.zona_id ? { ...r, saving: true } : r)
    );

    try {
      await this.svc.setPreco(z.zona_id, cents);
      this.items.update(rows =>
        rows.map(r =>
          r.zona_id === z.zona_id
            ? { ...r, editing: false, saving: false, preco_minimo_cents: cents }
            : r
        )
      );
    } catch {
      this.items.update(rows =>
        rows.map(r => r.zona_id === z.zona_id ? { ...r, saving: false } : r)
      );
    }
  }
}
