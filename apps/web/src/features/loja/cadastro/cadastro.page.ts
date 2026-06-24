import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faEye, faEyeSlash, faLocationCrosshairs } from '@fortawesome/free-solid-svg-icons';
import {
  ErrorStateComponent,
  LoadingSkeletonComponent,
  WarnBannerComponent,
} from '@jaxego/shared/state';
import {
  PlanCardComponent,
  WizardStepperComponent,
  type Plan,
  type WizardStep,
} from '@jaxego/shared/components';
import { SemAreaComponent } from './sem-area.component';
import {
  isCepComplete,
  isCnpjComplete,
  isCpfComplete,
  isPhoneComplete,
  maskCep,
  maskCnpj,
  maskCpf,
  maskPhone,
  phoneToE164,
} from '@jaxego/shared/util/br-format';
import { AreaOption, MERCHANT_ERROR } from './merchant.models';
import { MerchantService } from './merchant.service';

const STEPS: WizardStep[] = [
  { label: 'Identificação' },
  { label: 'Confirmação' },
  { label: 'Endereço' },
  { label: 'Plano' },
];

const DRAFT_KEY = 'jx-merchant-onboarding';

/**
 * Cadastro de loja — wizard tela 02 (UI-SPEC §2). Four steps with a stepper,
 * BR-masked fields, inline validation on blur, partial-progress persistence in
 * sessionStorage (NEVER the password — UI-SPEC §2.4), and the F-01 exception
 * states E1 (CNPJ inativo) / E2 (anti-enumeration). Consume /v1/merchants/* and
 * /v1/plans. Zero hardcoded hex; dark mode via inherited semantic vars (DEC-001).
 */
@Component({
  selector: 'jx-cadastro-loja',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    FaIconComponent,
    WizardStepperComponent,
    PlanCardComponent,
    SemAreaComponent,
    ErrorStateComponent,
    WarnBannerComponent,
    LoadingSkeletonComponent,
  ],
  templateUrl: './cadastro.page.html',
  styleUrl: './cadastro.page.scss',
})
export class CadastroLojaPage {
  private readonly fb = inject(FormBuilder);
  private readonly merchants = inject(MerchantService);
  private readonly router = inject(Router);

