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
  faTrashCan,
  faCheck,
  faXmark,
  faChevronLeft,
  faChevronRight,
  faDrawPolygon,
} from '@fortawesome/free-solid-svg-icons';
import { AdminZonasService, Zona } from './zonas.service';
import { AreaMapComponent, AreaMapDraft } from '../../admin-plataforma/area-map.component';

type ViewMode = 'list' | 'mass-add';

/** Cores cicladas pros rascunhos de zona no modo de adicionar em massa — precisam
 * ser visualmente distintas entre si e da cor cinza das zonas existentes (#9aa0a6). */
const DRAFT_COLORS = ['#e8722a', '#2563eb', '#16a34a', '#c026d3', '#dc2626', '#0891b2', '#ca8a04', '#7c3aed'];
let draftSeq = 0;

interface ZoneDraftRow extends AreaMapDraft {
  /** null = zona nova (ainda não existe); número = zona já cadastrada sendo editada junto. */
  zonaId: number | null;
  originalName: string;
  originalBoundary: object | null;
}

function newDraftRow(): ZoneDraftRow {
  draftSeq += 1;
  return {
    id: `draft-${draftSeq}`,
    zonaId: null,
    name: '',
    boundary: null,
    originalName: '',
    originalBoundary: null,
    color: DRAFT_COLORS[(draftSeq - 1) % DRAFT_COLORS.length],
  };
}

function rowFromExisting(z: Zona): ZoneDraftRow {
  draftSeq += 1;
  return {
    id: `draft-${draftSeq}`,
    zonaId: z.id,
    name: z.name,
    boundary: z.boundary,
    originalName: z.name,
    originalBoundary: z.boundary,
    color: DRAFT_COLORS[(draftSeq - 1) % DRAFT_COLORS.length],
  };
}

