import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { IonContent } from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faLock, faEye, faEyeSlash, faXmark } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { PageHeaderComponent, DotsLoaderComponent } from '@jaxego/shared/components';
import { CourierProfile, EntregadorService } from '../entregador.service';

@Component({
  selector: 'jx-editar-dados',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, FormsModule, FaIconComponent, PageHeaderComponent, DotsLoaderComponent],
  template: `
    <ion-content>
      @if (loading()) {
        <jx-dots-loader />
      } @else {
        <jx-page-header title="Editar dados" backLink="/entregador/perfil" />
        <div class="jx-edit">
          <label class="jx-edit__field">
            <span class="jx-edit__label">Nome</span>
            <input class="jx-edit__input" [(ngModel)]="name" maxlength="120" />
          </label>

          <label class="jx-edit__field">
            <span class="jx-edit__label">E-mail</span>
            <input class="jx-edit__input" [value]="profile()?.email_masked" disabled />
          </label>

          <label class="jx-edit__field">
            <span class="jx-edit__label">Telefone</span>
            <input class="jx-edit__input" [value]="profile()?.phone_masked" disabled />
          </label>

          <label class="jx-edit__field">
            <span class="jx-edit__label">CPF</span>
            <input class="jx-edit__input" [value]="profile()?.cpf_masked" disabled />
          </label>

          <label class="jx-edit__field">
            <span class="jx-edit__label">Equipe</span>
            <input class="jx-edit__input" [value]="profile()?.team_name ?? 'Sem equipe'" disabled />
          </label>

          <button class="jx-edit__pwd-btn" (click)="showPwdModal.set(true)">
            <fa-icon [icon]="iconLock" aria-hidden="true" /> Alterar senha
          </button>

          @if (msg(); as m) {
            <p class="jx-edit__msg" [class.jx-edit__msg--ok]="m.tone === 'ok'" [class.jx-edit__msg--err]="m.tone === 'err'">{{ m.text }}</p>
          }

          <button class="jx-edit__btn" [disabled]="saving()" (click)="save()">
            {{ saving() ? 'Salvando...' : 'Salvar' }}
          </button>
        </div>
      }

      @if (showPwdModal()) {
        <div class="jx-modal-overlay" (click)="closePwdModal()">
          <div class="jx-modal" (click)="$event.stopPropagation()">
            <div class="jx-modal__header">
              <h3 class="jx-modal__title">Alterar senha</h3>
              <button class="jx-modal__close" (click)="closePwdModal()">
                <fa-icon [icon]="iconXmark" aria-hidden="true" />
              </button>
            </div>

            <div class="jx-modal__body">
              <label class="jx-edit__field">
                <span class="jx-edit__label">Senha atual</span>
                <div class="jx-edit__input-wrap">
                  <input class="jx-edit__input jx-edit__input--full"
                    [type]="showCurrent() ? 'text' : 'password'"
                    [(ngModel)]="currentPassword" />
                  <button class="jx-edit__eye" type="button" (click)="showCurrent.set(!showCurrent())">
                    <fa-icon [icon]="showCurrent() ? iconEyeSlash : iconEye" aria-hidden="true" />
                  </button>
                </div>
              </label>

              <label class="jx-edit__field">
                <span class="jx-edit__label">Nova senha</span>
                <div class="jx-edit__input-wrap">
                  <input class="jx-edit__input jx-edit__input--full"
                    [type]="showNew() ? 'text' : 'password'"
                    [(ngModel)]="newPassword" />
                  <button class="jx-edit__eye" type="button" (click)="showNew.set(!showNew())">
                    <fa-icon [icon]="showNew() ? iconEyeSlash : iconEye" aria-hidden="true" />
                  </button>
                </div>
              </label>

              <label class="jx-edit__field">
                <span class="jx-edit__label">Confirmar nova senha</span>
                <div class="jx-edit__input-wrap">
                  <input class="jx-edit__input jx-edit__input--full"
                    [type]="showConfirm() ? 'text' : 'password'"
                    [(ngModel)]="confirmPassword" />
                  <button class="jx-edit__eye" type="button" (click)="showConfirm.set(!showConfirm())">
                    <fa-icon [icon]="showConfirm() ? iconEyeSlash : iconEye" aria-hidden="true" />
                  </button>
                </div>
              </label>

              @if (pwdMsg(); as m) {
                <p class="jx-edit__msg" [class.jx-edit__msg--ok]="m.tone === 'ok'" [class.jx-edit__msg--err]="m.tone === 'err'">{{ m.text }}</p>
              }
            </div>

            <button class="jx-edit__btn" [disabled]="savingPwd()" (click)="savePassword()">
              {{ savingPwd() ? 'Salvando...' : 'Alterar senha' }}
            </button>
          </div>
        </div>
      }
    </ion-content>
  `,
  styles: [`
    .jx-edit { padding: var(--jx-space-4); display: flex; flex-direction: column; gap: var(--jx-space-3); }
    .jx-edit__field { display: flex; flex-direction: column; gap: 4px; }
    .jx-edit__label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-muted, #888); }
    .jx-edit__input { min-height: 44px; padding: 0 12px; border: 1px solid var(--border, #ddd); border-radius: 12px; font-size: 15px; color: var(--text); background: #fff; }
    .jx-edit__input:focus { outline: none; border-color: var(--brand, #e8722a); }
    .jx-edit__input-wrap { position: relative; display: flex; align-items: center; }
    .jx-edit__input--full { width: 100%; padding-right: 44px; }
    .jx-edit__eye { position: absolute; right: 4px; width: 36px; height: 36px; border: 0; background: transparent; color: var(--text-muted, #888); font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    .jx-edit__input:disabled { background: var(--bg-muted, #f5f5f5); color: var(--text-muted, #888); opacity: 1; -webkit-text-fill-color: var(--text-muted, #888); }
    .jx-edit__btn { min-height: 50px; border: 0; border-radius: 999px; background: var(--brand, #e8722a); color: #fff; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 8px; }
    .jx-edit__btn:disabled { opacity: 0.5; }
    .jx-edit__pwd-btn { min-height: 44px; border: 1px solid var(--border, #ddd); border-radius: 12px; background: #fff; color: var(--text); font-size: 15px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; }
    .jx-edit__pwd-btn:active { background: var(--bg-hover, #f5f5f5); }
    .jx-edit__msg { margin: 0; font-size: 14px; font-weight: 600; }
    .jx-edit__msg--ok { color: var(--success, #2e7d32); }
    .jx-edit__msg--err { color: var(--error, #d32f2f); }

    .jx-modal-overlay { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,0.5); display: flex; align-items: flex-end; justify-content: center; animation: fadeIn .2s ease; }
    .jx-modal { width: 100%; max-width: 500px; background: #fff; border-radius: 20px 20px 0 0; padding: var(--jx-space-4); display: flex; flex-direction: column; gap: var(--jx-space-3); animation: slideUp .25s ease; }
    .jx-modal__header { display: flex; align-items: center; justify-content: space-between; }
    .jx-modal__title { margin: 0; font-size: 18px; font-weight: 700; color: var(--text); }
    .jx-modal__close { width: 36px; height: 36px; border: 0; background: transparent; color: var(--text-muted, #888); font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
    .jx-modal__body { display: flex; flex-direction: column; gap: var(--jx-space-3); }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
  `],
})
export class EditarDadosPage implements OnInit {
  protected readonly iconLock = faLock;
  protected readonly iconEye = faEye;
  protected readonly iconEyeSlash = faEyeSlash;
  protected readonly iconXmark = faXmark;

  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);

  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly profile = signal<CourierProfile | null>(null);
  protected readonly msg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected name = '';

  protected readonly showPwdModal = signal(false);
  protected readonly savingPwd = signal(false);
  protected readonly pwdMsg = signal<{ text: string; tone: 'ok' | 'err' } | null>(null);
  protected readonly showCurrent = signal(false);
  protected readonly showNew = signal(false);
  protected readonly showConfirm = signal(false);
  protected currentPassword = '';
  protected newPassword = '';
  protected confirmPassword = '';

  async ngOnInit(): Promise<void> {
    const id = this.auth.me()?.courier_id;
    if (!id) return;
    const p = await this.svc.profile(id);
    this.profile.set(p);
    this.name = p?.full_name ?? '';
    this.loading.set(false);
  }

  protected async save(): Promise<void> {
    const id = this.auth.me()?.courier_id;
    if (!id) return;
    this.saving.set(true);
    this.msg.set(null);
    const data: Record<string, any> = {};
    if (this.name.trim()) data['full_name'] = this.name.trim();
    const ok = await this.svc.updateProfile(id, data);
    this.saving.set(false);
    this.msg.set(ok ? { text: 'Dados atualizados!', tone: 'ok' } : { text: 'Erro ao salvar.', tone: 'err' });
  }

  protected closePwdModal(): void {
    this.showPwdModal.set(false);
    this.pwdMsg.set(null);
    this.currentPassword = '';
    this.newPassword = '';
    this.confirmPassword = '';
    this.showCurrent.set(false);
    this.showNew.set(false);
    this.showConfirm.set(false);
  }

  protected async savePassword(): Promise<void> {
    if (!this.currentPassword) {
      this.pwdMsg.set({ text: 'Informe a senha atual.', tone: 'err' });
      return;
    }
    if (!this.newPassword) {
      this.pwdMsg.set({ text: 'Informe a nova senha.', tone: 'err' });
      return;
    }
    if (this.newPassword !== this.confirmPassword) {
      this.pwdMsg.set({ text: 'As senhas não coincidem.', tone: 'err' });
      return;
    }
    const id = this.auth.me()?.courier_id;
    if (!id) return;
    this.savingPwd.set(true);
    this.pwdMsg.set(null);
    const ok = await this.svc.updateProfile(id, {
      current_password: this.currentPassword,
      password: this.newPassword,
    });
    this.savingPwd.set(false);
    if (ok) {
      this.pwdMsg.set({ text: 'Senha alterada com sucesso!', tone: 'ok' });
      setTimeout(() => this.closePwdModal(), 1500);
    } else {
      this.pwdMsg.set({ text: 'Senha atual incorreta.', tone: 'err' });
    }
  }
}
