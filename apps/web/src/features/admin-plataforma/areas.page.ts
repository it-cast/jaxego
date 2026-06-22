import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faPenToSquare,
  faBoxArchive,
  faPlus,
  faXmark,
  faCheck,
} from '@fortawesome/free-solid-svg-icons';
import { Area, PlatformAdminService } from './platform-admin.service';

type ViewMode = 'list' | 'create' | 'edit';

@Component({
  selector: 'jx-plataforma-areas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, DataTableComponent, FaIconComponent],
  templateUrl: './areas.page.html',
  styleUrl: './areas.page.scss',
})
export class PlataformaAreasPage implements OnInit {
  private readonly svc = inject(PlatformAdminService);

  protected readonly iconEdit = faPenToSquare;
  protected readonly iconArchive = faBoxArchive;
  protected readonly iconPlus = faPlus;
  protected readonly iconCancel = faXmark;
  protected readonly iconSave = faCheck;

  protected readonly state = signal<DataTableState>('loading');
  protected readonly areas = signal<Area[]>([]);
  protected readonly filtered = signal<Area[]>([]);
  protected readonly mode = signal<ViewMode>('list');
  protected readonly saving = signal(false);
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected readonly confirmArchiveId = signal<number | null>(null);

  protected searchQuery = '';

  protected readonly columns: DataTableColumn[] = [
    { key: 'id', label: 'ID', numeric: true },
    { key: 'codename', label: 'Slug' },
    { key: 'name', label: 'Nome' },
    { key: 'kyc', label: 'Validacao' },
    { key: 'actions', label: 'Acoes' },
  ];

  protected form = this.emptyForm();
  protected editingArea: Area | null = null;

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  protected async load(): Promise<void> {
    this.state.set('loading');
    try {
      const areas = await this.svc.listAreas();
      this.areas.set(areas);
      this.applyFilter();
      this.state.set(areas.length === 0 ? 'empty' : 'ready');
    } catch {
      this.state.set('error');
    }
  }

  protected applyFilter(): void {
    let result = this.areas();
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.trim().toLowerCase();
      result = result.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.codename.toLowerCase().includes(q),
      );
    }
    this.filtered.set(result);
  }

  protected showCreate(): void {
    this.form = this.emptyForm();
    this.editingArea = null;
    this.mode.set('create');
    this.msg.set(null);
  }

  protected showEdit(area: Area): void {
    this.editingArea = area;
    this.form = {
      codename: area.codename,
      name: area.name,
      kyc_level: (area.config?.['kyc_level'] as string) ?? 'simples',
    };
    this.mode.set('edit');
    this.msg.set(null);
  }

  protected cancel(): void {
    this.mode.set('list');
    this.editingArea = null;
    this.msg.set(null);
  }

  protected async save(): Promise<void> {
    this.saving.set(true);
    this.msg.set(null);
    try {
      if (this.mode() === 'create') {
        await this.svc.createArea({
          codename: this.form.codename,
          name: this.form.name,
          config: { kyc_level: this.form.kyc_level },
        });
        this.msg.set({ text: 'Area criada com sucesso.', tone: 'ok' });
      } else if (this.editingArea) {
        await this.svc.updateArea(this.editingArea.id, {
          name: this.form.name,
          config: { kyc_level: this.form.kyc_level },
        });
        this.msg.set({ text: 'Area atualizada com sucesso.', tone: 'ok' });
      }
      this.mode.set('list');
      this.editingArea = null;
      await this.load();
    } catch {
      this.msg.set({ text: 'Erro ao salvar area.', tone: 'err' });
    } finally {
      this.saving.set(false);
    }
  }

  protected confirmArchive(areaId: number): void {
    this.confirmArchiveId.set(areaId);
  }

  protected cancelArchive(): void {
    this.confirmArchiveId.set(null);
  }

  protected async doArchive(areaId: number): Promise<void> {
    this.confirmArchiveId.set(null);
    try {
      await this.svc.archiveArea(areaId);
      this.msg.set({ text: 'Area arquivada com sucesso.', tone: 'ok' });
      await this.load();
    } catch {
      this.msg.set({ text: 'Erro ao arquivar a area.', tone: 'err' });
    }
  }

  protected kycLabel(area: Area): string {
    const level = (area.config?.['kyc_level'] as string) ?? 'simples';
    return level === 'completa' ? 'Completa' : 'Simples';
  }

  protected trackArea = (item: unknown): unknown => (item as Area).id;

  private emptyForm() {
    return {
      codename: '',
      name: '',
      kyc_level: 'simples',
    };
  }
}