function rowChanged(d: ZoneDraftRow): boolean {
  return (
    d.name.trim() !== d.originalName.trim() ||
    JSON.stringify(d.boundary) !== JSON.stringify(d.originalBoundary)
  );
}

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
          <button type="button" class="jx-zonas__cta" (click)="showMassAdd()">
            <fa-icon [icon]="iconPlus" aria-hidden="true" /> Adicionar
          </button>
        }
      </header>

      @if (msg(); as m) {
        <div class="jx-zonas__msg" [class.jx-zonas__msg--ok]="m.tone === 'ok'" [class.jx-zonas__msg--err]="m.tone === 'err'" role="status">
          {{ m.text }}
        </div>
      }

      @if (mode() === 'mass-add') {
        <section class="jx-zonas__form-card">
          <h2 class="jx-zonas__form-title">Zonas</h2>
          <p class="jx-zonas__hint">
            As zonas já cadastradas já aparecem abaixo, pra editar nome/polígono
            junto com as novas. Clique em "Desenhar"/"Redesenhar" pra marcar o
            polígono de qualquer linha no mapa, ou em "+ Nova zona" pra adicionar
            mais uma.
          </p>

          <div class="jx-zonas__draft-list">
            @for (d of drafts(); track d.id) {
              <div class="jx-zonas__draft-row" [class.jx-zonas__draft-row--active]="d.id === activeDraftId()">
                <span class="jx-zonas__draft-swatch" [style.background]="d.color"></span>
                <input
                  class="jx-zonas__input jx-zonas__draft-input"
                  type="text"
                  [(ngModel)]="d.name"
                  [name]="'draft-name-' + d.id"
                  maxlength="160"
                  placeholder="Nome da zona"
                />
                <button
                  type="button"
                  class="jx-zonas__draft-draw-btn"
                  [class.jx-zonas__draft-draw-btn--active]="d.id === activeDraftId()"
                  (click)="setActiveDraft(d.id)"
                >
                  <fa-icon [icon]="iconPolygon" aria-hidden="true" />
                  {{ d.boundary ? 'Redesenhar' : 'Desenhar' }}
                </button>
                @if (d.zonaId !== null) {
                  <span class="jx-zonas__draft-badge jx-zonas__draft-badge--existing">Existente</span>
                } @else {
                  <span class="jx-zonas__draft-badge">Nova</span>
                }
                @if (isRowChanged(d)) {
                  <span class="jx-zonas__draft-badge jx-zonas__draft-badge--changed">Alterada</span>
                }
                @if (d.zonaId === null) {
                  <button
                    type="button"
                    class="jx-zonas__action-btn jx-zonas__action-btn--danger"
                    (click)="removeDraftRow(d.id)"
                    aria-label="Remover esta linha"
                  >
                    <fa-icon [icon]="iconRemove" aria-hidden="true" />
                  </button>
                }
              </div>
            }
          </div>

          <button type="button" class="jx-zonas__btn-secondary" (click)="addDraftRow()">
            <fa-icon [icon]="iconPlus" aria-hidden="true" /> Nova zona
          </button>

          <div class="jx-zonas__field">
            <span class="jx-zonas__label">
              Mapa
              @if (activeDraftName(); as n) { — desenhando: <strong>{{ n }}</strong> }
            </span>
            <jx-area-map
              [multiMode]="true"
              [drafts]="drafts()"
              [activeDraftId]="activeDraftId()"
              (draftBoundaryChange)="onDraftBoundaryChange($event)"
            />
          </div>

          <div class="jx-zonas__form-actions">
            <button type="button" class="jx-zonas__cta" [disabled]="saving() || !hasSavableDraft()" (click)="saveAllDrafts()">
              <fa-icon [icon]="iconSave" aria-hidden="true" />
              {{ saving() ? 'Salvando...' : 'Salvar alterações' }}
            </button>
            <button type="button" class="jx-zonas__btn-secondary" (click)="cancel()">
              <fa-icon [icon]="iconCancel" aria-hidden="true" /> Cancelar
            </button>
          </div>
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
    .jx-zonas__btn-secondary { display: flex; align-items: center; gap: var(--jx-space-1); min-height: 44px; padding: 0 var(--jx-space-3); border: 1px solid var(--border); border-radius: var(--jx-radius-lg); background: transparent; color: var(--text); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); cursor: pointer; align-self: flex-start; }
    .jx-zonas__msg { padding: var(--jx-space-3) var(--jx-space-4); border-radius: var(--jx-radius-lg); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); }
    .jx-zonas__msg--ok { background: var(--success-wash, var(--brand-wash)); color: var(--success, var(--brand)); }
    .jx-zonas__msg--err { background: var(--error-wash, hsl(0 70% 95%)); color: var(--error); }
    .jx-zonas__form-card { background: var(--surface-elevated); border: 1px solid var(--border); border-radius: var(--jx-radius-xl); padding: var(--jx-space-5); display: flex; flex-direction: column; gap: var(--jx-space-4); }
    .jx-zonas__form-title { margin: 0; font-family: var(--jx-font-display); font-size: var(--jx-text-lg); font-weight: var(--jx-weight-bold); color: var(--text); }
    .jx-zonas__form { display: flex; flex-direction: column; gap: var(--jx-space-3); }
    .jx-zonas__field { display: flex; flex-direction: column; gap: var(--jx-space-1); }
    .jx-zonas__label { font-size: var(--jx-text-xs); font-weight: var(--jx-weight-semibold); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
    .jx-zonas__label strong { text-transform: none; letter-spacing: normal; color: var(--text); }
    .jx-zonas__input { min-height: 44px; padding: 0 var(--jx-space-3); border: 1px solid var(--border-strong, var(--border)); border-radius: var(--jx-radius-lg); font-size: var(--jx-text-base); color: var(--text); background: var(--surface); }
    .jx-zonas__input:focus { outline: none; border-color: var(--brand); }
    .jx-zonas__hint { font-size: var(--jx-text-xs); color: var(--text-muted); margin: 0; }
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

    .jx-zonas__draft-list { display: flex; flex-direction: column; gap: var(--jx-space-2); }
    .jx-zonas__draft-row { display: flex; align-items: center; gap: var(--jx-space-2); padding: var(--jx-space-2); border: 1px solid var(--border); border-radius: var(--jx-radius-md); }
    .jx-zonas__draft-row--active { border-color: var(--brand); background: var(--brand-wash, hsl(24 80% 97%)); }
    .jx-zonas__draft-swatch { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
    .jx-zonas__draft-input { flex: 1; min-height: 40px; }
    .jx-zonas__draft-draw-btn { display: flex; align-items: center; gap: 6px; min-height: 40px; padding: 0 var(--jx-space-3); border: 1px solid var(--border-strong, var(--border)); border-radius: var(--jx-radius-md); background: var(--surface); color: var(--text); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); cursor: pointer; white-space: nowrap; }
    .jx-zonas__draft-draw-btn--active { background: var(--brand); border-color: var(--brand); color: var(--brand-contrast, #fff); }
    .jx-zonas__draft-badge { font-size: var(--jx-text-xs); font-weight: 600; padding: 2px 8px; border-radius: 999px; background: var(--brand-wash, hsl(24 80% 95%)); color: var(--brand, #e8722a); white-space: nowrap; }
    .jx-zonas__draft-badge--existing { background: var(--surface-sunken); color: var(--text-muted); }
    .jx-zonas__draft-badge--changed { background: hsl(45 90% 92%); color: hsl(35 80% 35%); }
  `],
})
export class ZonasPage implements OnInit {
  private readonly service = inject(AdminZonasService);

  protected readonly iconPlus = faPlus;
  protected readonly iconRemove = faTrashCan;
  protected readonly iconSave = faCheck;
  protected readonly iconCancel = faXmark;
  protected readonly iconPrev = faChevronLeft;
  protected readonly iconNext = faChevronRight;
  protected readonly iconPolygon = faDrawPolygon;

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

  // --- Adicionar/editar em massa (CORRECAO-261) -------------------------------
  protected readonly drafts = signal<ZoneDraftRow[]>([]);
  protected readonly activeDraftId = signal<string | null>(null);

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

  protected cancel(): void {
    this.mode.set('list');
    this.drafts.set([]);
    this.activeDraftId.set(null);
    this.msg.set(null);
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

  // --- Adicionar/editar em massa -----------------------------------------------

  /** Abre com todas as zonas já cadastradas como linhas editáveis + uma linha nova em branco. */
  protected showMassAdd(): void {
    this.msg.set(null);
    const existingRows = this.allRows.map(rowFromExisting);
    const blank = newDraftRow();
    this.drafts.set([...existingRows, blank]);
    this.activeDraftId.set(blank.id);
    this.mode.set('mass-add');
  }

  protected addDraftRow(): void {
    const row = newDraftRow();
    this.drafts.update((rows) => [...rows, row]);
    this.activeDraftId.set(row.id);
  }

  /** Só remove linhas de zona NOVA (sem zonaId) desta sessão de edição — zonas já
   * cadastradas não podem ser tiradas por aqui (é preciso pra continuar mostrando/
   * editando todas as existentes). Apagar uma zona de verdade continua sendo só
   * pelo botão de remover na lista, com confirmação e checagem de uso. */
  protected removeDraftRow(id: string): void {
    const row = this.drafts().find((r) => r.id === id);
    if (!row || row.zonaId !== null) return;
    this.drafts.update((rows) => rows.filter((r) => r.id !== id));
    if (this.activeDraftId() === id) {
      const remaining = this.drafts();
      this.activeDraftId.set(remaining.length ? remaining[remaining.length - 1].id : null);
    }
  }

  protected setActiveDraft(id: string): void {
    this.activeDraftId.set(id);
  }

  protected activeDraftName(): string | null {
    const active = this.drafts().find((d) => d.id === this.activeDraftId());
    return active?.name.trim() || null;
  }

  protected onDraftBoundaryChange(e: { id: string; boundary: any }): void {
    this.drafts.update((rows) =>
      rows.map((r) => (r.id === e.id ? { ...r, boundary: e.boundary } : r))
    );
  }

  protected isRowChanged(d: ZoneDraftRow): boolean {
    return d.zonaId !== null && rowChanged(d);
  }

  /** Zona nova completa (nome + polígono), OU zona existente com nome/polígono alterado. */
  private savable(d: ZoneDraftRow): boolean {
    if (d.zonaId === null) return !!(d.name.trim() && d.boundary);
    return rowChanged(d) && !!d.name.trim();
  }

  protected hasSavableDraft(): boolean {
    return this.drafts().some((d) => this.savable(d));
  }

  protected async saveAllDrafts(): Promise<void> {
    const toSave = this.drafts().filter((d) => this.savable(d));
    if (toSave.length === 0) return;
    this.saving.set(true);
    this.msg.set(null);
    let created = 0;
    let updated = 0;
    const failedIds: string[] = [];
    for (const d of toSave) {
      try {
        if (d.zonaId === null) {
          await this.service.create({ name: d.name.trim(), boundary: d.boundary });
          created += 1;
        } else {
          await this.service.update(d.zonaId, { name: d.name.trim(), boundary: d.boundary });
          updated += 1;
        }
      } catch {
        failedIds.push(d.id);
      }
    }
    this.saving.set(false);

    if (failedIds.length === 0) {
      const parts: string[] = [];
      if (created > 0) parts.push(`${created} nova${created > 1 ? 's' : ''}`);
      if (updated > 0) parts.push(`${updated} atualizada${updated > 1 ? 's' : ''}`);
      this.msg.set({ text: `Zonas salvas: ${parts.join(', ')}.`, tone: 'ok' });
      this.mode.set('list');
      this.drafts.set([]);
      this.activeDraftId.set(null);
      await this.load();
    } else {
      // Mantém no modo de edição só as que falharam, pra tentar de novo sem perder o trabalho.
      const failed = this.drafts().filter((d) => failedIds.includes(d.id));
      this.drafts.set(failed);
      this.activeDraftId.set(failed[0]?.id ?? null);
      this.msg.set({
        text: `${created + updated} zona${created + updated > 1 ? 's' : ''} salva${created + updated > 1 ? 's' : ''}. ${failedIds.length} falharam — corrija e tente de novo.`,
        tone: 'err',
      });
      await this.load();
    }
  }
}
