import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faPlus,
  faPenToSquare,
  faTrashCan,
  faCheck,
  faXmark,
  faChevronLeft,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons';
import { AdminZonasService, Zona } from './zonas.service';
import { AreaMapComponent } from '../../admin-plataforma/area-map.component';

type ViewMode = 'list' | 'create' | 'edit';

@Component({
  selector: 'jx-zonas-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, DataTableComponent, FaIconComponent, AreaMapComponent],
  template: `
    <main class="jx-zonas">
      <header class="jx-zonas__header">
        <h1 class="jx-zonas__title">Zonas</h1>
        @if (mode() === 'list') {
          <button type="button" class="jx-zonas__cta" (click)="showCreate()">
            <fa-icon [icon]="iconPlus" aria-hidden="true" /> Adicionar
          </button>
        }
      </header>

      @if (msg(); as m) {
        <div class="jx-zonas__msg" [class.jx-zonas__msg--ok]="m.tone === 'ok'" [class.jx-zonas__msg--err]="m.tone === 'err'" role="status">
          {{ m.text }}
        </div>
      }

      @if (mode() === 'create' || mode() === 'edit') {
        <section class="jx-zonas__form-card">
          <h2 class="jx-zonas__form-title">{{ mode() === 'create' ? 'Nova zona' : 'Editar zona' }}</h2>
          <form class="jx-zonas__form" (ngSubmit)="save()">
            <label class="jx-zonas__field">
              <span class="jx-zonas__label">Nome da zona</span>
              <input
                class="jx-zonas__input"
                type="text"
                [(ngModel)]="formName"
                name="name"
                required
                maxlength="160"
                placeholder="Ex: Norte, Centro, Zona Sul"
              />
            </label>
            <div class="jx-zonas__field">
              <span class="jx-zonas__label">Polígono da zona</span>
              <jx-area-map
                [boundary]="formBoundary"
                (boundaryChange)="formBoundary = $event"
              />
              <span class="jx-zonas__hint">Desenhe o polígono que delimita esta zona no mapa.</span>
            </div>
            <div class="jx-zonas__form-actions">
              <button type="submit" class="jx-zonas__cta" [disabled]="saving() || !formName.trim()">
                <fa-icon [icon]="iconSave" aria-hidden="true" />
                {{ saving() ? 'Salvando...' : 'Salvar' }}
              </button>
              <button type="button" class="jx-zonas__btn-secondary" (click)="cancel()">
                <fa-icon [icon]="iconCancel" aria-hidden="true" /> Cancelar
              </button>
            </div>
          </form>
        </section>
      }

      @if (mode() === 'list') {
        <div class="jx-zonas__search">
          <input
            class="jx-zonas__input"
            type="search"
            placeholder="Buscar zona..."
            [(ngModel)]="searchQuery"
            (ngModelChange)="applyFilter()"
          />
        </div>

        <jx-data-table
          [columns]="columns"
          [rows]="filteredRows()"
          [state]="tableState()"
          [trackBy]="trackById"
          caption="Zonas da área"
          emptyIcon="🗺️"
          emptyTitle="Nenhuma zona cadastrada"
          emptyMessage="Crie a primeira zona clicando em '+ Adicionar'."
          errorMessage="Não foi possível carregar as zonas."
          (retry)="load()"
        >
          <ng-template #row let-item>
            <td class="jx-zonas__num">{{ item.id }}</td>
            <td>{{ item.name }}</td>
            <td>
              @if (item.boundary) {
                <span class="jx-zonas__badge jx-zonas__badge--yes">Com polígono</span>
              } @else {
                <span class="jx-zonas__badge jx-zonas__badge--no">Sem polígono</span>
              }
            </td>
            <td class="jx-zonas__actions">
              @if (confirmRemoveId() === item.id) {
                <span class="jx-zonas__confirm-msg">Remover?</span>
                <button type="button" class="jx-zonas__action-btn jx-zonas__action-btn--danger" (click)="doRemove(item.id)">
                  <fa-icon [icon]="iconSave" aria-hidden="true" />
                </button>
                <button type="button" class="jx-zonas__action-btn" (click)="cancelConfirmRemove()">
                  <fa-icon [icon]="iconCancel" aria-hidden="true" />
                </button>
              } @else {
                <button type="button" class="jx-zonas__action-btn" (click)="showEdit(item)" aria-label="Editar">
                  <fa-icon [icon]="iconEdit" aria-hidden="true" />
                </button>
                <button type="button" class="jx-zonas__action-btn jx-zonas__action-btn--danger" (click)="confirmRemove(item.id)" aria-label="Remover">
                  <fa-icon [icon]="iconRemove" aria-hidden="true" />
                </button>
              }
            </td>
          </ng-template>
        </jx-data-table>

        @if (totalPages > 1) {
          <div class="jx-zonas__pagination">
            <button class="jx-zonas__page-btn" [disabled]="currentPage() === 0" (click)="goPage(currentPage() - 1)" aria-label="Página anterior">
              <fa-icon [icon]="iconPrev" aria-hidden="true" /> Anterior
            </button>
            <span class="jx-zonas__page-info">Página {{ currentPage() + 1 }} de {{ totalPages }}</span>
            <button class="jx-zonas__page-btn" [disabled]="currentPage() >= totalPages - 1" (click)="goPage(currentPage() + 1)" aria-label="Próxima página">
              Próxima <fa-icon [icon]="iconNext" aria-hidden="true" />
            </button>
          </div>
        }
      }
    </main>
  `,
  styles: [`
    .jx-zonas { display: flex; flex-direction: column; gap: var(--jx-space-4); }
    .jx-zonas__header { display: flex; align-items: center; justify-content: space-between; }
    .jx-zonas__title { margin: 0; font-family: var(--jx-font-display); font-size: var(--jx-text-2xl); font-weight: var(--jx-weight-bold); color: var(--text); }
    .jx-zonas__cta { display: flex; align-items: center; gap: var(--jx-space-1); min-height: 44px; padding: 0 var(--jx-space-3); border: 0; border-radius: var(--jx-radius-lg); background: var(--brand); color: var(--brand-contrast, #fff); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); cursor: pointer; }
    .jx-zonas__cta:disabled { opacity: 0.6; cursor: default; }
    .jx-zonas__btn-secondary { display: flex; align-items: center; gap: var(--jx-space-1); min-height: 44px; padding: 0 var(--jx-space-3); border: 1px solid var(--border); border-radius: var(--jx-radius-lg); background: transparent; color: var(--text); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); cursor: pointer; }
    .jx-zonas__msg { padding: var(--jx-space-3) var(--jx-space-4); border-radius: var(--jx-radius-lg); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); }
    .jx-zonas__msg--ok { background: var(--success-wash, var(--brand-wash)); color: var(--success, var(--brand)); }
    .jx-zonas__msg--err { background: var(--error-wash, hsl(0 70% 95%)); color: var(--error); }
    .jx-zonas__form-card { background: var(--surface-elevated); border: 1px solid var(--border); border-radius: var(--jx-radius-xl); padding: var(--jx-space-5); display: flex; flex-direction: column; gap: var(--jx-space-4); }
    .jx-zonas__form-title { margin: 0; font-family: var(--jx-font-display); font-size: var(--jx-text-lg); font-weight: var(--jx-weight-bold); color: var(--text); }
    .jx-zonas__form { display: flex; flex-direction: column; gap: var(--jx-space-3); }
    .jx-zonas__field { display: flex; flex-direction: column; gap: var(--jx-space-1); }
    .jx-zonas__label { font-size: var(--jx-text-xs); font-weight: var(--jx-weight-semibold); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
    .jx-zonas__input { min-height: 44px; padding: 0 var(--jx-space-3); border: 1px solid var(--border-strong, var(--border)); border-radius: var(--jx-radius-lg); font-size: var(--jx-text-base); color: var(--text); background: var(--surface); }
    .jx-zonas__input:focus { outline: none; border-color: var(--brand); }
    .jx-zonas__hint { font-size: var(--jx-text-xs); color: var(--text-muted); }
    .jx-zonas__form-actions { display: flex; gap: var(--jx-space-2); }
    .jx-zonas__num { font-size: var(--jx-text-sm); color: var(--text-muted); font-variant-numeric: tabular-nums; }
    .jx-zonas__badge { font-size: var(--jx-text-xs); font-weight: 600; padding: 2px 8px; border-radius: 999px; }
    .jx-zonas__badge--yes { background: var(--brand-wash, hsl(24 80% 95%)); color: var(--brand, #e8722a); }
    .jx-zonas__badge--no { background: var(--surface-sunken); color: var(--text-muted); }
    .jx-zonas__actions { display: flex; gap: var(--jx-space-1); }
    .jx-zonas__action-btn { min-width: 36px; min-height: 36px; display: grid; place-items: center; border: 0; border-radius: var(--jx-radius-md); background: var(--surface-sunken); color: var(--text-muted); cursor: pointer; font-size: 14px; }
    .jx-zonas__action-btn:hover { background: var(--surface-elevated); color: var(--text); }
    .jx-zonas__action-btn--danger:hover { color: var(--error); }
    .jx-zonas__confirm-msg { font-size: var(--jx-text-xs); color: var(--error); font-weight: 600; margin-right: var(--jx-space-1); }
    .jx-zonas__pagination { display: flex; align-items: center; justify-content: center; gap: var(--jx-space-3); padding: var(--jx-space-3) 0; }
    .jx-zonas__page-btn { min-height: 36px; padding: 0 var(--jx-space-3); border: 1px solid var(--border); border-radius: var(--jx-radius-md); background: var(--surface); color: var(--text); font-size: var(--jx-text-sm); cursor: pointer; display: flex; align-items: center; gap: var(--jx-space-1); }
    .jx-zonas__page-btn:hover:not(:disabled) { background: var(--surface-elevated); }
    .jx-zonas__page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .jx-zonas__page-info { font-size: var(--jx-text-sm); color: var(--text-muted); font-weight: 600; }
    .jx-zonas__search { margin-bottom: 0; }
  `],
})
export class ZonasPage implements OnInit {
  private readonly service = inject(AdminZonasService);

