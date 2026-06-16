import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { AuthService } from '../../core/auth/auth.service';
import { ThemeToggleComponent } from '../../core/theme/theme-toggle.component';
import {
  ScoreBreakdownComponent,
  ScoreChipComponent,
  type ScoreLevel,
} from '../../shared/components';
import { EmptyStateComponent } from '../../shared/state';
import {
  CourierProfile,
  CourierScore,
  EntregadorService,
} from './entregador.service';

const VALID_LEVELS: ScoreLevel[] = [
  'probation',
  'bronze',
  'prata',
  'ouro',
  'diamante',
];

/**
 * Perfil do entregador (tela tpl-c-profile). Score transparency (ADR-013): the
 * level + the explainable breakdown per component (informative only in M1 — no
 * financial weight). Cadastro status from /me. Identity/documents/PIX editing is
 * managed in the cadastro/saldo flows. Tokens only.
 */
@Component({
  selector: 'jx-entregador-perfil',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    EmptyStateComponent,
    ThemeToggleComponent,
    ScoreChipComponent,
    ScoreBreakdownComponent,
  ],
  template: `
    <ion-content>
      <div class="jx-perfil">
        <h1 class="jx-perfil__title">Seu perfil</h1>

        @if (profile(); as p) {
          <section class="jx-perfil__card">
            <strong class="jx-perfil__name">{{ p.full_name }}</strong>
            <p class="jx-perfil__id">
              CPF {{ p.cpf_masked }} · {{ vehicleLabel(p.vehicle_type) }}
              @if (p.vehicle_plate) {
                {{ p.vehicle_plate }}
              }
            </p>
          </section>
        }

        <section class="jx-perfil__card">
          <span class="jx-perfil__eyebrow">Situação do cadastro</span>
          <strong>{{ statusLabel() }}</strong>
        </section>

        @if (profile(); as p) {
          @if (p.documents.length) {
            <section class="jx-perfil__card">
              <span class="jx-perfil__eyebrow">Documentos</span>
              @for (d of p.documents; track d.kind) {
                <div class="jx-perfil__doc">
                  <span>{{ docLabel(d.kind) }}</span>
                  <span
                    class="jx-perfil__doc-status"
                    [class.jx-perfil__doc-status--ok]="d.status === 'approved'"
                    >{{ docStatusLabel(d.status) }}</span
                  >
                </div>
              }
            </section>
          }
        }

        @if (score(); as sc) {
          <section class="jx-perfil__card">
            <div class="jx-perfil__score-head">
              <span class="jx-perfil__eyebrow">Seu score</span>
              <jx-score-chip [level]="level()" [value]="sc.total_score" />
            </div>
            <jx-score-breakdown [components]="sc.components" />
            <p class="jx-perfil__note">
              No M1 o score é só o seu histórico público — não muda suas taxas.
            </p>
          </section>
        } @else {
          <jx-empty-state
            icon="⭐"
            title="Score ainda não calculado"
            message="Assim que você fizer entregas, seu score aparece aqui."
          />
        }

        <div class="jx-perfil__theme">
          <jx-theme-toggle />
        </div>
      </div>
    </ion-content>
  `,
  styles: [
    `
      .jx-perfil {
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
        padding: var(--jx-space-4) var(--jx-space-4) var(--jx-space-6);
      }
      .jx-perfil__title {
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-2xl);
        margin: 0;
      }
      .jx-perfil__card {
        background: var(--jx-color-surface);
        border: 1px solid var(--jx-color-neutral-200);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-3);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-2);
      }
      .jx-perfil__score-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .jx-perfil__eyebrow {
        font-family: var(--jx-font-mono);
        font-size: var(--jx-text-xs);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--jx-color-neutral-500);
      }
      .jx-perfil__name {
        font-size: var(--jx-text-md);
      }
      .jx-perfil__id {
        margin: 0;
        font-family: var(--jx-font-mono);
        font-size: var(--jx-text-xs);
        color: var(--jx-color-neutral-500);
      }
      .jx-perfil__doc {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: var(--jx-text-sm);
        padding: var(--jx-space-1) 0;
        border-bottom: 1px solid var(--surface-sunken);
      }
      .jx-perfil__doc-status {
        color: var(--jx-color-neutral-500);
        font-weight: var(--jx-weight-medium);
      }
      .jx-perfil__doc-status--ok {
        color: var(--jx-color-semantic-success);
      }
      .jx-perfil__note {
        margin: 0;
        font-size: var(--jx-text-sm);
        color: var(--jx-color-neutral-500);
      }
      .jx-perfil__theme {
        display: flex;
        justify-content: center;
        padding-top: var(--jx-space-2);
      }
    `,
  ],
})
export class EntregadorPerfilPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);

  protected readonly score = signal<CourierScore | null>(null);
  protected readonly profile = signal<CourierProfile | null>(null);

  protected readonly level = computed<ScoreLevel>(() => {
    const lvl = this.score()?.level as ScoreLevel | undefined;
    return lvl && VALID_LEVELS.includes(lvl) ? lvl : 'probation';
  });

  protected readonly statusLabel = computed<string>(() => {
    const map: Record<string, string> = {
      active: 'Ativo — você pode receber ofertas',
      pending_kyc: 'Em análise — termine sua validação',
      mei_pending: 'Ativo — regularize seu MEI para receber pela plataforma',
      suspended: 'Suspenso — veja as disputas',
    };
    const status = this.auth.me()?.status ?? '';
    return map[status] ?? 'Cadastro em andamento';
  });

  async ngOnInit(): Promise<void> {
    const id = this.auth.me()?.courier_id;
    if (!id) return;
    const [score, profile] = await Promise.all([
      this.svc.score(id),
      this.svc.profile(id),
    ]);
    this.score.set(score);
    this.profile.set(profile);
  }

  protected vehicleLabel(v: string): string {
    const map: Record<string, string> = {
      moto: 'Moto',
      bicicleta: 'Bicicleta',
      carro: 'Carro',
      a_pe: 'A pé',
    };
    return map[v] ?? v;
  }

  protected docLabel(kind: string): string {
    const map: Record<string, string> = {
      selfie: 'CPF + Selfie',
      cnh: 'CNH com EAR',
      crlv: 'CRLV',
      mei: 'MEI',
      antecedentes: 'Antecedentes',
    };
    return map[kind] ?? kind;
  }

  protected docStatusLabel(status: string): string {
    const map: Record<string, string> = {
      approved: '✓ Aprovado',
      rejected: 'Reprovado',
      pending: 'Em análise',
      pending_upload: 'Aguardando envio',
    };
    return map[status] ?? status;
  }
}
