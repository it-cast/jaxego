import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faPlus,
  faPenToSquare,
  faBoxArchive,
  faCheck,
  faXmark,
} from '@fortawesome/free-solid-svg-icons';

interface Team {
  id: number;
  name: string;
  created_at: string;
}

type ViewMode = 'list' | 'create' | 'edit';

@Component({
  selector: 'jx-admin-equipes',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, DataTableComponent, FaIconComponent],
  template: `
    <main class="jx-equipes">
      <header class="jx-equipes__header">
        <h1 class="jx-equipes__title">Equipes</h1>
        @if (mode() === 'list') {
          <button type="button" class="jx-equipes__cta" (click)="showCreate()">
            <fa-icon [icon]="iconPlus" aria-hidden="true" /> Adicionar
          </button>
        }
      </header>

      @if (msg(); as m) {
        <div class="jx-equipes__msg" [class.jx-equipes__msg--ok]="m.tone === 'ok'" [class.jx-equipes__msg--err]="m.tone === 'err'" role="status">
          {{ m.text }}
        </div>
      }

      @if (mode() === 'create' || mode() === 'edit') {
        <section class="jx-equipes__form-card">
          <h2 class="jx-equipes__form-title">{{ mode() === 'create' ? 'Nova equipe' : 'Editar equipe' }}</h2>
          <form class="jx-equipes__form" (ngSubmit)="save()">
            <label class="jx-equipes__field">
              <span class="jx-equipes__label">Nome da equipe</span>
              <input class="jx-equipes__input" type="text" [(ngModel)]="formName" name="name" required maxlength="160" placeholder="Ex: Equipe Centro" />
            </label>
            <div class="jx-equipes__form-actions">
              <button type="submit" class="jx-equipes__cta" [disabled]="saving()">
                <fa-icon [icon]="iconSave" aria-hidden="true" />
                {{ saving() ? 'Salvando...' : 'Salvar' }}
              </button>
              <button type="button" class="jx-equipes__btn-secondary" (click)="cancel()">
                <fa-icon [icon]="iconCancel" aria-hidden="true" /> Cancelar
              </button>
            </div>
          </form>
        </section>
      }

      @if (mode() === 'list') {
        <div class="jx-equipes__search">
          <input class="jx-equipes__input" type="search" placeholder="Buscar equipe..." [(ngModel)]="searchQuery" (ngModelChange)="applyFilter()" />
        </div>

        <jx-data-table
          [columns]="columns"
          [rows]="teams()"
          [state]="state()"
          [trackBy]="trackTeam"
          caption="Equipes da área"
          emptyIcon="👥"
          emptyTitle="Nenhuma equipe cadastrada"
          emptyMessage="Crie a primeira equipe clicando em '+ Adicionar'."
          errorMessage="Não foi possível carregar as equipes."
          (retry)="load()"
        >
          <ng-template #row let-item>
            <td>{{ item.id }}</td>
            <td>{{ item.name }}</td>
            <td class="jx-equipes__actions">
              @if (confirmArchiveId() === item.id) {
                <span class="jx-equipes__confirm-msg">Arquivar?</span>
                <button type="button" class="jx-equipes__action-btn jx-equipes__action-btn--danger" (click)="doArchive(item.id)">
                  <fa-icon [icon]="iconSave" aria-hidden="true" />
                </button>
                <button type="button" class="jx-equipes__action-btn" (click)="cancelArchive()">
                  <fa-icon [icon]="iconCancel" aria-hidden="true" />
                </button>
              } @else {
                <button type="button" class="jx-equipes__action-btn" (click)="showEdit(item)">
                  <fa-icon [icon]="iconEdit" aria-hidden="true" />
                </button>
                <button type="button" class="jx-equipes__action-btn jx-equipes__action-btn--danger" (click)="confirmArchive(item.id)">
                  <fa-icon [icon]="iconArchive" aria-hidden="true" />
                </button>
              }
            </td>
          </ng-template>
        </jx-data-table>

        @if (totalPages > 1) {
          <div class="jx-equipes__pagination">
            <button class="jx-equipes__page-btn" [disabled]="currentPage() === 0" (click)="goPage(currentPage() - 1)">Anterior</button>
            <span class="jx-equipes__page-info">{{ currentPage() + 1 }} de {{ totalPages }}</span>
            <button class="jx-equipes__page-btn" [disabled]="currentPage() >= totalPages - 1" (click)="goPage(currentPage() + 1)">Próxima</button>
          </div>
        }
      }
    </main>
  `,
  styles: [`
    .jx-equipes { display: flex; flex-direction: column; gap: var(--jx-space-4); }
    .jx-equipes__header { display: flex; align-items: center; justify-content: space-between; }
    .jx-equipes__title { margin: 0; font-family: var(--jx-font-display); font-size: var(--jx-text-2xl); font-weight: var(--jx-weight-bold); color: var(--text); }
    .jx-equipes__cta { display: flex; align-items: center; gap: var(--jx-space-1); min-height: 44px; padding: 0 var(--jx-space-3); border: 0; border-radius: var(--jx-radius-lg); background: var(--brand); color: var(--brand-contrast, #fff); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); cursor: pointer; }
    .jx-equipes__cta:disabled { opacity: 0.6; }
    .jx-equipes__btn-secondary { display: flex; align-items: center; gap: var(--jx-space-1); min-height: 44px; padding: 0 var(--jx-space-3); border: 1px solid var(--border); border-radius: var(--jx-radius-lg); background: transparent; color: var(--text); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); cursor: pointer; }
    .jx-equipes__msg { padding: var(--jx-space-3) var(--jx-space-4); border-radius: var(--jx-radius-lg); font-size: var(--jx-text-sm); font-weight: var(--jx-weight-semibold); }
    .jx-equipes__msg--ok { background: var(--success-wash, var(--brand-wash)); color: var(--success, var(--brand)); }
    .jx-equipes__msg--err { background: var(--error-wash, hsl(0 70% 95%)); color: var(--error); }
    .jx-equipes__form-card { background: var(--surface-elevated); border: 1px solid var(--border); border-radius: var(--jx-radius-xl); padding: var(--jx-space-5); display: flex; flex-direction: column; gap: var(--jx-space-4); }
    .jx-equipes__form-title { margin: 0; font-family: var(--jx-font-display); font-size: var(--jx-text-lg); font-weight: var(--jx-weight-bold); color: var(--text); }
    .jx-equipes__form { display: flex; flex-direction: column; gap: var(--jx-space-3); }
    .jx-equipes__field { display: flex; flex-direction: column; gap: var(--jx-space-1); }
    .jx-equipes__label { font-size: var(--jx-text-xs); font-weight: var(--jx-weight-semibold); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
    .jx-equipes__input { min-height: 44px; padding: 0 var(--jx-space-3); border: 1px solid var(--border-strong, var(--border)); border-radius: var(--jx-radius-lg); font-size: var(--jx-text-base); color: var(--text); background: var(--surface); }
    .jx-equipes__input:focus { outline: none; border-color: var(--brand); }
    .jx-equipes__form-actions { display: flex; gap: var(--jx-space-2); }
    .jx-equipes__actions { display: flex; gap: var(--jx-space-1); }
    .jx-equipes__action-btn { min-width: 36px; min-height: 36px; display: grid; place-items: center; border: 0; border-radius: var(--jx-radius-md); background: var(--surface-sunken); color: var(--text-muted); cursor: pointer; font-size: 14px; }
    .jx-equipes__action-btn:hover { background: var(--surface-elevated); color: var(--text); }
    .jx-equipes__action-btn--danger:hover { color: var(--error); }
    .jx-equipes__confirm-msg { font-size: var(--jx-text-xs); color: var(--error); font-weight: 600; margin-right: var(--jx-space-1); }
    .jx-equipes__pagination { display: flex; align-items: center; justify-content: center; gap: var(--jx-space-3); padding: var(--jx-space-3) 0; }
    .jx-equipes__page-btn { min-height: 36px; padding: 0 var(--jx-space-3); border: 1px solid var(--border); border-radius: var(--jx-radius-md); background: var(--surface); color: var(--text); font-size: var(--jx-text-sm); cursor: pointer; }
    .jx-equipes__page-btn:hover:not(:disabled) { background: var(--surface-elevated); }
    .jx-equipes__page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .jx-equipes__page-info { font-size: var(--jx-text-sm); color: var(--text-muted); font-weight: 600; }
    .jx-equipes__search { margin-bottom: 0; }
  `],
})
export class AdminEquipesPage implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly iconPlus = faPlus;
  protected readonly iconEdit = faPenToSquare;
  protected readonly iconArchive = faBoxArchive;
  protected readonly iconSave = faCheck;
  protected readonly iconCancel = faXmark;

  protected readonly state = signal<DataTableState>('loading');
  private allTeams: Team[] = [];
  protected readonly teams = signal<Team[]>([]);
  protected readonly mode = signal<ViewMode>('list');
  protected searchQuery = '';
  protected readonly saving = signal(false);
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected readonly confirmArchiveId = signal<number | null>(null);
  protected readonly currentPage = signal(0);
  protected readonly totalItems = signal(0);
  protected readonly PAGE_SIZE = 20;

  protected formName = '';
  private editingId: number | null = null;

  protected readonly columns: DataTableColumn[] = [
    { key: 'id', label: 'ID', numeric: true },
    { key: 'name', label: 'Nome' },
    { key: 'actions', label: 'Ações' },
  ];

  protected get totalPages(): number {
    return Math.ceil(this.totalItems() / this.PAGE_SIZE);
  }

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  protected async load(): Promise<void> {
    this.state.set('loading');
    try {
      const offset = this.currentPage() * this.PAGE_SIZE;
      const res = await firstValueFrom(
        this.http.get<{ items: Team[]; total: number }>('/v1/admin/teams', {
          params: { limit: this.PAGE_SIZE, offset },
        })
      );
      this.allTeams = res.items;
      this.totalItems.set(res.total);
      this.applyFilter();
      this.state.set(res.items.length === 0 && res.total === 0 ? 'empty' : 'ready');
    } catch {
      this.state.set('error');
    }
  }

  protected applyFilter(): void {
    const q = this.searchQuery.trim().toLowerCase();
    this.teams.set(q ? this.allTeams.filter(t => t.name.toLowerCase().includes(q)) : this.allTeams);
  }

  protected async goPage(page: number): Promise<void> {
    this.currentPage.set(page);
    await this.load();
  }

  protected showCreate(): void {
    this.formName = '';
    this.editingId = null;
    this.mode.set('create');
    this.msg.set(null);
  }

  protected showEdit(team: Team): void {
    this.formName = team.name;
    this.editingId = team.id;
    this.mode.set('edit');
    this.msg.set(null);
  }

  protected cancel(): void {
    this.mode.set('list');
    this.editingId = null;
    this.msg.set(null);
  }

  protected async save(): Promise<void> {
    this.saving.set(true);
    this.msg.set(null);
    try {
      if (this.mode() === 'create') {
        await firstValueFrom(this.http.post('/v1/admin/teams', { name: this.formName }));
        this.msg.set({ text: 'Equipe criada com sucesso.', tone: 'ok' });
      } else if (this.editingId) {
        await firstValueFrom(this.http.patch(`/v1/admin/teams/${this.editingId}`, { name: this.formName }));
        this.msg.set({ text: 'Equipe atualizada com sucesso.', tone: 'ok' });
      }
      this.mode.set('list');
      this.editingId = null;
      await this.load();
    } catch {
      this.msg.set({ text: 'Erro ao salvar equipe.', tone: 'err' });
    } finally {
      this.saving.set(false);
    }
  }

  protected confirmArchive(id: number): void {
    this.confirmArchiveId.set(id);
  }

  protected cancelArchive(): void {
    this.confirmArchiveId.set(null);
  }

  protected async doArchive(id: number): Promise<void> {
    this.confirmArchiveId.set(null);
    try {
      await firstValueFrom(this.http.post(`/v1/admin/teams/${id}/archive`, {}));
      this.msg.set({ text: 'Equipe arquivada.', tone: 'ok' });
      await this.load();
    } catch {
      this.msg.set({ text: 'Erro ao arquivar equipe.', tone: 'err' });
    }
  }

  protected trackTeam = (item: unknown) => (item as Team).id;
}
