import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { NoticeComponent } from '../../../shared/components/notice/notice.component';
import { ScoreBadgeComponent } from '../../../shared/components/score-badge/score-badge.component';
import { ScoreBreakdownComponent } from '../../../shared/components/score-breakdown/score-breakdown.component';
import { SuspensionPanelComponent } from '../../../shared/components/suspension-panel/suspension-panel.component';
import type {
  AppealDecision,
  SuspensionAppeal,
} from '../../../shared/components/suspension-panel/suspension-panel.component';
import { CourierScore, GovernancaService } from './governanca.service';

/**
 * Telas 19/20 — Detalhe do entregador (UI-SPEC §Tela 19/20 / D-04/D-05).
 *
 * Score + breakdown explicável (ADR-013); suspender com motivo OBRIGATÓRIO (auditado)
 * → abre a janela de recurso; e o painel de recurso (jx-suspension-panel) com SLA
 * countdown e decisão (manter/reverter). A reversão automática quando o SLA vence é
 * indicada no painel. Tokens; AA 2 temas. pt-BR sem jargão (UI-SPEC §copy).
 */
@Component({
  selector: 'jx-admin-entregador-detalhe',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    NoticeComponent,
    ScoreBadgeComponent,
    ScoreBreakdownComponent,
    SuspensionPanelComponent,
  ],
  templateUrl: './entregador-detalhe.page.html',
  styleUrl: './entregador-detalhe.page.scss',
})
export class AdminEntregadorDetalhePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(GovernancaService);

  protected readonly courierId = signal<number>(0);

  // --- Score ----------------------------------------------------------------
  protected readonly scoreState = signal<'loading' | 'ready' | 'empty' | 'error'>(
    'loading',
  );
  protected readonly score = signal<CourierScore | null>(null);

  // --- Recurso ativo --------------------------------------------------------
  protected readonly appeal = signal<SuspensionAppeal | null>(null);
  protected readonly appealBusy = signal(false);
  protected readonly appealError = signal<string | null>(null);

  // --- Suspensão (motivo obrigatório) --------------------------------------
  protected readonly suspending = signal(false);
  protected readonly suspendSubmitting = signal(false);
  protected readonly suspendError = signal<string | null>(null);

  protected readonly suspendForm = this.fb.nonNullable.group({
    reason: this.fb.nonNullable.control('', [
      Validators.required,
      Validators.minLength(3),
      Validators.maxLength(500),
    ]),
  });

  async ngOnInit(): Promise<void> {
    const id = Number(this.route.snapshot.paramMap.get('courierId'));
    this.courierId.set(id);
    await Promise.all([this.loadScore(), this.loadAppeal()]);
  }

  protected async loadScore(): Promise<void> {
    this.scoreState.set('loading');
    try {
      const s = await this.service.courierScore(this.courierId());
      this.score.set(s);
      this.scoreState.set('ready');
    } catch (err) {
      // 404 = score ainda não calculado (estado empty, não erro).
      if (this.isNotFound(err)) {
        this.scoreState.set('empty');
      } else {
        this.scoreState.set('error');
      }
    }
  }

  protected async loadAppeal(): Promise<void> {
    try {
      const appeals = await this.service.listAppeals();
      const active = appeals.find(
        (a) =>
          a.subject_type === 'courier' && a.subject_id === this.courierId(),
      );
      this.appeal.set(active ?? null);
    } catch {
      this.appeal.set(null);
    }
  }

  // --- Suspender ------------------------------------------------------------
  protected openSuspend(): void {
    this.suspendError.set(null);
    this.suspendForm.reset({ reason: '' });
    this.suspending.set(true);
  }

  protected cancelSuspend(): void {
    this.suspending.set(false);
  }

  protected reasonError(): string | null {
    const ctrl = this.suspendForm.controls.reason;
    if (!ctrl.touched || ctrl.valid) {
      return null;
    }
    return 'Informe o motivo da suspensão (mínimo 3 caracteres).';
  }

  async confirmSuspend(): Promise<void> {
    if (this.suspendForm.invalid) {
      this.suspendForm.markAllAsTouched();
      return;
    }
    this.suspendSubmitting.set(true);
    this.suspendError.set(null);
    try {
      const { reason } = this.suspendForm.getRawValue();
      const appeal = await this.service.openSuspension(
        'courier',
        this.courierId(),
        reason.trim(),
      );
      this.appeal.set(appeal);
      this.suspending.set(false);
    } catch {
      this.suspendError.set('Não conseguimos suspender agora. Tente de novo.');
    } finally {
      this.suspendSubmitting.set(false);
    }
  }

  // --- Decisão do recurso ---------------------------------------------------
  protected async decideAppeal(decision: AppealDecision): Promise<void> {
    const current = this.appeal();
    if (!current) {
      return;
    }
    this.appealBusy.set(true);
    this.appealError.set(null);
    try {
      const updated = await this.service.decideAppeal(current.id, decision);
      this.appeal.set(updated);
    } catch {
      this.appealError.set('Não conseguimos registrar a decisão. Tente de novo.');
    } finally {
      this.appealBusy.set(false);
    }
  }

  protected isSuspended(): boolean {
    const a = this.appeal();
    return a != null && a.reverted_at == null && a.decision == null;
  }

  private isNotFound(err: unknown): boolean {
    return (
      typeof err === 'object' &&
      err != null &&
      'status' in err &&
      (err as { status: number }).status === 404
    );
  }
}
