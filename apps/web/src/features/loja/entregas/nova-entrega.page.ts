import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import {
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { FieldComponent } from '@jaxego/shared/components/field/field.component';
import { EstimateBoxComponent } from '@jaxego/shared/components/estimate-box/estimate-box.component';
import { UpgradeModalComponent } from '@jaxego/shared/components/upgrade-modal/upgrade-modal.component';
import { ErrorStateComponent, WarnBannerComponent } from '@jaxego/shared/state';
import { CardFormComponent } from '../plano/components/jx-card-form.component';
import { Plan } from '@jaxego/shared/components/plan-card/plan-card.component';
import {
  isCepComplete,
  isPhoneComplete,
  maskCep,
  maskPhone,
  phoneToE164,
} from '@jaxego/shared/util/br-format';
import { maskBrl, parseBrl } from '@jaxego/shared/util/money';
import { DeliveryService } from './delivery.service';
import { CreateDeliveryRequest } from '@jaxego/shared/models/delivery.models';

interface NeighborhoodOption {
  id: number;
  name: string;
}

/**
 * Tela 12 — new delivery form (F-03 / UI-SPEC §2). Reactive form, sections by
 * fieldset, BR masks (phone→E.164, CEP, BRL), inline validation, estimate before
 * confirm (RN-030), E1 (out of area, blocks), E2 (0 couriers, non-blocking),
 * E4 (plan limit → upgrade modal). Only `direct` payment is enabled; card/PIX and
 * the OTP proof are selectable-disabled "em breve". Tokens only — no hex.
 */
@Component({
  selector: 'jx-nova-entrega',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    RouterLink,
    FieldComponent,
    EstimateBoxComponent,
    UpgradeModalComponent,
    ErrorStateComponent,
    WarnBannerComponent,
    CardFormComponent,
  ],
  templateUrl: './nova-entrega.page.html',
  styleUrl: './nova-entrega.page.scss',
})
export class NovaEntregaPage {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(DeliveryService);
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  protected readonly form = this.fb.group({
    pickup_address: ['', [Validators.required, Validators.minLength(3)]],
    dropoff_address: ['', [Validators.required, Validators.minLength(3)]],
    dropoff_number: [''],
    cep: [''],
    dropoff_neighborhood_id: [null as number | null, [Validators.required]],
    recipient_name: ['', [Validators.required, Validators.minLength(2)]],
    recipient_phone: ['', [Validators.required]],
    items_description: ['', [Validators.required]],
    items_quantity: ['1'],
    declared_value: [''],
    // Pacote (MG-1): peso em kg + dimensões em cm (opcionais).
    weight_kg: [''],
    length_cm: [''],
    width_cm: [''],
    height_cm: [''],
    reference_number: [''],
    notes: [''],
    proof_method: ['photo'],
    payment_method: ['direct'],
  });

  protected readonly neighborhoods = signal<NeighborhoodOption[]>([]);
  protected readonly submitting = signal(false);
  protected readonly submitError = signal<string | null>(null);

  // Estimate / exceptions surfaced after create or pre-check.
  protected readonly estimating = signal(false);
  protected readonly estimateMin = signal<number | null>(null);
  protected readonly estimateMax = signal<number | null>(null);
  protected readonly courierCount = signal(0);
  protected readonly noCouriersWarning = signal(false); // E2

  // E1 (out of area) and E4 (plan limit) state.
  protected readonly outOfArea = signal(false);
  protected readonly showUpgrade = signal(false);
  protected readonly upgradePlans = signal<Plan[]>([]);

  // Phase 10 — online payment (card/pix). F-03 E3: a refusal does NOT create the
  // delivery; the store gets retry or switch-to-direct (no form data lost).
  protected readonly paymentMethod = signal<'direct' | 'pix' | 'card'>('direct');
  protected readonly deliveryRefused = signal(false);
  private cardBlob: string | null = null;

  constructor() {
    void this.loadNeighborhoods();
    // Apply BR masks reactively (no raw type="number"; mask on every keystroke).
    this.form.controls.cep.valueChanges.subscribe((v) => {
      const masked = maskCep(v ?? '');
      if (masked !== v) {
        this.form.controls.cep.setValue(masked, { emitEvent: false });
      }
      if (isCepComplete(masked)) {
        this.outOfArea.set(false);
      }
    });
    this.form.controls.recipient_phone.valueChanges.subscribe((v) => {
      const masked = maskPhone(v ?? '');
      if (masked !== v) {
        this.form.controls.recipient_phone.setValue(masked, { emitEvent: false });
      }
    });
    this.form.controls.declared_value.valueChanges.subscribe((v) => {
      const masked = maskBrl(v ?? '');
      if (masked !== v) {
        this.form.controls.declared_value.setValue(masked, { emitEvent: false });
      }
    });
    this.form.controls.payment_method.valueChanges.subscribe((v) => {
      this.paymentMethod.set((v as 'direct' | 'pix' | 'card') ?? 'direct');
      this.deliveryRefused.set(false);
      if (v !== 'card') this.cardBlob = null;
    });
  }

