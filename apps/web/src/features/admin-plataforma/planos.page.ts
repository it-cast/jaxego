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
  faTrash,
  faPlus,
  faXmark,
  faCheck,
} from '@fortawesome/free-solid-svg-icons';
import {
  PlanAdmin,
  PlatformAdminService,
} from './platform-admin.service';

type ViewMode = 'list' | 'create' | 'edit';

@Component({
  selector: 'jx-plataforma-planos',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, DataTableComponent, FaIconComponent],
  templateUrl: './planos.page.html',
  styleUrl: './planos.page.scss',
})
export class PlataformaPlanosPage implements OnInit {
  private readonly service = inject(PlatformAdminService);

  protected readonly iconEdit = faPenToSquare;
  protected readonly iconDelete = faTrash;
  protected readonly iconPlus = faPlus;
  protected readonly iconCancel = faXmark;
  protected readonly iconSave = faCheck;

  protected readonly state = signal<DataTableState>('loading');
  protected readonly plans = signal<PlanAdmin[]>([]);
  protected readonly filtered = signal<PlanAdmin[]>([]);
  protected readonly mode = signal<ViewMode>('list');
  protected readonly saving = signal(false);
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected readonly confirmDeleteId = signal<number | null>(null);

  protected searchQuery = '';
  protected filterActive: 'all' | 'active' | 'inactive' = 'all';

  protected readonly columns: DataTableColumn[] = [
    { key: 'name', label: 'Nome' },
    { key: 'code', label: 'Codigo' },
    { key: 'price_cents', label: 'Preco (R$)', numeric: true },
    { key: 'deliveries_per_month', label: 'Entregas/mes', numeric: true },
    { key: 'fee_cents', label: 'Taxa (R$)', numeric: true },
    { key: 'is_active', label: 'Status' },
    { key: 'actions', label: 'Acoes' },
  ];

  // Form fields
  protected form = this.emptyForm();
  protected editingPlan: PlanAdmin | null = null;

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  protected async load(): Promise<void> {
    this.state.set('loading');
    try {
      const plans = await this.service.listPlans();
      this.plans.set(plans);
      this.applyFilter();
      this.state.set(plans.length === 0 ? 'empty' : 'ready');
    } catch {
      this.state.set('error');
    }
  }

  protected applyFilter(): void {
    let result = this.plans();
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.trim().toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.code.toLowerCase().includes(q),
      );
    }
    if (this.filterActive === 'active') {
      result = result.filter((p) => p.is_active);
    } else if (this.filterActive === 'inactive') {
      result = result.filter((p) => !p.is_active);
    }
    this.filtered.set(result);
  }

  protected showCreate(): void {
    this.form = this.emptyForm();
    this.editingPlan = null;
    this.mode.set('create');
    this.msg.set(null);
  }

  protected showEdit(plan: PlanAdmin): void {
    this.editingPlan = plan;
    this.form = {
      code: plan.code,
      name: plan.name,
      price_cents: plan.price_cents,
      deliveries_per_month: plan.deliveries_per_month,
      fee_cents: plan.fee_cents,
      is_unlimited: plan.is_unlimited,
      sort_order: plan.sort_order,
    };
    this.mode.set('edit');
    this.msg.set(null);
  }

  protected cancel(): void {
    this.mode.set('list');
    this.editingPlan = null;
    this.msg.set(null);
  }

  protected async save(): Promise<void> {
    this.saving.set(true);
    this.msg.set(null);
    try {
      if (this.mode() === 'create') {
        await this.service.createPlan({
          code: this.form.code,
          name: this.form.name,
          price_cents: this.form.price_cents,
          deliveries_per_month: this.form.deliveries_per_month,
          fee_cents: this.form.fee_cents,
          is_unlimited: this.form.is_unlimited,
          sort_order: this.form.sort_order,
        });
        this.msg.set({ text: 'Plano criado com sucesso.', tone: 'ok' });
      } else if (this.editingPlan) {
        await this.service.updatePlan(this.editingPlan.id, {
          name: this.form.name,
          price_cents: this.form.price_cents,
          deliveries_per_month: this.form.deliveries_per_month,
          fee_cents: this.form.fee_cents,
          is_unlimited: this.form.is_unlimited,
          sort_order: this.form.sort_order,
        });
        this.msg.set({ text: 'Plano atualizado com sucesso.', tone: 'ok' });
      }
      this.mode.set('list');
      this.editingPlan = null;
      await this.load();
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'error' in err
          ? (err as { error: { message: string } }).error?.message
          : 'Erro ao salvar plano.';
      this.msg.set({ text: message || 'Erro ao salvar plano.', tone: 'err' });
    } finally {
      this.saving.set(false);
    }
  }

  protected async confirmDelete(planId: number): Promise<void> {
    this.confirmDeleteId.set(planId);
  }

  protected cancelDelete(): void {
    this.confirmDeleteId.set(null);
  }

  protected async doDelete(planId: number): Promise<void> {
    this.confirmDeleteId.set(null);
    try {
      await this.service.deletePlan(planId);
      this.msg.set({ text: 'Plano desativado com sucesso.', tone: 'ok' });
      await this.load();
    } catch {
      this.msg.set({ text: 'Erro ao desativar o plano.', tone: 'err' });
    }
  }

  protected formatCents(cents: number): string {
    return (cents / 100).toFixed(2).replace('.', ',');
  }

  protected trackPlan = (item: unknown): unknown => (item as PlanAdmin).id;

  private emptyForm() {
    return {
      code: '',
      name: '',
      price_cents: 0,
      deliveries_per_month: 0,
      fee_cents: 0,
      is_unlimited: false,
      sort_order: 0,
    };
  }
}
