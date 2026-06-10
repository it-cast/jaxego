import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { IonContent } from '@ionic/angular/standalone';
import {
  DocCardComponent,
  WizardStepperComponent,
  type DocStatus,
  type WizardStep,
} from '../../../shared/components';
import {
  ErrorStateComponent,
  WarnBannerComponent,
} from '../../../shared/state';
import {
  isCpfComplete,
  isPhoneComplete,
  maskCpf,
  maskPhone,
  phoneToE164,
} from '../../loja/cadastro/br-format';
import { COURIER_ERROR, type KycLevel, type VehicleType } from './cadastro.models';
import { CourierCadastroService } from './cadastro.service';

const DRAFT_KEY = 'jx-courier-onboarding';

/** A document item the wizard tracks (status drives the jx-doc-card badge). */
interface DocItem {
  kind: 'selfie' | 'cnh' | 'crlv' | 'antecedentes';
  title: string;
  purpose: string;
  capture: 'environment' | 'user';
  status: DocStatus;
  documentId?: number;
}

/**
 * Cadastro do entregador — wizard tela 03 (UI-SPEC §2, Ionic mobile-first).
 *
 * The stepper is CONDITIONAL on the KYC level the chosen area requires (D-03):
 * 3 steps (simples: dados · selfie · veículo) or 4 (completa: + documentos). The
 * level is known after step 1 (the area is picked there). Step 5 "bairros/preços"
 * is OUT (Phase 6). Fields are BR-masked, validated on blur; the draft persists
 * in sessionStorage WITHOUT the password (E1 resumption). E2 (CPF same area) and
 * E3 (mei_pending) surface as actionable messages. Zero hardcoded hex; dark mode
 * via inherited semantic vars (DEC-001).
 */
@Component({
  selector: 'jx-cadastro-entregador',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    IonContent,
    ReactiveFormsModule,
    WizardStepperComponent,
    DocCardComponent,
    ErrorStateComponent,
    WarnBannerComponent,
  ],
  templateUrl: './cadastro.page.html',
  styleUrl: './cadastro.page.scss',
})
export class CadastroEntregadorPage {
  private readonly fb = inject(FormBuilder);
  private readonly couriers = inject(CourierCadastroService);
  private readonly router = inject(Router);

  // Areas the courier can pick (loaded from the backend in a fuller impl; the
  // pilot ships Pádua/Itaocara — kept minimal and DATA-DRIVEN, no hardcoded copy).
  protected readonly areas = signal<{ id: number; name: string; level: KycLevel }[]>([
    { id: 1, name: 'Pádua', level: 'completa' },
    { id: 2, name: 'Itaocara', level: 'simples' },
  ]);

  protected readonly current = signal(0);
  protected readonly loading = signal(false);
  protected readonly stepError = signal<string | null>(null);
  protected readonly courierId = signal<number | null>(null);
  protected readonly level = signal<KycLevel>('simples');
  protected readonly meiPending = signal(false);
  protected readonly offlineWarn = signal<string | null>(null);

  protected readonly docs = signal<DocItem[]>([]);

