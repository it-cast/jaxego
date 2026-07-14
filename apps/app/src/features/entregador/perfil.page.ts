import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { Router } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faRotateRight,
  faRightFromBracket,
  faChevronRight,
  faUser,
  faPenToSquare,
  faFolderOpen,
  faStar,
} from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import {
  DocCardComponent,
  type DocStatus,
} from '@jaxego/shared/components';
import {
  DotsLoaderComponent,
  PageHeaderComponent,
} from '@jaxego/shared/components';
import { EmptyStateComponent } from '@jaxego/shared/state';
import {
  CourierDocumentItem,
  CourierProfile,
  CourierScore,
  EntregadorService,
} from './entregador.service';
import { CourierCadastroService } from './cadastro/cadastro.service';
import { CourierLocationService } from './courier-location.service';


const REASON_LABELS: Record<string, string> = {
  ilegivel: 'Ilegível',
  sem_ear: 'Sem EAR',
  vencida: 'Vencida',
  nao_confere: 'Não confere com o titular',
  outro: 'Outro',
};

@Component({
  selector: 'jx-entregador-perfil',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    FaIconComponent,
    DocCardComponent,
    EmptyStateComponent,
    PageHeaderComponent,
    DotsLoaderComponent,
  ],
  template: `
    <ion-content>
      @if (initialLoading()) {
        <jx-dots-loader />
      } @else {
      <jx-page-header title="Perfil" />
      <div class="jx-perfil">
        <header class="jx-perfil__header">
          <div class="jx-perfil__avatar">
            <fa-icon [icon]="faUser" class="jx-perfil__avatar-icon" aria-hidden="true" />
          </div>
          @if (profile(); as p) {
            <strong class="jx-perfil__name">{{ p.full_name }}</strong>
            <p class="jx-perfil__sub">
              {{ vehicleLabel(p.vehicle_type) }}
              @if (p.vehicle_plate) { · {{ p.vehicle_plate }} }
            </p>
          }
        </header>

        <ul class="jx-perfil__list">
          <li class="jx-perfil__item" (click)="go('/entregador/perfil/editar-dados')">
            <span class="jx-perfil__item-left">
              <fa-icon [icon]="iconEdit" class="jx-perfil__item-icon" aria-hidden="true" />
              <span>Editar dados</span>
            </span>
            <span class="jx-perfil__chevron">›</span>
          </li>
          <li class="jx-perfil__item" (click)="go('/entregador/perfil/documentacao')">
            <span class="jx-perfil__item-left">
              <fa-icon [icon]="iconDocs" class="jx-perfil__item-icon" aria-hidden="true" />
              <span>Documentação</span>
            </span>
            <span class="jx-perfil__chevron">›</span>
          </li>
          <li class="jx-perfil__item" (click)="go('/entregador/perfil/avaliacoes')">
            <span class="jx-perfil__item-left">
              <fa-icon [icon]="iconStar" class="jx-perfil__item-icon" aria-hidden="true" />
              <span>Avaliações</span>
            </span>
            <span class="jx-perfil__chevron">›</span>
          </li>
        </ul>

        <button type="button" class="jx-perfil__logout" (click)="logout()">
          <fa-icon [icon]="faLogout" aria-hidden="true" />
          Sair da conta
        </button>
      </div>
      }
    </ion-content>
  `,
  styles: [`
    .jx-perfil {
      display: flex; flex-direction: column; gap: var(--jx-space-3);
      padding: var(--jx-space-4) var(--jx-space-4) var(--jx-space-6);
    }

    /* Header with avatar */
    .jx-perfil__header {
      display: flex; flex-direction: column; align-items: center;
      gap: var(--jx-space-2); padding-bottom: var(--jx-space-4);
    }
    .jx-perfil__page-title {
      font-family: var(--jx-font-display); font-size: var(--jx-text-lg);
      font-weight: var(--jx-weight-bold); margin: 0; color: var(--text);
    }
    .jx-perfil__avatar {
      width: 88px; height: 88px; border-radius: 50%;
      background: var(--brand-wash, hsl(24 80% 95%));
      display: grid; place-items: center; position: relative;
    }
    .jx-perfil__avatar-icon { font-size: 36px; color: var(--brand); }
    .jx-perfil__name {
      font-family: var(--jx-font-display); font-size: var(--jx-text-lg);
      font-weight: var(--jx-weight-bold); color: var(--text); text-align: center;
    }
    .jx-perfil__sub {
      margin: 0; font-family: var(--jx-font-mono); font-size: var(--jx-text-xs);
      color: var(--text-muted); text-align: center;
    }

    /* Menu list */
    .jx-perfil__list {
      list-style: none; margin: 0; padding: 0;
      display: flex; flex-direction: column;
    }
    .jx-perfil__item {
      display: flex; align-items: center; justify-content: space-between;
      min-height: 48px; padding: var(--jx-space-3) 0;
      border-bottom: 1px solid var(--border, hsl(0 0% 90%));
      font-size: var(--jx-text-sm); color: var(--text);
    }
    .jx-perfil__item-left { display: flex; align-items: center; gap: 12px; }
    .jx-perfil__item-icon { font-size: 18px; color: var(--brand, #e8722a); width: 24px; text-align: center; }
    .jx-perfil__item-value {
      font-size: var(--jx-text-xs); color: var(--text-muted); text-align: right; max-width: 60%;
    }
    .jx-perfil__item-right {
      display: flex; align-items: center; gap: var(--jx-space-2);
    }

    /* Status pills */
    .jx-perfil__status-pill {
      display: inline-block; padding: 2px 8px; border-radius: 999px;
      font-size: var(--jx-text-2xs); font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.04em;
      background: var(--surface-sunken); color: var(--text-muted);
    }
    .jx-perfil__status-pill--ok {
      background: var(--success-wash, hsl(120 40% 93%)); color: var(--success, hsl(120 40% 35%));
    }
    .jx-perfil__status-pill--err {
      background: var(--error-wash, hsl(0 70% 95%)); color: var(--error, #d32f2f);
    }
    .jx-perfil__status-pill--pending {
      background: var(--warning-wash, hsl(40 80% 92%)); color: var(--warning, hsl(40 80% 35%));
    }

    .jx-perfil__chevron {
      font-size: 20px; color: var(--text-muted, #ccc); font-weight: 300;
    }
    .jx-perfil__avg-stars {
      font-size: var(--jx-text-sm); font-weight: 600; color: var(--brand, #e8722a);
    }
    .jx-perfil__avg-stars small {
      font-weight: 400; color: var(--text-muted, #888); font-size: var(--jx-text-xs);
    }
    .jx-perfil__resend-btn {
      width: 32px; height: 32px; display: grid; place-items: center;
      background: var(--brand); color: var(--brand-contrast, #fff);
      border: none; border-radius: 50%; cursor: pointer; font-size: 14px;
    }

    /* Score card */
    .jx-perfil__score-card {
      background: var(--surface-elevated, #fff); border: 1px solid var(--border, hsl(0 0% 90%));
      border-radius: var(--jx-radius-lg); padding: var(--jx-space-3);
      display: flex; flex-direction: column; gap: var(--jx-space-2);
    }
    .jx-perfil__note {
      margin: 0; font-size: var(--jx-text-xs); color: var(--text-muted);
    }

    /* Logout */
    .jx-perfil__logout {
      width: 100%; min-height: 48px; display: flex; align-items: center;
      justify-content: center; gap: var(--jx-space-2);
      background: none; border: 1px solid var(--error, #d32f2f);
      border-radius: var(--jx-radius-full, 999px);
      color: var(--error, #d32f2f); font-size: var(--jx-text-sm);
      font-weight: var(--jx-weight-semibold); cursor: pointer; margin-top: var(--jx-space-3);
    }

    /* Modal de reenvio */
    .jx-resend-backdrop { position: fixed; inset: 0; z-index: 60; background: rgba(0,0,0,0.5); }
    .jx-resend-modal {
      position: fixed; bottom: 0; left: 0; right: 0; z-index: 70;
      background: var(--surface, #fff); border-radius: var(--jx-radius-xl) var(--jx-radius-xl) 0 0;
      padding: var(--jx-space-4); padding-bottom: max(var(--jx-space-5), env(safe-area-inset-bottom));
      display: flex; flex-direction: column; gap: var(--jx-space-3); max-height: 85vh; overflow-y: auto;
    }
    .jx-resend-modal__title { margin: 0; font-family: var(--jx-font-display); font-size: var(--jx-text-lg); font-weight: var(--jx-weight-bold); }
    .jx-resend-modal__info { display: flex; flex-direction: column; gap: var(--jx-space-1); font-size: var(--jx-text-sm); color: var(--text-muted); }
    .jx-resend-modal__info p { margin: 0; }
    .jx-resend-modal__err { margin: 0; font-size: var(--jx-text-xs); color: var(--error); }
    .jx-resend-modal__actions { display: flex; gap: var(--jx-space-2); }
    .jx-resend-modal__btn { flex: 1; min-height: 44px; border-radius: var(--jx-radius-md); font-weight: var(--jx-weight-semibold); cursor: pointer; border: none; }
    .jx-resend-modal__btn--cancel { background: var(--surface-sunken); color: var(--text); }
    .jx-resend-modal__btn--send { background: var(--brand); color: var(--brand-contrast, #fff); }
    .jx-resend-modal__btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .jx-resend-modal__doc-wrap { position: relative; }
    .jx-resend-modal__remove-x { position: absolute; top: 8px; right: 8px; width: 28px; height: 28px; display: grid; place-items: center; background: var(--error, #d32f2f); color: #fff; border: none; border-radius: 50%; font-size: 14px; font-weight: 700; cursor: pointer; z-index: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
  `],
})
export class EntregadorPerfilPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly cadastroSvc = inject(CourierCadastroService);
  private readonly locationSvc = inject(CourierLocationService);

  private readonly router = inject(Router);
  protected readonly faRotateRight = faRotateRight;
  protected readonly faLogout = faRightFromBracket;
  protected readonly faUser = faUser;
  protected readonly iconEdit = faPenToSquare;
  protected readonly iconDocs = faFolderOpen;
  protected readonly iconStar = faStar;

  protected readonly initialLoading = signal(true);
  protected readonly score = signal<CourierScore | null>(null);
  protected readonly profile = signal<CourierProfile | null>(null);

  // Modal de reenvio
  protected readonly resendDoc = signal<CourierDocumentItem | null>(null);
  protected readonly resendFile = signal<File | null>(null);
  protected readonly resendPreview = signal<string | null>(null);
  protected readonly resendUploading = signal(false);
  protected readonly resendError = signal<string | null>(null);


  protected readonly statusLabel = computed<string>(() => {
    const map: Record<string, string> = {
      active: 'Ativo — você pode receber ofertas',
      pending_kyc: 'Em análise — termine sua validação',
      mei_pending: 'Ativo — regularize seu MEI para receber pela plataforma',
      suspended: 'Suspenso — veja as disputas',
    };
    return map[this.auth.me()?.status ?? ''] ?? 'Cadastro em andamento';
  });

  protected go(path: string): void {
    void this.router.navigate([path]);
  }

  protected async logout(): Promise<void> {
    this.locationSvc.stop();
    await this.auth.logout();
    void this.router.navigate(['/entrar']);
  }

  private get courierId(): number | null {
    return this.auth.me()?.courier_id ?? null;
  }

  async ngOnInit(): Promise<void> {
    const id = this.courierId;
    if (!id) return;
    const [score, profile] = await Promise.all([
      this.svc.score(id),
      this.svc.profile(id),
    ]);
    this.score.set(score);
    this.profile.set(profile);
    this.initialLoading.set(false);
  }

  // --- Modal de reenvio ---
  protected openResendModal(doc: CourierDocumentItem): void {
    this.resendDoc.set(doc);
    this.resendFile.set(null);
    this.resendPreview.set(null);
    this.resendError.set(null);
  }

  protected closeResendModal(): void {
    if (this.resendUploading()) return;
    if (this.resendPreview()) URL.revokeObjectURL(this.resendPreview()!);
    this.resendDoc.set(null);
    this.resendFile.set(null);
    this.resendPreview.set(null);
  }

  protected clearResendFile(): void {
    if (this.resendPreview()) URL.revokeObjectURL(this.resendPreview()!);
    this.resendFile.set(null);
    this.resendPreview.set(null);
  }

  protected onResendFile(file: File): void {
    if (this.resendPreview()) URL.revokeObjectURL(this.resendPreview()!);
    this.resendFile.set(file);
    this.resendPreview.set(URL.createObjectURL(file));
    this.resendError.set(null);
  }

  protected async submitResend(): Promise<void> {
    const doc = this.resendDoc();
    const file = this.resendFile();
    const id = this.courierId;
    if (!doc || !file || !id) return;

    this.resendUploading.set(true);
    this.resendError.set(null);

    try {
      const sha = await this.sha256(file);
      const presign = await this.cadastroSvc.presignDocument(id, {
        kind: doc.kind as 'selfie' | 'cnh' | 'crlv' | 'mei' | 'antecedentes',
        sha256_client: sha,
        content_type: 'image/jpeg',
      });
      if (!presign) {
        this.resendError.set('Não foi possível iniciar o envio. Tente novamente.');
        return;
      }
      const ok = await this.cadastroSvc.uploadToStorage(presign, file);
      if (!ok) {
        this.resendError.set('Falha no envio da foto. Verifique sua conexão.');
        return;
      }
      await this.cadastroSvc.completeDocument(id, presign.document_id);

      // Atualiza o profile local e fecha o modal
      this.profile.update((p) => {
        if (!p) return p;
        return {
          ...p,
          documents: p.documents.map((d) =>
            d.id === doc.id ? { ...d, status: 'pending', reject_reason: null, reject_detail: null } : d
          ),
        };
      });
      this.resendUploading.set(false);
      this.closeResendModal();
      return;
    } catch {
      this.resendError.set('Erro inesperado. Tente novamente.');
    } finally {
      this.resendUploading.set(false);
    }
  }

  private async sha256(file: Blob): Promise<string> {
    const buf = await file.arrayBuffer();
    const digest = await crypto.subtle.digest('SHA-256', buf);
    return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
  }

  // --- Labels ---
  protected vehicleLabel(v: string): string {
    return { moto: 'Moto', bicicleta: 'Bicicleta', carro: 'Carro', a_pe: 'A pé' }[v] ?? v;
  }

  protected docLabel(kind: string): string {
    return { selfie: 'CPF + Selfie', cnh: 'CNH com EAR', crlv: 'CRLV', mei: 'MEI', antecedentes: 'Antecedentes' }[kind] ?? kind;
  }

  protected docStatusLabel(status: string): string {
    return { approved: '✓ Aprovado', rejected: 'Reprovado', pending: 'Em análise', pending_upload: 'Aguardando envio' }[status] ?? status;
  }

  protected reasonLabel(reason: string | null): string {
    return reason ? (REASON_LABELS[reason] ?? reason) : 'Não informado';
  }
}