  protected readonly steps = STEPS;
  protected readonly current = signal(0);
  protected readonly loading = signal(false);
  protected readonly stepError = signal<string | null>(null);
  protected readonly cepWarn = signal<string | null>(null);
  protected readonly noArea = signal(false);
  protected readonly plans = signal<Plan[]>([]);
  protected readonly areas = signal<AreaOption[]>([]);
  protected readonly selectedPlan = signal<string>('free');
  protected readonly showPassword = signal(false);
  protected readonly faEye = faEye;
  protected readonly faEyeSlash = faEyeSlash;
  protected readonly iconLocation = faLocationCrosshairs;
  protected readonly gpsLoading = signal(false);
  protected readonly gpsError = signal<string | null>(null);
  protected readonly gpsFilled = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    account_type: ['cnpj' as 'cnpj' | 'cpf', Validators.required],
    document: ['', Validators.required],
    trade_name: ['', [Validators.required, Validators.maxLength(120)]],
    category: ['', Validators.required],
    phone: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(10)]],
    password_confirm: ['', Validators.required],
    area_id: [0, Validators.min(1)],
    cep: [''],
    rua: [''],
    numero: [''],
    bairro: [''],
    consent: [false, Validators.requiredTrue],
  });

  protected readonly isLastStep = computed(() => this.current() === STEPS.length - 1);

  constructor() {
    this.restoreDraft();
    void this.loadAreas();
    void this.loadPlans();
  }

  // --- masking on input -----------------------------------------------------
  protected onDocInput(value: string): void {
    const masked =
      this.form.controls.account_type.value === 'cnpj'
        ? maskCnpj(value)
        : maskCpf(value);
    this.form.controls.document.setValue(masked);
  }
  protected passwordMismatch(): boolean {
    const pw = this.form.controls.password.value;
    const confirm = this.form.controls.password_confirm.value;
    return confirm.length > 0 && pw !== confirm;
  }

  protected onPhoneInput(value: string): void {
    this.form.controls.phone.setValue(maskPhone(value));
  }
  protected onCepInput(value: string): void {
    const masked = maskCep(value);
    this.form.controls.cep.setValue(masked);
    if (isCepComplete(masked)) void this.lookupCep(masked);
  }
  protected toggleAccountType(type: 'cnpj' | 'cpf'): void {
    this.form.controls.account_type.setValue(type);
    this.form.controls.document.setValue('');
  }
  protected togglePassword(): void {
    this.showPassword.update((v) => !v);
  }
  protected onAreaChange(areaId: number): void {
    const area = this.areas().find((a) => a.id === Number(areaId));
    this.form.patchValue({
      area_id: area?.id ?? 0,
    });
    this.noArea.set(false);
  }

  // --- inline validation messages (what happened + what to do) --------------
  protected docError(): string | null {
    const v = this.form.controls.document.value;
    if (!v) return null;
    const type = this.form.controls.account_type.value;
    if (type === 'cnpj' && !isCnpjComplete(v)) return 'CNPJ incompleto. Confira os 14 dígitos.';
    if (type === 'cpf' && !isCpfComplete(v)) return 'CPF incompleto. Confira os 11 dígitos.';
    return null;
  }
  protected phoneError(): string | null {
    const v = this.form.controls.phone.value;
    if (v && !isPhoneComplete(v)) return 'Telefone precisa de DDD e 9 dígitos.';
    return null;
  }
  protected emailError(): string | null {
    const c = this.form.controls.email;
    if (c.touched && c.invalid) return 'Confira o e-mail. Algo está faltando.';
    return null;
  }
  protected passwordError(): string | null {
    const c = this.form.controls.password;
    if (c.touched && c.invalid) return 'A senha precisa de pelo menos 10 caracteres.';
    return null;
  }

  // --- step navigation ------------------------------------------------------
  protected goToStep(index: number): void {
    if (index < this.current()) {
      this.stepError.set(null);
      this.current.set(index);
    }
  }

  protected next(): void {
    this.stepError.set(null);
    if (!this.stepValid()) {
      this.form.markAllAsTouched();
      return;
    }
    this.persistDraft();
    if (this.isLastStep()) {
      void this.submit();
      return;
    }
    this.current.update((c) => c + 1);
  }

  private stepValid(): boolean {
    const f = this.form.controls;
    switch (this.current()) {
      case 0:
        return (
          !this.docError() &&
          !!f.document.value &&
          f.trade_name.valid &&
          f.category.valid
        );
      case 1:
        return !this.phoneError() && f.phone.valid && f.email.valid && f.password.valid;
      case 2:
        return !this.noArea() && f.area_id.valid;
      case 3:
        return f.consent.value === true;
      default:
        return false;
    }
  }

  // --- ViaCEP (resilient) ---------------------------------------------------
  private async lookupCep(masked: string): Promise<void> {
    this.cepWarn.set(null);
    this.loading.set(true);
    const res = await this.merchants.lookupCep(masked);
    this.loading.set(false);
    if (!res) {
      this.cepWarn.set('Não encontramos esse CEP. Preencha o endereço manualmente.');
      return;
    }
    this.form.patchValue({
      rua: res.logradouro ?? '',
      bairro: res.bairro ?? '',
    });
  }

  protected async fillFromGps(): Promise<void> {
    if (!navigator.geolocation) {
      this.gpsError.set('Seu navegador não suporta geolocalização.');
      return;
    }
    this.gpsLoading.set(true);
    this.gpsError.set(null);
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) =>
        navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 10000 })
      );
      const { latitude, longitude } = pos.coords;
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&addressdetails=1`,
        { headers: { 'Accept-Language': 'pt-BR' } }
      );
      if (!resp.ok) { this.gpsError.set('Não foi possível obter o endereço.'); return; }
      const data = await resp.json();
      const addr = data.address ?? {};
      const cep = (addr.postcode ?? '').replace(/\D/g, '');
      const masked = cep.length === 8 ? cep.replace(/^(\d{5})(\d{3})$/, '$1-$2') : '';
      this.form.patchValue({
        cep: masked,
        rua: addr.road ?? '',
        numero: addr.house_number ?? '',
        bairro: addr.suburb ?? addr.neighbourhood ?? '',
      });
      if (masked) this.form.controls.cep.setValue(masked);
      this.gpsFilled.set(true);
    } catch (err: any) {
      if (err?.code === 1) this.gpsError.set('Permissão de localização negada. Habilite nas configurações do navegador.');
      else if (err?.code === 3) this.gpsError.set('Tempo esgotado ao obter localização. Tente novamente.');
      else this.gpsError.set('Não foi possível obter sua localização.');
    } finally {
      this.gpsLoading.set(false);
    }
  }

  private async loadPlans(): Promise<void> {
    const plans = await this.merchants.listPlans();
    this.plans.set(plans);
  }

  private async loadAreas(): Promise<void> {
    const areas = await this.merchants.listAreas();
    this.areas.set(areas);
    if (areas.length === 0) {
      this.noArea.set(true);
    }
  }

  protected choosePlan(plan: Plan): void {
    this.selectedPlan.set(plan.codename);
  }

  // --- submit ---------------------------------------------------------------
  private async submit(): Promise<void> {
    if (this.loading()) return;
    if (this.form.controls.consent.value !== true) {
      this.stepError.set('Aceite os Termos e a Política de Privacidade para continuar.');
      return;
    }
    this.loading.set(true);
    const f = this.form.getRawValue();
    const result = await this.merchants.signup({
      area_id: f.area_id,
      account_type: f.account_type,
      document: f.document.replace(/[^0-9A-Za-z]/g, ''),
      trade_name: f.trade_name,
      category: f.category,
      phone_e164: phoneToE164(f.phone),
      email: f.email,
      password: f.password,
      consent: f.consent,
      address: f.rua || undefined,
      address_number: f.numero || undefined,
      address_neighborhood: f.bairro || undefined,
      plan_code: this.selectedPlan(),
    });
    this.loading.set(false);

    if (result.ok) {
      this.clearDraft();
      void this.router.navigate(['/loja/cadastro/sucesso']);
      return;
    }

    if (result.code === MERCHANT_ERROR.AREA_NOT_COVERED) {
      this.noArea.set(true);
      this.current.set(2);
      return;
    }
    // E1, E2 (anti-enumeration — message comes from the backend), and others
    // surface as a step-level alert. We never infer which field collided.
    this.stepError.set(
      result.message ?? 'Não foi possível concluir o cadastro agora. Tente de novo.'
    );
  }

  protected onInterest(email: string, cidade: string): void {
    void this.merchants.captureInterest(email, cidade);
  }

  // --- draft persistence (NEVER the password — UI-SPEC §2.4) ---------------
  private persistDraft(): void {
    const { password, password_confirm, ...rest } = this.form.getRawValue();
    void password_confirm;
    void password; // explicitly excluded
    try {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ ...rest, step: this.current() }));
    } catch {
      /* sessionStorage may be unavailable — non-fatal */
    }
  }
  private restoreDraft(): void {
    try {
      const raw = sessionStorage.getItem(DRAFT_KEY);
      if (!raw) return;
      const draft = JSON.parse(raw) as Record<string, unknown> & { step?: number };
      const { step, ...values } = draft;
      void step;
      this.form.patchValue(values as never);
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
