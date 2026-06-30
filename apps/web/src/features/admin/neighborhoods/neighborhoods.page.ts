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
  faCheck,
  faXmark,
  faTrashCan,
  faChevronLeft,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons';
import {
  AdminNeighborhoodsService,
  Neighborhood,
  NeighborhoodCreate,
} from './neighborhoods.service';

type ViewMode = 'list' | 'create';

@Component({
  selector: 'jx-neighborhoods-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, DataTableComponent, FaIconComponent],
  templateUrl: './neighborhoods.page.html',
  styleUrl: './neighborhoods.page.scss',
})
export class NeighborhoodsPage implements OnInit {
  private readonly service = inject(AdminNeighborhoodsService);

  protected readonly iconPlus = faPlus;
  protected readonly iconSave = faCheck;
  protected readonly iconCancel = faXmark;
  protected readonly iconRemove = faTrashCan;
  protected readonly iconPrev = faChevronLeft;
  protected readonly iconNext = faChevronRight;

  protected readonly columns: DataTableColumn[] = [
    { key: 'name', label: 'Nome' },
    { key: 'actions', label: 'Ações' },
  ];

  private allRows: Neighborhood[] = [];
  protected readonly filteredRows = signal<Neighborhood[]>([]);
  protected readonly tableState = signal<DataTableState>('loading');
  protected readonly mode = signal<ViewMode>('list');
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected readonly adding = signal(false);
  protected readonly confirmRemoveId = signal<number | null>(null);
  protected readonly currentPage = signal(0);
  protected readonly PAGE_SIZE = 20;

  protected searchQuery = '';
  protected newName = '';

  protected get totalPages(): number {
    return Math.ceil(this.filteredRows().length / this.PAGE_SIZE);
  }

  protected get pagedRows(): Neighborhood[] {
    const start = this.currentPage() * this.PAGE_SIZE;
    return this.filteredRows().slice(start, start + this.PAGE_SIZE);
  }

  protected readonly trackById = (item: unknown): number => (item as Neighborhood).id;

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
    const filtered = q
      ? this.allRows.filter(n => n.name.toLowerCase().includes(q))
      : this.allRows;
    this.filteredRows.set(filtered);
    this.currentPage.set(0);
  }

  protected goPage(page: number): void {
    this.currentPage.set(page);
  }

  protected showCreate(): void {
    this.newName = '';
    this.msg.set(null);
    this.mode.set('create');
  }

  protected cancel(): void {
    this.mode.set('list');
    this.msg.set(null);
  }

  protected async save(): Promise<void> {
    const name = this.newName.trim();
    if (!name) return;
    this.adding.set(true);
    try {
      await this.service.create({ name });
      this.msg.set({ text: 'Bairro adicionado com sucesso.', tone: 'ok' });
      this.mode.set('list');
      await this.load();
    } catch {
      this.msg.set({ text: 'Não conseguimos adicionar o bairro. Tente de novo.', tone: 'err' });
    } finally {
      this.adding.set(false);
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
      this.msg.set({ text: 'Bairro removido.', tone: 'ok' });
      await this.load();
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 409) {
        this.msg.set({
          text:
            err.error?.error?.message ??
            'Não é possível remover: há entregas ativas nesse bairro.',
          tone: 'err',
        });
      } else {
        this.msg.set({ text: 'Não conseguimos remover o bairro. Tente de novo.', tone: 'err' });
      }
    }
  }
}
