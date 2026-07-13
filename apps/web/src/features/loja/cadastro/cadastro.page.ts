import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
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
  CycleToggleComponent,
  PlanCardComponent,
  WizardStepperComponent,
  type BillingCycle,
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
import { AuthService } from '@jaxego/core/auth/auth.service';
import { environment } from '../../../environments/environment';

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
    CycleToggleComponent,
    PlanCardComponent,
    SemAreaComponent,
    ErrorStateComponent,
    WarnBannerComponent,
    LoadingSkeletonComponent,
  ],
  templateUrl: './cadastro.page.html',
  styleUrl: './cadastro.page.scss',
})
export class CadastroLojaPage implements OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly merchants = inject(MerchantService);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  protected readonly steps = STEPS;
  protected readonly current = signal(0);
  protected readonly loading = signal(false);
  protected readonly stepError = signal<string | null>(null);
  protected readonly cepWarn = signal<string | null>(null);
  protected readonly noArea = signal(false);
  protected readonly plans = signal<Plan[]>([]);
  protected readonly areas = signal<AreaOption[]>([]);
  protected readonly selectedPlan = signal<string>('free');
  protected readonly cycle = signal<BillingCycle>('mensal');
  protected readonly showPassword = signal(false);
  protected readonly faEye = faEye;
  protected readonly faEyeSlash = faEyeSlash;
  protected readonly iconLocation = faLocationCrosshairs;
  protected readonly gpsLoading = signal(false);
  protected readonly gpsError = signal<string | null>(null);
  protected readonly gpsFilled = signal(false);
  private gpsLat: number | null = null;
  private gpsLng: number | null = null;

  // Payment step state (shown after signup with paid plan)
  protected readonly showPayment = signal(false);
  protected readonly payMethod = signal<'card' | 'pix' | null>(null);
  protected readonly cardHolder = signal('');
  protected readonly cardNumber = signal('');
  protected readonly cardExpiry = signal('');
  protected readonly cardCvv = signal('');
  protected readonly pixQrCode = signal<string | null>(null);
  protected readonly pixQrB64 = signal<string | null>(null);
  protected readonly paymentError = signal<string | null>(null);
  protected readonly paymentErrorCode = signal<string | null>(null);
  protected readonly paymentLoading = signal(false);
  protected readonly pixPending = signal(false);
  private pixPollTimer: ReturnType<typeof setInterval> | null = null;

  private static readonly S2P_MESSAGES: Record<string, string> = {
    '001': 'Transação recusada pelo emissor. Entre em contato com seu banco.',
    '051': 'Saldo insuficiente ou limite excedido.',
    '054': 'Cartão vencido. Verifique a data de validade.',
    '055': 'CVV inválido. Confira o código de segurança.',
    '057': 'Transação não permitida para este cartão.',
    '061': 'Valor acima do limite do cartão.',
    '065': 'Limite de transações atingido. Tente mais tarde.',
    '091': 'Banco emissor indisponível. Tente em instantes.',
    '092': 'Comunicação com o emissor falhou. Tente novamente.',
    '096': 'Falha no sistema de pagamento. Tente novamente.',
    '116': 'Dados do cartão inválidos. Confira número, validade e CVV.',
  };

  private s2pFriendly(code: string | undefined, fallback: string): string {
    if (!code) return fallback;
    return CadastroLojaPage.S2P_MESSAGES[code] ?? fallback;
  }

  private rsaPublicKey: string | null = null;
  private pendingPlanId: number | null = null;
  private pendingDocument: string | null = null;
  private pendingEmail: string | null = null;

  protected readonly form = this.fb.nonNullable.group({
    account_type: ['cpf' as 'cnpj' | 'cpf', Validators.required],
    document: ['', Validators.required],
    trade_name: ['', [Validators.required, Validators.maxLength(120)]],
    category: ['', Validators.required],
    phone: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    password_confirm: ['', Validators.required],
    area_id: [0, Validators.min(1)],
    cep: [''],
    rua: [''],
    numero: [''],
    bairro: [''],
    uf: [''],
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
    const digits = value.replace(/\D/g, '');
    const type = digits.length > 11 ? 'cnpj' : 'cpf';
    if (this.form.controls.account_type.value !== type) {
      this.form.controls.account_type.setValue(type);
    }
    this.form.controls.document.setValue(type === 'cnpj' ? maskCnpj(value) : maskCpf(value));
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

  protected onUfInput(value: string): void {
    this.form.controls.uf.setValue(value.toUpperCase().slice(0, 2));
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
    if (c.touched && c.invalid) return 'A senha precisa de pelo menos 6 caracteres.';
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
      if (this.current() === 2) {
        this.stepError.set(this.addressMissingMessage());
      }
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
        return (
          !this.noArea() &&
          f.area_id.valid &&
          !!f.cep.value &&
          !!f.rua.value &&
          !!f.numero.value &&
          !!f.bairro.value
        );
      case 3:
        return f.consent.value === true;
      default:
        return false;
    }
  }

  private addressMissingMessage(): string {
    const f = this.form.controls;
    const missing: string[] = [];
    if (!f.area_id.value || f.area_id.value === 0) missing.push('Cidade/Área');
    if (!f.cep.value) missing.push('CEP');
    if (!f.rua.value) missing.push('Rua');
    if (!f.numero.value) missing.push('Número');
    if (!f.bairro.value) missing.push('Bairro');
    return missing.length
      ? `Preencha os campos obrigatórios: ${missing.join(', ')}.`
      : 'Verifique os campos do endereço.';
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
    // Só sobrescreve campos com dados reais — CEPs "abertos" no BR não têm
    // logradouro/bairro no ViaCEP e não devem apagar o que o Mapbox preencheu.
    if (res.logradouro) this.form.controls.rua.setValue(res.logradouro);
    if (res.bairro) this.form.controls.bairro.setValue(res.bairro);
    if (res.uf) this.form.controls.uf.setValue(res.uf);
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
      this.gpsLat = latitude;
      this.gpsLng = longitude;

      // Mapbox Geocoding API — sem types=address para cair em neighborhood/place
      // quando não houver endereço exato (comum no Brasil)
      const url =
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${longitude},${latitude}.json` +
        `?access_token=${environment.mapboxToken}&language=pt-BR&country=BR`;
      const resp = await fetch(url);
      if (!resp.ok) { this.gpsError.set('Não foi possível obter o endereço.'); return; }
      const data = await resp.json();

      const feature = data.features?.[0];
      if (!feature) { this.gpsError.set('Endereço não encontrado para essa localização.'); return; }

      // feature.text = rua (quando type=address); context carrega bairro e CEP
      const context: Array<{ id: string; text: string; short_code?: string }> = feature.context ?? [];
      const postcode = context.find((c) => c.id.startsWith('postcode'))?.text ?? '';
      const neighborhood =
        context.find((c) => c.id.startsWith('neighborhood'))?.text ??
        context.find((c) => c.id.startsWith('locality'))?.text ??
        context.find((c) => c.id.startsWith('district'))?.text ?? '';
      const cityFromGps =
        context.find((c) => c.id.startsWith('place'))?.text ?? '';
      const stateFromGps =
        context.find((c) => c.id.startsWith('region'))?.short_code?.replace('BR-', '') ?? '';

      const cep = postcode.replace(/\D/g, '');
      const masked = cep.length === 8 ? cep.replace(/^(\d{5})(\d{3})$/, '$1-$2') : '';

      this.form.patchValue({
        cep: masked,
        rua: feature.text ?? '',
        numero: feature.address ?? '',
        bairro: neighborhood,
        uf: stateFromGps,
      });

      // Tenta selecionar automaticamente a área que bate com a cidade do GPS
      if (cityFromGps) this.tryMatchArea(cityFromGps);

      // ViaCEP é autoritativo para logradouro/bairro no BR — mas só sobrescreve
      // se trouxer dados (CEPs "abertos" não têm logradouro e não devem apagar
      // o que o Mapbox já preencheu)
      if (isCepComplete(masked)) void this.lookupCep(masked);
      this.gpsFilled.set(true);
    } catch (err: any) {
      if (err?.code === 1) this.gpsError.set('Permissão de localização negada. Habilite nas configurações do navegador.');
      else if (err?.code === 3) this.gpsError.set('Tempo esgotado ao obter localização. Tente novamente.');
      else this.gpsError.set('Não foi possível obter sua localização.');
    } finally {
      this.gpsLoading.set(false);
    }
  }

  private tryMatchArea(cityName: string): void {
    // eslint-disable-next-line no-misleading-character-class
    const diacritics = new RegExp('[\\u0300-\\u036f]', 'g');
    const normalize = (s: string) =>
      s.toLowerCase().normalize('NFD').replace(diacritics, '').trim();
    const city = normalize(cityName);
    const match = this.areas().find((a) => {
      const areaName = normalize(a.name);
      return areaName.includes(city) || city.includes(areaName);
    });
    if (match) {
      this.form.controls.area_id.setValue(match.id);
      this.noArea.set(false);
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
    this.pendingPlanId = plan.id;
  }

  // --- submit ---------------------------------------------------------------
  private async submit(): Promise<void> {
    if (this.loading()) return;
    if (this.form.controls.consent.value !== true) {
      this.form.controls.consent.markAsTouched();
      this.stepError.set('Aceite os Termos e a Política de Privacidade para continuar.');
      return;
    }
    this.loading.set(true);
    const f = this.form.getRawValue();
    const cleanDoc = f.document.replace(/[^0-9A-Za-z]/g, '');
    const result = await this.merchants.signup({
      area_id: f.area_id,
      account_type: f.account_type,
      document: cleanDoc,
      trade_name: f.trade_name,
      category: f.category,
      phone_e164: phoneToE164(f.phone),
      email: f.email,
      password: f.password,
      consent: f.consent,
      address: f.rua || undefined,
      address_number: f.numero || undefined,
      address_neighborhood: f.bairro || undefined,
      address_zip: f.cep ? f.cep.replace(/\D/g, '') : undefined,
      address_state: f.uf || undefined,
      plan_code: this.selectedPlan(),
      lat: this.gpsLat ?? undefined,
      lng: this.gpsLng ?? undefined,
    });
    this.loading.set(false);

    if (result.ok) {
      this.clearDraft();
      if (result.data?.status === 'pending_payment') {
        // Auto-login so the payment endpoint can authenticate the request.
        await this.auth.login({ email: f.email, password: f.password }, 'loja');
        const key = await this.merchants.getPublicKey();
        this.rsaPublicKey = key;
        this.pendingDocument = cleanDoc;
        this.pendingEmail = f.email;
        this.showPayment.set(true);
        return;
      }
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

  // --- payment step ---------------------------------------------------------
  protected goToLoja(): void {
    void this.router.navigate(['/loja']);
  }

  protected copyPixCode(): void {
    const code = this.pixQrCode();
    if (code) void navigator.clipboard.writeText(code);
  }

  ngOnDestroy(): void {
    this.stopPixPolling();
  }

  private startPixPolling(): void {
    this.pixPollTimer = setInterval(() => {
      void this.checkPixStatus();
    }, 5000);
  }

  private stopPixPolling(): void {
    if (this.pixPollTimer !== null) {
      clearInterval(this.pixPollTimer);
      this.pixPollTimer = null;
    }
  }

  private async checkPixStatus(): Promise<void> {
    const sub = await this.merchants.getSubscription();
    if (sub?.billing_status === 'active') {
      this.stopPixPolling();
      void this.router.navigate(['/loja/cadastro/sucesso']);
    }
  }

  protected setPayMethod(m: 'card' | 'pix'): void {
    this.payMethod.set(m);
    this.paymentError.set(null);
    this.paymentErrorCode.set(null);
    this.pixQrCode.set(null);
    this.pixQrB64.set(null);
    this.pixPending.set(false);
  }

  protected onCardNumberInput(v: string): void {
    const digits = v.replace(/\D/g, '').slice(0, 16);
    this.cardNumber.set(digits.replace(/(.{4})/g, '$1 ').trim());
  }

  protected onCardExpiryInput(v: string): void {
    const digits = v.replace(/\D/g, '').slice(0, 4);
    this.cardExpiry.set(digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits);
  }

  protected async submitPayment(): Promise<void> {
    if (this.paymentLoading()) return;
    this.paymentError.set(null);
    this.paymentErrorCode.set(null);
    this.paymentLoading.set(true);
    try {
      const method = this.payMethod();
      const planId = this.pendingPlanId!;
      const doc = this.pendingDocument!;
      const email = this.pendingEmail!;

      if (method === 'card') {
        const holder = this.cardHolder().trim();
        const number = this.cardNumber().replace(/\s/g, '');
        const expiry = this.cardExpiry().trim();
        const cvv = this.cardCvv().trim();
        if (!holder || number.length < 13 || expiry.length < 5 || cvv.length < 3) {
          this.paymentError.set('Preencha todos os dados do cartão corretamente.');
          return;
        }
        if (!this.rsaPublicKey) {
          this.paymentError.set('Chave de segurança indisponível. Recarregue e tente de novo.');
          return;
        }
        const cardBlob = await this.encryptCard({
          nomeTitular: holder,
          numeroCartao: number,
          validade: expiry,
          cvv,
        });
        const res = await this.merchants.subscribe({
          plan_id: planId,
          cycle: this.cycle(),
          method: 'card',
          card_blob: cardBlob,
        });
        if (res.ok) {
          void this.router.navigate(['/loja/cadastro/sucesso']);
          return;
        }
        this.paymentErrorCode.set(res.code ?? null);
        this.paymentError.set(
          this.s2pFriendly(res.code, res.message ?? 'Erro ao processar o cartão. Verifique os dados.')
        );
      } else {
        const res = await this.merchants.subscribe({
          plan_id: planId,
          cycle: this.cycle(),
          method: 'pix',
          pix_recorrente: true,
        });
        if (res.ok && res.data) {
          void this.router.navigate(['/loja/aguardando-pagamento']);
          return;
        }
        this.paymentErrorCode.set(res.code ?? null);
        this.paymentError.set(
          this.s2pFriendly(res.code, res.message ?? 'Erro ao gerar o PIX. Tente de novo.')
        );
      }
    } finally {
      this.paymentLoading.set(false);
    }
  }

  private async encryptCard(cardData: object): Promise<string> {
    const pem = this.rsaPublicKey!
      .replace(/-----BEGIN PUBLIC KEY-----/, '')
      .replace(/-----END PUBLIC KEY-----/, '')
      .replace(/\s/g, '');
    const der = Uint8Array.from(atob(pem), (c) => c.charCodeAt(0));
    const key = await crypto.subtle.importKey(
      'spki',
      der,
      { name: 'RSA-OAEP', hash: 'SHA-256' },
      false,
      ['encrypt']
    );
    const encoded = new TextEncoder().encode(JSON.stringify(cardData));
    const cipher = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, key, encoded);
    return btoa(String.fromCharCode(...new Uint8Array(cipher)));
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