  protected readonly form = this.fb.nonNullable.group({
    area_id: [0, Validators.min(1)],
    cpf: ['', Validators.required],
    full_name: ['', [Validators.required, Validators.maxLength(120)]],
    phone: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(10)]],
    vehicle_type: ['moto' as VehicleType, Validators.required],
    vehicle_plate: [''],
    mei_cnpj: [''],
    consent: [false, Validators.requiredTrue],
  });

  // Stepper labels depend on the level (3 or 4 steps).
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
    this.level.set(area?.level ?? 'simples');
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
      await this.submitStep1();
      return;
    }
    if (this.isLastStep()) {
      await this.submitFinal();
      return;
    }
    this.current.update((c) => c + 1);
  }

  /** Step 1 creates the courier (pending_kyc) and fixes the KYC level. */
  private async submitStep1(): Promise<void> {
    const f = this.form.getRawValue();
    if (this.cpfError() || !f.area_id || f.consent !== true) {
      this.form.markAllAsTouched();
      this.stepError.set('Confira os dados e aceite a Política para continuar.');
      return;
    }
    this.loading.set(true);
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
    this.loading.set(false);

    if (result.ok && result.data) {
      this.courierId.set(result.data.courier_id);
      this.level.set(result.data.kyc_level);
      this.initDocs(result.data.kyc_level);
      this.persistDraft();
      this.current.update((c) => c + 1);
      return;
    }
    if (result.code === COURIER_ERROR.EXISTS) {
      // E2 anti-enumeration: a single generic message (from the backend).
      this.stepError.set(
        result.message ?? 'Você já tem cadastro nessa cidade. Recupere o acesso.'
      );
      return;
    }
    this.stepError.set(result.message ?? 'Não foi possível concluir agora. Tente de novo.');
  }

  private initDocs(level: KycLevel): void {
    const items: DocItem[] = [
      {
        kind: 'selfie',
        title: 'Selfie com documento',
        purpose: 'Confirma que é você de verdade.',
        capture: 'user',
        status: 'pending_upload',
      },
    ];
    if (level === 'completa') {
      items.push(
        {
          kind: 'cnh',
          title: 'CNH com EAR',
          purpose: 'Mostra que você pode dirigir fazendo entregas.',
          capture: 'environment',
          status: 'pending_upload',
        },
        {
          kind: 'crlv',
          title: 'CRLV',
          purpose: 'Confirma que o veículo está regular.',
          capture: 'environment',
          status: 'pending_upload',
        }
      );
    }
    this.docs.set(items);
  }

  // --- document upload (presign PUT in background) --------------------------
  protected async onFile(item: DocItem, file: File): Promise<void> {
    const courierId = this.courierId();
    if (!courierId) return;
    this.setDocStatus(item.kind, 'uploading');
    const sha = await this.sha256(file);
    const presign = await this.couriers.presignDocument(courierId, {
      kind: item.kind,
      sha256_client: sha,
      content_type: 'image/jpeg',
    });
    if (!presign) {
      this.setDocStatus(item.kind, 'pending_upload');
      return;
    }
    const ok = await this.couriers.uploadToStorage(presign, file);
    if (!ok) {
      // Resilience (offline-first): keep the file, warn, retry on reconnect.
      this.offlineWarn.set('Sem conexão. Sua foto sobe sozinha quando a internet voltar.');
      this.setDocStatus(item.kind, 'pending_upload');
      return;
    }
    await this.couriers.completeDocument(courierId, presign.document_id);
    this.setDocStatus(item.kind, 'pending', presign.document_id);
  }

  private setDocStatus(
    kind: DocItem['kind'],
    status: DocStatus,
    documentId?: number
  ): void {
    this.docs.update((list) =>
      list.map((d) => (d.kind === kind ? { ...d, status, documentId } : d))
    );
  }

  private async sha256(file: Blob): Promise<string> {
    const buf = await file.arrayBuffer();
    const digest = await crypto.subtle.digest('SHA-256', buf);
    return [...new Uint8Array(digest)]
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  }

  // --- final submit (MEI optional + "Enviar para análise") ------------------
  private async submitFinal(): Promise<void> {
    const courierId = this.courierId();
    if (!courierId) return;
    const cnpj = this.form.controls.mei_cnpj.value.replace(/\D/g, '');
    if (cnpj.length === 14) {
      const pending = await this.couriers.submitMei(courierId, cnpj);
      if (pending !== null) this.meiPending.set(pending);
    }
    this.clearDraft();
    // Post-submit "em análise" surface (pending_kyc).
    void this.router.navigate(['/entregador/cadastro/em-analise'], {
      queryParams: { mei_pending: this.meiPending() ? '1' : '0' },
    });
  }

  // --- draft persistence (NEVER the password — E1) --------------------------
  private persistDraft(): void {
    const { password, ...rest } = this.form.getRawValue();
    void password;
    try {
      sessionStorage.setItem(
        DRAFT_KEY,
        JSON.stringify({
          ...rest,
          step: this.current(),
          courierId: this.courierId(),
          level: this.level(),
        })
      );
    } catch {
      /* sessionStorage may be unavailable — non-fatal */
    }
  }
  private restoreDraft(): void {
    try {
      const raw = sessionStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const draft = JSON.parse(raw) as Record<string, unknown> & {
        step?: number;
        courierId?: number;
        level?: KycLevel;
      };
      const { step, courierId, level, ...values } = draft;
      this.form.patchValue(values as never);
      if (level) this.level.set(level);
      if (typeof courierId === 'number') {
        this.courierId.set(courierId);
        this.initDocs(level ?? 'simples');
      }
      if (typeof step === 'number') {
        this.current.set(Math.min(step, this.steps().length - 1));
      }
    } catch {
      /* ignore corrupt draft */
    }
  }
  private clearDraft(): void {
    try {
      sessionStorage.removeItem(DRAFT_KEY);
    } catch {
      /* ignore */
    }
  }
}
