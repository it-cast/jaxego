import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faRotateRight } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { DocCardComponent } from '@jaxego/shared/components';
import { PageHeaderComponent, DotsLoaderComponent } from '@jaxego/shared/components';
import { CourierDocumentItem, CourierProfile, EntregadorService } from '../entregador.service';
import { CourierCadastroService } from '../cadastro/cadastro.service';

@Component({
  selector: 'jx-documentacao',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, FaIconComponent, DocCardComponent, PageHeaderComponent, DotsLoaderComponent],
  template: `
    <ion-content>
      @if (loading()) {
        <jx-dots-loader />
      } @else {
        <jx-page-header title="Documentacao" backLink="/entregador/perfil" />
        <div class="jx-docs">
          @if (profile(); as p) {
            <ul class="jx-docs__list">
              @for (d of p.documents; track d.id) {
                <li class="jx-docs__item">
                  <div class="jx-docs__row">
                    <span class="jx-docs__kind">{{ docLabel(d.kind) }}</span>
                    <div class="jx-docs__right">
                      <span class="jx-docs__status"
                        [class.jx-docs__status--ok]="d.status === 'approved'"
                        [class.jx-docs__status--err]="d.status === 'rejected'"
                        [class.jx-docs__status--pending]="d.status === 'pending' || d.status === 'pending_upload'"
                      >{{ statusLabel(d.status) }}</span>
                      @if (d.status === 'rejected') {
                        <button class="jx-docs__resend" (click)="openResend(d)">
                          <fa-icon [icon]="faResend" aria-hidden="true" />
                        </button>
                      }
                    </div>
                  </div>
                  @if (d.status === 'rejected' && d.reject_reason) {
                    <p class="jx-docs__reason">Motivo: {{ reasonLabel(d.reject_reason) }}@if (d.reject_detail) { — {{ d.reject_detail }}}</p>
                  }
                </li>
              }
            </ul>
          }

          @if (resendDoc()) {
            <div class="jx-docs__backdrop" (click)="closeResend()"></div>
            <div class="jx-docs__modal">
              <h2 class="jx-docs__modal-title">Reenviar {{ docLabel(resendDoc()!.kind) }}</h2>
              <jx-doc-card
                [title]="docLabel(resendDoc()!.kind)"
                mode="edit"
                status="pending_upload"
                [captureMode]="resendDoc()!.kind === 'selfie' ? 'user' : 'environment'"
                purpose="Selecione a nova foto"
                [previewUrl]="resendPreview()"
                [hideBadge]="true"
                uploadState="idle"
                (fileSelected)="onFile($event)"
              />
              @if (resendError()) { <p class="jx-docs__err">{{ resendError() }}</p> }
              <div class="jx-docs__modal-actions">
                <button class="jx-docs__btn-cancel" [disabled]="uploading()" (click)="closeResend()">Cancelar</button>
                <button class="jx-docs__btn-send" [disabled]="!resendFile() || uploading()" (click)="submitResend()">
                  {{ uploading() ? 'Enviando...' : 'Enviar' }}
                </button>
              </div>
            </div>
          }
        </div>
      }
    </ion-content>
  `,
  styles: [`
    .jx-docs { padding: var(--jx-space-4); }
    .jx-docs__list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
    .jx-docs__item { padding: var(--jx-space-3) 0; border-bottom: 1px solid var(--border, #eee); }
    .jx-docs__row { display: flex; align-items: center; justify-content: space-between; }
    .jx-docs__kind { font-size: 15px; color: var(--text); }
    .jx-docs__right { display: flex; align-items: center; gap: 8px; }
    .jx-docs__status { font-size: 11px; font-weight: 600; text-transform: uppercase; padding: 2px 8px; border-radius: 999px; background: var(--surface-sunken, #f0f0f0); color: var(--text-muted, #888); }
    .jx-docs__status--ok { background: hsl(120 40% 93%); color: hsl(120 50% 35%); }
    .jx-docs__status--err { background: hsl(0 70% 95%); color: hsl(0 60% 45%); }
    .jx-docs__status--pending { background: hsl(40 80% 92%); color: hsl(40 80% 35%); }
    .jx-docs__resend { width: 32px; height: 32px; display: grid; place-items: center; background: var(--brand, #e8722a); color: #fff; border: 0; border-radius: 50%; cursor: pointer; font-size: 14px; }
    .jx-docs__reason { margin: 4px 0 0; font-size: 12px; color: var(--error, #d32f2f); }
    .jx-docs__backdrop { position: fixed; inset: 0; z-index: 60; background: rgba(0,0,0,0.5); }
    .jx-docs__modal { position: fixed; bottom: 0; left: 0; right: 0; z-index: 70; background: #fff; border-radius: 20px 20px 0 0; padding: var(--jx-space-4); display: flex; flex-direction: column; gap: var(--jx-space-3); max-height: 85vh; overflow-y: auto; animation: jx-slide-up 0.3s ease; }
    @keyframes jx-slide-up { from { transform: translateY(100%); } to { transform: translateY(0); } }
    .jx-docs__modal-title { margin: 0; font-size: 18px; font-weight: 700; text-align: center; }
    .jx-docs__err { margin: 0; font-size: 12px; color: var(--error, #d32f2f); }
    .jx-docs__modal-actions { display: flex; gap: 8px; }
    .jx-docs__btn-cancel, .jx-docs__btn-send { flex: 1; min-height: 44px; border-radius: 12px; font-weight: 600; cursor: pointer; border: 0; }
    .jx-docs__btn-cancel { background: var(--surface-sunken, #f0f0f0); color: var(--text); }
    .jx-docs__btn-send { background: var(--brand, #e8722a); color: #fff; }
    .jx-docs__btn-send:disabled, .jx-docs__btn-cancel:disabled { opacity: 0.5; }
  `],
})
export class DocumentacaoPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);
  private readonly cadastroSvc = inject(CourierCadastroService);

  protected readonly faResend = faRotateRight;
  protected readonly loading = signal(true);
  protected readonly profile = signal<CourierProfile | null>(null);
  protected readonly resendDoc = signal<CourierDocumentItem | null>(null);
  protected readonly resendFile = signal<File | null>(null);
  protected readonly resendPreview = signal<string | null>(null);
  protected readonly resendError = signal<string | null>(null);
  protected readonly uploading = signal(false);

  async ngOnInit(): Promise<void> {
    const id = this.auth.me()?.courier_id;
    if (!id) return;
    this.profile.set(await this.svc.profile(id));
    this.loading.set(false);
  }

  protected docLabel(kind: string): string {
    return { selfie: 'CPF + Selfie', cnh: 'CNH com EAR', crlv: 'CRLV', mei: 'MEI', antecedentes: 'Antecedentes' }[kind] ?? kind;
  }
  protected statusLabel(s: string): string {
    return { approved: 'Aprovado', rejected: 'Reprovado', pending: 'Em analise', pending_upload: 'Aguardando envio' }[s] ?? s;
  }
  protected reasonLabel(r: string | null): string {
    return r ? ({ ilegivel: 'Ilegivel', sem_ear: 'Sem EAR', vencida: 'Vencida', nao_confere: 'Nao confere', outro: 'Outro' }[r] ?? r) : '';
  }

  protected openResend(doc: CourierDocumentItem): void { this.resendDoc.set(doc); this.resendFile.set(null); this.resendPreview.set(null); this.resendError.set(null); }
  protected closeResend(): void { if (!this.uploading()) { this.resendDoc.set(null); } }
  protected onFile(file: File): void { this.resendFile.set(file); this.resendPreview.set(URL.createObjectURL(file)); this.resendError.set(null); }

  protected async submitResend(): Promise<void> {
    const doc = this.resendDoc(); const file = this.resendFile(); const id = this.auth.me()?.courier_id;
    if (!doc || !file || !id) return;
    this.uploading.set(true);
    try {
      const sha = await this.sha256(file);
      const presign = await this.cadastroSvc.presignDocument(id, { kind: doc.kind as any, sha256_client: sha, content_type: 'image/jpeg' });
      if (!presign) { this.resendError.set('Erro ao iniciar envio.'); return; }
      const ok = await this.cadastroSvc.uploadToStorage(presign, file);
      if (!ok) { this.resendError.set('Falha no envio.'); return; }
      await this.cadastroSvc.completeDocument(id, presign.document_id);
      this.profile.update(p => p ? { ...p, documents: p.documents.map(d => d.id === doc.id ? { ...d, status: 'pending', reject_reason: null, reject_detail: null } : d) } : p);
      this.uploading.set(false); this.closeResend();
    } catch { this.resendError.set('Erro inesperado.'); } finally { this.uploading.set(false); }
  }

  private async sha256(file: Blob): Promise<string> {
    const buf = await file.arrayBuffer();
    const digest = await crypto.subtle.digest('SHA-256', buf);
    return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('');
  }
}