  /** The card is RSA-encrypted by jx-card-form; only the opaque blob arrives here. */
  protected onDeliveryCardEncrypted(blob: string): void {
    this.cardBlob = blob;
    void this.submit();
  }

  protected retryPayment(): void {
    this.deliveryRefused.set(false);
  }

  /** F-03 E3 exit: switch to direct WITHOUT losing the filled form. */
  protected switchToDirect(): void {
    this.deliveryRefused.set(false);
    this.cardBlob = null;
    this.form.controls.payment_method.setValue('direct');
  }

  private async loadNeighborhoods(): Promise<void> {
    // Best-effort catalog read; on failure the store types nothing and the
    // backend enforces E1 on submit (graceful degradation).
    try {
      const res = await firstValueFrom(
        this.http.get<NeighborhoodOption[]>('/v1/neighborhoods/catalog'),
      );
      this.neighborhoods.set(res as NeighborhoodOption[]);
    } catch {
      this.neighborhoods.set([]);
    }
  }

  protected phoneError(): string | null {
    const c = this.form.controls.recipient_phone;
    if (c.touched && c.value && !isPhoneComplete(c.value)) {
      return 'Telefone incompleto. Use (DD) 9XXXX-XXXX.';
    }
    return null;
  }

  protected canSubmit(): boolean {
    return this.form.valid && !this.outOfArea() && !this.submitting();
  }

  protected async submit(): Promise<void> {
    if (!this.canSubmit()) {
      this.form.markAllAsTouched();
      return;
    }
    const method = this.paymentMethod();
    // Card requires the encrypted blob first — the form's submit triggers
    // onDeliveryCardEncrypted, which re-enters submit() with the blob set.
    if (method === 'card' && !this.cardBlob) {
      return;
    }

    this.submitting.set(true);
    this.submitError.set(null);
    this.deliveryRefused.set(false);

    const v = this.form.getRawValue();
    const declared = v.declared_value ? Math.round(parseBrl(v.declared_value) * 100) : null;
    const toInt = (s: string | null | undefined): number | null => {
      const n = s ? parseInt(s.replace(',', '.'), 10) : NaN;
      return Number.isFinite(n) && n > 0 ? n : null;
    };
    const weightKg = v.weight_kg ? parseFloat(v.weight_kg.replace(',', '.')) : NaN;
    const req: CreateDeliveryRequest = {
      pickup_address: v.pickup_address!,
      dropoff_neighborhood_id: v.dropoff_neighborhood_id!,
      dropoff_address: v.dropoff_address!,
      dropoff_number: v.dropoff_number || null,
      recipient_name: v.recipient_name!,
      recipient_phone_e164: phoneToE164(v.recipient_phone!),
      items_description: v.items_description || null,
      items_quantity: Math.max(parseInt(v.items_quantity || '1', 10) || 1, 1),
      declared_value_cents: declared,
      weight_g: Number.isFinite(weightKg) && weightKg > 0 ? Math.round(weightKg * 1000) : null,
      length_cm: toInt(v.length_cm),
      width_cm: toInt(v.width_cm),
      height_cm: toInt(v.height_cm),
      reference_number: v.reference_number || null,
      notes: v.notes || null,
      proof_method: 'photo',
      payment_method: method,
      card_blob: method === 'card' ? this.cardBlob : null,
    };

    const result = await this.service.create(req);
    this.submitting.set(false);

    if (result.ok) {
      this.estimateMin.set(result.data.estimate_min_cents);
      this.estimateMax.set(result.data.estimate_max_cents);
      this.noCouriersWarning.set(result.data.no_couriers_warning);
      // Born CRIADA → go to the detail, which shows "procurando entregador" and
      // polls until a courier accepts (F4.1 / tpl-m-searching).
      void this.router.navigate(['/loja/entregas', result.data.delivery_id]);
      return;
    }

    if (result.planLimit) {
      await this.openUpgrade();
      return;
    }
    if (result.code === 'dropoff_out_of_area') {
      this.outOfArea.set(true);
      return;
    }
    // F-03 E3: card/pix refused/gateway error → the delivery was NOT created. Offer
    // retry or switch-to-direct without losing the filled form. The blob is single-use.
    if (method !== 'direct' && result.code === 'payment_gateway_error') {
      this.cardBlob = null;
      this.deliveryRefused.set(true);
      return;
    }
    this.submitError.set(
      result.message ?? 'Não foi possível criar a entrega. Tente de novo.',
    );
  }

  private async openUpgrade(): Promise<void> {
    try {
      const plans = await firstValueFrom(this.http.get<Plan[]>('/v1/plans'));
      this.upgradePlans.set(plans);
    } catch {
      this.upgradePlans.set([]);
    }
    this.showUpgrade.set(true);
  }

  protected onUpgradeDismiss(): void {
    // Lossless: the form keeps what was filled (E4, anti-dark-pattern).
    this.showUpgrade.set(false);
  }

  protected onChoosePlan(): void {
    void this.router.navigate(['/loja/plano']);
  }
}
