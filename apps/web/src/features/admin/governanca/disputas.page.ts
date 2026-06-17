import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnInit,
  ViewChild,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { NoticeComponent } from '@jaxego/shared/components/notice/notice.component';
import { SuspensionPanelComponent } from '@jaxego/shared/components/suspension-panel/suspension-panel.component';
import type {
  AppealDecision,
  SuspensionAppeal,
} from '@jaxego/shared/components/suspension-panel/suspension-panel.component';
import {
  DisputeOutcome,
  DisputeRow,
  GovernancaService,
} from './governanca.service';

/**
 * Tela 09 — Disputas e suspensões da área (UI-SPEC §Tela 09 / D-08).
 *
 * jx-data-table de disputas (`payment_dispute`, Phase 9) + painéis de recurso
 * (jx-suspension-panel) com decisão (manter/reverter). A decisão de disputa é
 * ADMINISTRATIVA — registrar procedente/improcedente SEM efeito financeiro (DEC-004 →
 * Phase 15), com aviso explícito. Confirmação sensível antes de decidir. Tokens; AA. pt-BR.
 */
@Component({
  selector: 'jx-admin-governanca-disputas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    DataTableComponent,
    NoticeComponent,
    SuspensionPanelComponent,
  ],
  templateUrl: './disputas.page.html',
  styleUrl: './disputas.page.scss',
})
export class AdminGovernancaDisputasPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(GovernancaService);

  // --- Disputas -------------------------------------------------------------
  protected readonly disputesState = signal<DataTableState>('loading');
  protected readonly disputes = signal<DisputeRow[]>([]);

  protected readonly disputeColumns: DataTableColumn[] = [
    { key: 'id', label: 'Disputa', numeric: true },
    { key: 'delivery_id', label: 'Entrega', numeric: true },
    { key: 'courier_id', label: 'Entregador', numeric: true },
    { key: 'status', label: 'Situação' },
    { key: 'opened_at', label: 'Aberta em' },
  ];

  // --- Decisão de disputa (confirmação sensível) ---------------------------
  protected readonly deciding = signal<DisputeRow | null>(null);
  protected readonly decideSubmitting = signal(false);
  protected readonly decideError = signal<string | null>(null);

  protected readonly decideForm = this.fb.nonNullable.group({
    outcome: this.fb.nonNullable.control<DisputeOutcome>('procedente', [
      Validators.required,
    ]),
    note: this.fb.nonNullable.control(''),
  });

  // --- Suspensões / recursos ------------------------------------------------
  protected readonly suspensionsState = signal<DataTableState>('loading');
  protected readonly suspensions = signal<SuspensionAppeal[]>([]);
  protected readonly appealBusyId = signal<number | null>(null);
  protected readonly appealError = signal<string | null>(null);

  @ViewChild('decideTrigger') private decideTrigger?: ElementRef<HTMLButtonElement>;

  async ngOnInit(): Promise<void> {
    await Promise.all([this.loadDisputes(), this.loadSuspensions()]);
  }

  protected async loadDisputes(): Promise<void> {
    this.disputesState.set('loading');
    try {
      const rows = await this.service.listDisputes();
      this.disputes.set(rows);
      this.disputesState.set(rows.length === 0 ? 'empty' : 'ready');
    } catch {
      this.disputesState.set('error');
    }
  }

  protected async loadSuspensions(): Promise<void> {
    this.suspensionsState.set('loading');
    try {
      const rows = await this.service.listAppeals();
      this.suspensions.set(rows);
      this.suspensionsState.set(rows.length === 0 ? 'empty' : 'ready');
    } catch {
      this.suspensionsState.set('error');
    }
  }

  // --- Decisão de disputa ---------------------------------------------------
  protected requestDecide(dispute: DisputeRow): void {
    this.decideError.set(null);
    this.decideForm.reset({ outcome: 'procedente', note: '' });
    this.deciding.set(dispute);
  }

  protected cancelDecide(): void {
    this.deciding.set(null);
    this.decideTrigger?.nativeElement.focus();
  }

  async confirmDecide(): Promise<void> {
    const dispute = this.deciding();
    if (!dispute) {
      return;
    }
    this.decideSubmitting.set(true);
    this.decideError.set(null);
    try {
      const { outcome, note } = this.decideForm.getRawValue();
      await this.service.decideDispute(dispute.id, outcome, note.trim() || undefined);
      this.deciding.set(null);
      await this.loadDisputes();
    } catch {
      this.decideError.set('Não conseguimos registrar a decisão. Tente de novo.');
    } finally {
      this.decideSubmitting.set(false);
    }
  }

  // --- Decisão de recurso ---------------------------------------------------
  protected async decideAppeal(
    appeal: SuspensionAppeal,
    decision: AppealDecision,
  ): Promise<void> {
    this.appealBusyId.set(appeal.id);
    this.appealError.set(null);
    try {
      await this.service.decideAppeal(appeal.id, decision);
      await this.loadSuspensions();
    } catch {
      this.appealError.set('Não conseguimos registrar a decisão do recurso. Tente de novo.');
    } finally {
      this.appealBusyId.set(null);
    }
  }

  protected disputeStatusLabel(status: string): string {
    const map: Record<string, string> = {
      open: 'Aberta',
      resolved: 'Resolvida',
      pending: 'Pendente',
    };
    return map[status] ?? status;
  }

  protected canDecide(dispute: DisputeRow): boolean {
    return dispute.status !== 'resolved';
  }

  protected formatDate(iso: string): string {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) {
      return iso;
    }
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  protected trackDispute = (item: unknown): unknown => (item as DisputeRow).id;
  protected trackSuspension = (item: unknown): unknown =>
    (item as SuspensionAppeal).id;
}
