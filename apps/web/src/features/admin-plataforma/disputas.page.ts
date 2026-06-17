import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import {
  DataTableColumn,
  DataTableComponent,
  DataTableState,
} from '@jaxego/shared/components/data-table/data-table.component';
import { SuspensionPanelComponent } from '@jaxego/shared/components/suspension-panel/suspension-panel.component';
import type { SuspensionAppeal } from '@jaxego/shared/components/suspension-panel/suspension-panel.component';
import { DisputeRow, PlatformAdminService } from './platform-admin.service';

/**
 * Tela 25 — Disputas e suspensões globais (UI-SPEC §Tela 25 / D-06 / D-08).
 *
 * Lista global (cross-área) de disputas (`payment_dispute`, Phase 9) + recursos de
 * suspensão (jx-suspension-panel — leitura/SLA). É a visão de triagem do dono da
 * plataforma; a decisão administrativa de cada disputa é tomada pelo admin de área
 * (tela 09). NÃO há efeito financeiro (DEC-004 → Phase 15). Leitura cross-área
 * auditada no backend. Tokens; AA 2 temas. pt-BR.
 */
@Component({
  selector: 'jx-plataforma-disputas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DataTableComponent, SuspensionPanelComponent],
  templateUrl: './disputas.page.html',
  styleUrl: './disputas.page.scss',
})
export class PlataformaDisputasPage implements OnInit {
  private readonly service = inject(PlatformAdminService);

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

  // --- Suspensões -----------------------------------------------------------
  protected readonly suspensionsState = signal<DataTableState>('loading');
  protected readonly suspensions = signal<SuspensionAppeal[]>([]);

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
      const rows = await this.service.listSuspensions();
      this.suspensions.set(rows);
      this.suspensionsState.set(rows.length === 0 ? 'empty' : 'ready');
    } catch {
      this.suspensionsState.set('error');
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
