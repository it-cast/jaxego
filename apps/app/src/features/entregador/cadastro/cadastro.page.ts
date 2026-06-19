import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import {
  DocCardComponent,
  WizardStepperComponent,
  type DocStatus,
  type WizardStep,
} from '@jaxego/shared/components';
import {
  ErrorStateComponent,
  WarnBannerComponent,
} from '@jaxego/shared/state';
import {
  isCpfComplete,
  isPhoneComplete,
  maskCpf,
  maskPhone,
  phoneToE164,
} from '@jaxego/shared/util/br-format';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { COURIER_ERROR, type KycLevel, type VehicleType } from './cadastro.models';
import { CourierCadastroService } from './cadastro.service';

const DRAFT_KEY = 'jx-courier-onboarding';

function normalizeKycLevel(level: string | null | undefined): KycLevel {
  return level === 'completa' ? 'completa' : 'simples';
}

interface DocItem {
  kind: 'selfie' | 'cnh' | 'crlv' | 'antecedentes';
  title: string;
  purpose: string;
  capture: 'environment' | 'user';
  status: DocStatus;
  file: File | null;
  previewUrl: string | null;
}

/**
 * Cadastro do entregador — wizard tela 03 (F-02). Coleta todos os dados e
 * fotos em memória ao longo dos passos. O signup (POST /v1/couriers/signup)
 * só acontece no último passo; após receber o courier_id, as fotos são
 * enviadas em sequência. Se algum upload falhar, o courier já existe com
 * pending_kyc e o entregador pode reenviar depois.
 */