  protected readonly iconPlus = faPlus;
  protected readonly iconEdit = faPenToSquare;
  protected readonly iconRemove = faTrashCan;
  protected readonly iconSave = faCheck;
  protected readonly iconCancel = faXmark;
  protected readonly iconPrev = faChevronLeft;
  protected readonly iconNext = faChevronRight;

  protected readonly columns: DataTableColumn[] = [
    { key: 'id', label: 'ID', numeric: true },
    { key: 'name', label: 'Nome' },
    { key: 'boundary', label: 'Polígono' },
    { key: 'actions', label: 'Ações' },
  ];

  private allRows: Zona[] = [];
  protected readonly filteredRows = signal<Zona[]>([]);
  protected readonly tableState = signal<DataTableState>('loading');
  protected readonly mode = signal<ViewMode>('list');
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected readonly saving = signal(false);
  protected readonly confirmRemoveId = signal<number | null>(null);
  protected readonly currentPage = signal(0);
  protected readonly PAGE_SIZE = 20;

  protected searchQuery = '';
  protected formName = '';
  protected formBoundary: object | null = null;
  private editingId: number | null = null;

  protected get totalPages(): number {
    return Math.ceil(this.filteredRows().length / this.PAGE_SIZE);
  }

  protected readonly trackById = (item: unknown): number => (item as Zona).id;

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  protected async load(): Promise<void> {
    this.tableState.set('loading');
    try {
      const list = await this.service.list();
      this.allRows = list;
      this.applyFilter();
      this.tableState.set(list.length === 0 ? 'empty' : 'ready');
    } catch {
      this.tableState.set('error');
    }
  }

