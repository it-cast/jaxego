import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
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
  faTrash,
  faPlus,
  faXmark,
  faCheck,
  faChevronLeft,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons';
import {
  Area,
  AreaAdminRow,
  PlatformAdminService,
} from './platform-admin.service';

type ViewMode = 'list' | 'create' | 'edit';

const PAGE_SIZE = 20;

@Component({
  selector: 'jx-plataforma-admins',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, DataTableComponent, FaIconComponent],
  templateUrl: './admins.page.html',
  styleUrl: './admins.page.scss',
})
export class PlataformaAdminsPage implements OnInit {
  private readonly service = inject(PlatformAdminService);

  protected readonly iconEdit = faPenToSquare;
  protected readonly iconDelete = faTrash;
  protected readonly iconPlus = faPlus;
  protected readonly iconCancel = faXmark;
  protected readonly iconSave = faCheck;
  protected readonly iconPrev = faChevronLeft;
  protected readonly iconNext = faChevronRight;

  protected readonly state = signal<DataTableState>('loading');
  protected readonly admins = signal<AreaAdminRow[]>([]);
  protected readonly filtered = signal<AreaAdminRow[]>([]);
  protected readonly areas = signal<Area[]>([]);
  protected readonly mode = signal<ViewMode>('list');
  protected readonly saving = signal(false);
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected readonly confirmDeleteId = signal<number | null>(null);

  protected readonly page = signal(1);
  protected readonly paged = computed(() => {
    const start = (this.page() - 1) * PAGE_SIZE;
    return this.filtered().slice(start, start + PAGE_SIZE);
  });
  protected readonly hasNext = computed(
    () => this.page() * PAGE_SIZE < this.filtered().length,
  );

  protected searchQuery = '';

  protected readonly columns: DataTableColumn[] = [
    { key: 'user_name', label: 'Nome' },
    { key: 'user_email', label: 'E-mail' },
    { key: 'area_name', label: 'Area' },
    { key: 'role', label: 'Papel' },
    { key: 'actions', label: 'Acoes' },
  ];

  protected form = this.emptyForm();
  protected editingAdmin: AreaAdminRow | null = null;

  async ngOnInit(): Promise<void> {
    await Promise.all([this.load(), this.loadAreas()]);
  }

  protected async load(): Promise<void> {
    this.state.set('loading');
    try {
      const admins = await this.service.listAreaAdmins();
      this.admins.set(admins);
      this.applyFilter();
      this.state.set(admins.length === 0 ? 'empty' : 'ready');
    } catch {
      this.state.set('error');
    }
  }

  private async loadAreas(): Promise<void> {
    try {
      this.areas.set(await this.service.listAreas());
    } catch {
      // areas will be empty — form won't have area options
    }
  }

  protected applyFilter(): void {
    let result = this.admins();
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.trim().toLowerCase();
      result = result.filter(
        (a) =>
          a.user_name.toLowerCase().includes(q) ||
          a.user_email.toLowerCase().includes(q) ||
          a.area_name.toLowerCase().includes(q),
      );
    }
    this.filtered.set(result);
    this.page.set(1);
  }

  protected goTo(delta: number): void {
    this.page.update((p) => p + delta);
  }

  protected showCreate(): void {
    this.form = this.emptyForm();
    this.editingAdmin = null;
    this.mode.set('create');
    this.msg.set(null);
  }

  protected showEdit(admin: AreaAdminRow): void {
    this.editingAdmin = admin;
    this.form = {
      area_id: admin.area_id,
      email: admin.user_email,
      name: admin.user_name,
      password: '',
      role: admin.role,
    };
    this.mode.set('edit');
    this.msg.set(null);
  }

  protected cancel(): void {
    this.mode.set('list');
    this.editingAdmin = null;
    this.msg.set(null);
  }

  protected async save(): Promise<void> {
    this.saving.set(true);
    this.msg.set(null);
    try {
      if (this.mode() === 'create') {
        await this.service.createAreaAdmin({
          area_id: this.form.area_id,
          email: this.form.email,
          name: this.form.name,
          password: this.form.password,
          role: this.form.role,
        });
        this.msg.set({ text: 'Admin criado com sucesso.', tone: 'ok' });
      } else if (this.editingAdmin) {
        await this.service.updateAreaAdmin(this.editingAdmin.id, {
          role: this.form.role,
          area_id: this.form.area_id,
        });
        this.msg.set({ text: 'Admin atualizado com sucesso.', tone: 'ok' });
      }
      this.mode.set('list');
      this.editingAdmin = null;
      await this.load();
    } catch {
      this.msg.set({ text: 'Erro ao salvar admin.', tone: 'err' });
    } finally {
      this.saving.set(false);
    }
  }

  protected confirmDelete(adminId: number): void {
    this.confirmDeleteId.set(adminId);
  }

  protected cancelDelete(): void {
    this.confirmDeleteId.set(null);
  }

  protected async doDelete(adminId: number): Promise<void> {
    this.confirmDeleteId.set(null);
    try {
      await this.service.removeAreaAdmin(adminId);
      this.msg.set({ text: 'Admin removido com sucesso.', tone: 'ok' });
      await this.load();
    } catch {
      this.msg.set({ text: 'Erro ao remover admin.', tone: 'err' });
    }
  }

  protected roleLabel(role: string): string {
    const map: Record<string, string> = {
      owner: 'Dono',
      manager: 'Gestor',
      viewer: 'Leitura',
    };
    return map[role] ?? role;
  }

  protected trackAdmin = (item: unknown): unknown => (item as AreaAdminRow).id;

  private emptyForm() {
    return {
      area_id: 0,
      email: '',
      name: '',
      password: '',
      role: 'manager',
    };
  }
}