@Component({
  selector: 'jx-cadastro-entregador',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    FaIconComponent,
    WizardStepperComponent,
    DocCardComponent,
    ErrorStateComponent,
    WarnBannerComponent,
  ],
  templateUrl: './cadastro.page.html',
  styleUrl: './cadastro.page.scss',
})
export class CadastroEntregadorPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);
  private readonly couriers = inject(CourierCadastroService);
  private readonly router = inject(Router);

  protected readonly areas = signal<{ id: number; name: string; level: KycLevel }[]>([]);

  protected readonly current = signal(0);
  protected readonly loading = signal(false);
  protected readonly stepError = signal<string | null>(null);
  protected readonly level = signal<KycLevel>('simples');
  protected readonly submitting = signal(false);
  protected readonly submitProgress = signal('');

  protected readonly showPassword = signal(false);
  protected readonly faEye = faEye;
  protected readonly faEyeSlash = faEyeSlash;
  protected readonly docs = signal<DocItem[]>([]);

  protected readonly form = this.fb.nonNullable.group({
    area_id: [0, Validators.min(1)],
    cpf: ['', Validators.required],
    full_name: ['', [Validators.required, Validators.maxLength(120)]],
    phone: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(10)]],
    password_confirm: ['', Validators.required],
    vehicle_type: ['moto' as VehicleType, Validators.required],
    vehicle_plate: [''],
    mei_cnpj: [''],
    consent: [false, Validators.requiredTrue],
  });

  protected readonly steps = computed<WizardStep[]>(() => {
    const base: WizardStep[] = [
      { label: 'Dados' },
      { label: 'Selfie' },
      { label: 'Veículo' },
    ];
    return this.level() === 'completa' ? [...base, { label: 'Documentos' }] : base;
  });

  protected readonly isLastStep = computed(
    () => this.current() === this.steps().length - 1
  );

  constructor() {
    this.restoreDraft();
  }

  async ngOnInit(): Promise<void> {
    try {
      const data = await firstValueFrom(
        this.http.get<{ id: number; name: string; kyc_level: string }[]>('/v1/areas/public')
      );
      this.areas.set(
        data.map((a) => ({ id: a.id, name: a.name, level: normalizeKycLevel(a.kyc_level) }))
      );
    } catch {
      // Areas indisponíveis — o select fica vazio com mensagem.
    }
  }

  // --- masking + validation -------------------------------------------------
  protected onCpfInput(value: string): void {
    this.form.controls.cpf.setValue(maskCpf(value));
  }
  protected onPhoneInput(value: string): void {
    this.form.controls.phone.setValue(maskPhone(value));
  }
  protected onAreaChange(areaId: number): void {
    const area = this.areas().find((a) => a.id === Number(areaId));
    this.form.controls.area_id.setValue(area?.id ?? 0);
    const level = normalizeKycLevel(area?.level);
    this.level.set(level);
    this.initDocs(level);
  }

  protected togglePassword(): void {
    this.showPassword.update((v) => !v);
  }

  protected passwordMismatch(): boolean {
    const pw = this.form.controls.password.value;
    const confirm = this.form.controls.password_confirm.value;
    return confirm.length > 0 && pw !== confirm;
  }

  protected cpfError(): string | null {
    const v = this.form.controls.cpf.value;
    if (v && !isCpfComplete(v)) return 'CPF incompleto. Confira os 11 dígitos.';
    return null;
  }
  protected phoneError(): string | null {
    const v = this.form.controls.phone.value;
    if (v && !isPhoneComplete(v)) return 'Telefone precisa de DDD e 9 dígitos.';
    return null;
  }
  protected get motorized(): boolean {
    const t = this.form.controls.vehicle_type.value;
    return t === 'moto' || t === 'carro';
  }

  // --- doc items (fotos guardadas em memória como File) ---------------------
  private initDocs(level: KycLevel): void {
    const currentByKind = new Map(this.docs().map((doc) => [doc.kind, doc]));
    const items: DocItem[] = [
      { kind: 'selfie', title: 'Selfie com documento', purpose: 'Confirma que é você de verdade.', capture: 'user', status: 'pending_upload', file: null, previewUrl: null },
    ];
    if (level === 'completa') {
      items.push(
        { kind: 'cnh', title: 'CNH com EAR', purpose: 'Mostra que você pode dirigir fazendo entregas.', capture: 'environment', status: 'pending_upload', file: null, previewUrl: null },
        { kind: 'crlv', title: 'CRLV', purpose: 'Confirma que o veículo está regular.', capture: 'environment', status: 'pending_upload', file: null, previewUrl: null },
      );
    }
    this.docs.set(items.map((item) => currentByKind.get(item.kind) ?? item));
  }

  protected onFileSelected(item: DocItem, file: File): void {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
    const previewUrl = URL.createObjectURL(file);
    this.docs.update((list) =>
      list.map((d) => d.kind === item.kind ? { ...d, file, previewUrl, status: 'pending_upload' as DocStatus } : d)
    );
  }

  protected removeFile(item: DocItem): void {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
    this.docs.update((list) =>
      list.map((d) => d.kind === item.kind ? { ...d, file: null, previewUrl: null, status: 'pending_upload' as DocStatus } : d)
    );
  }

  protected docHasFile(kind: string): boolean {
    return this.docs().some((d) => d.kind === kind && d.file !== null);
  }

  // --- step navigation ------------------------------------------------------
  protected goToStep(index: number): void {
    if (index < this.current()) {
      this.stepError.set(null);
      this.current.set(index);
    }
  }

  protected async next(): Promise<void> {
    this.stepError.set(null);

    if (this.current() === 0) {
      if (!this.validateStep1()) return;
      this.persistDraft();
      this.current.update((c) => c + 1);
      return;
    }

    if (this.current() === 1) {
      if (!this.docHasFile('selfie')) {
        this.stepError.set('Tire a selfie com documento para continuar.');
        return;
      }
      this.current.update((c) => c + 1);
      return;
    }

    if (this.isLastStep()) {
      await this.submitAll();
      return;
    }

    this.current.update((c) => c + 1);
  }

  private validateStep1(): boolean {
    const f = this.form.getRawValue();
    if (this.passwordMismatch()) {
      this.form.markAllAsTouched();
      this.stepError.set('As senhas não coincidem.');
      return false;
    }
    if (this.cpfError() || !f.area_id || f.consent !== true) {
      this.form.markAllAsTouched();
      this.stepError.set('Confira os dados e aceite a Política para continuar.');
      return false;
    }
    return true;
  }

  // --- submit tudo no final -------------------------------------------------
  private async submitAll(): Promise<void> {
    const f = this.form.getRawValue();
    this.submitting.set(true);
    this.submitProgress.set('Criando sua conta…');
    this.stepError.set(null);

    const result = await this.couriers.signup({
      area_id: f.area_id,
      cpf: f.cpf.replace(/\D/g, ''),
      full_name: f.full_name,
      phone_e164: phoneToE164(f.phone),
      email: f.email,
      password: f.password,
      vehicle_type: f.vehicle_type,
      vehicle_plate: this.motorized ? f.vehicle_plate || null : null,
      consent: f.consent,
    });

    if (!result.ok || !result.data) {
      this.submitting.set(false);
      this.submitProgress.set('');
      if (result.code === COURIER_ERROR.EXISTS) {
        this.stepError.set(result.message ?? 'Você já tem cadastro nessa cidade. Recupere o acesso.');
      } else {
        this.stepError.set(result.message ?? 'Não foi possível concluir agora. Tente de novo.');
      }
      return;
    }

    const courierId = result.data.courier_id;

    // MEI (opcional)
    const cnpj = f.mei_cnpj.replace(/\D/g, '');
    if (cnpj.length === 14) {
      await this.couriers.submitMei(courierId, cnpj);
    }

    // Upload das fotos selecionadas
    const docsWithFile = this.docs().filter((d) => d.file !== null);
    for (let i = 0; i < docsWithFile.length; i++) {
      const doc = docsWithFile[i];
      this.submitProgress.set(`Enviando ${doc.title} (${i + 1}/${docsWithFile.length})…`);
      await this.uploadDoc(courierId, doc);
    }

    this.submitting.set(false);
    this.clearDraft();
    void this.router.navigate(['/entregador/cadastro/em-analise']);
  }

  private async uploadDoc(courierId: number, doc: DocItem): Promise<void> {
    if (!doc.file) return;
    try {
      const sha = await this.sha256(doc.file);
      const presign = await this.couriers.presignDocument(courierId, {
        kind: doc.kind,
        sha256_client: sha,
        content_type: 'image/jpeg',
      });
      if (!presign) return;
      const ok = await this.couriers.uploadToStorage(presign, doc.file);
      if (ok) {
        await this.couriers.completeDocument(courierId, presign.document_id);
      }
    } catch {
      // Upload falhou — courier já existe com pending_kyc, pode reenviar depois.
    }
  }

  private async sha256(file: Blob): Promise<string> {
    const buf = await file.arrayBuffer();
    const digest = await crypto.subtle.digest('SHA-256', buf);
    return [...new Uint8Array(digest)]
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  }

  // --- draft persistence (NUNCA salva password/password_confirm/files) ------
  private persistDraft(): void {
    const { password, password_confirm, ...rest } = this.form.getRawValue();
    void password, password_confirm;
    try {
      sessionStorage.setItem(
        DRAFT_KEY,
        JSON.stringify({ ...rest, step: this.current(), level: this.level() })
      );
    } catch { /* non-fatal */ }
  }
  private restoreDraft(): void {
    try {
      const raw = sessionStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const draft = JSON.parse(raw) as Record<string, unknown> & {
        step?: number;
        level?: KycLevel;
      };
      const { step, level, ...values } = draft;
      this.form.patchValue(values as never);
      if (level) {
        const restoredLevel = normalizeKycLevel(level);
        this.level.set(restoredLevel);
        this.initDocs(restoredLevel);
      }
      if (typeof step === 'number') {
        this.current.set(Math.min(step, this.steps().length - 1));
      }
    } catch { /* ignore corrupt draft */ }
  }
  private clearDraft(): void {
    try { sessionStorage.removeItem(DRAFT_KEY); } catch { /* ignore */ }
  }
}