  protected applyFilter(): void {
    const q = this.searchQuery.trim().toLowerCase();
    const filtered = q ? this.allRows.filter(z => z.name.toLowerCase().includes(q)) : this.allRows;
    this.filteredRows.set(filtered);
    this.currentPage.set(0);
  }

  protected goPage(page: number): void {
    this.currentPage.set(page);
  }

  protected showCreate(): void {
    this.formName = '';
    this.formBoundary = null;
    this.editingId = null;
    this.msg.set(null);
    this.mode.set('create');
  }

  protected showEdit(zona: Zona): void {
    this.formName = zona.name;
    this.formBoundary = zona.boundary;
    this.editingId = zona.id;
    this.msg.set(null);
    this.mode.set('edit');
  }

  protected cancel(): void {
    this.mode.set('list');
    this.editingId = null;
    this.msg.set(null);
  }

  protected async save(): Promise<void> {
    const name = this.formName.trim();
    if (!name) return;
    this.saving.set(true);
    try {
      if (this.editingId !== null) {
        await this.service.update(this.editingId, { name, boundary: this.formBoundary });
        this.msg.set({ text: 'Zona atualizada com sucesso.', tone: 'ok' });
      } else {
        await this.service.create({ name, boundary: this.formBoundary });
        this.msg.set({ text: 'Zona adicionada com sucesso.', tone: 'ok' });
      }
      this.mode.set('list');
      this.editingId = null;
      await this.load();
    } catch {
      this.msg.set({ text: 'Não conseguimos salvar a zona. Tente de novo.', tone: 'err' });
    } finally {
      this.saving.set(false);
    }
  }

  protected confirmRemove(id: number): void {
    this.confirmRemoveId.set(id);
  }

  protected cancelConfirmRemove(): void {
    this.confirmRemoveId.set(null);
  }

  protected async doRemove(id: number): Promise<void> {
    this.confirmRemoveId.set(null);
    try {
      await this.service.remove(id);
      this.msg.set({ text: 'Zona removida.', tone: 'ok' });
      await this.load();
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 409) {
        this.msg.set({ text: err.error?.error?.message ?? 'Não é possível remover esta zona.', tone: 'err' });
      } else {
        this.msg.set({ text: 'Não conseguimos remover a zona. Tente de novo.', tone: 'err' });
      }
    }
  }
}
