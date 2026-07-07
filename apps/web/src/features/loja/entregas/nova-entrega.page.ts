import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom, interval } from 'rxjs';
import { FieldComponent } from '@jaxego/shared/components/field/field.component';
import { UpgradeModalComponent } from '@jaxego/shared/components/upgrade-modal/upgrade-modal.component';
import { ErrorStateComponent } from '@jaxego/shared/state';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faBoxOpen, faCamera, faXmark } from '@fortawesome/free-solid-svg-icons';
import { CardFormComponent } from '../plano/components/jx-card-form.component';
import {
  isCepComplete,
  isPhoneComplete,
  maskCep,
  maskPhone,
  phoneToE164,
} from '@jaxego/shared/util/br-format';
import { maskBrl, parseBrl } from '@jaxego/shared/util/money';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { DeliveryService } from './delivery.service';
import { CreateDeliveryRequest } from '@jaxego/shared/models/delivery.models';

interface NeighborhoodOption {
  id: number;
  name: string;
}

interface CourierOnline {
  id: number;
  full_name: string;
  avg_stars: number;
  price_cents: number | null;
}

interface TeamOnline {
  id: number;
  name: string;
  couriers: CourierOnline[];
}

interface TeamsForAddressResponse {
  zona_id: number | null;
  zona_name: string | null;
  teams: TeamOnline[];
}

/**
 * Tela 12 — new delivery form (F-03 / UI-SPEC §2). 2-step wizard:
 * Step 1: fill all delivery data (address, recipient, items, options).
 * Step 2: select team(s) filtered to the zone resolved from the address.
 * Zone resolution geocodes the dropoff address and does point-in-polygon
 * matching — couriers with ativo=False for that zone are excluded.
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
    UpgradeModalComponent,
    ErrorStateComponent,
    CardFormComponent,
    FaIconComponent,
  ],
  templateUrl: './nova-entrega.page.html',
  styleUrl: './nova-entrega.page.scss',
})
export class NovaEntregaPage {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(DeliveryService);
  private readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  protected readonly form = this.fb.group({
    pickup_address: ['', [Validators.required, Validators.minLength(3)]],
    dropoff_address: ['', [Validators.required, Validators.minLength(3)]],
    dropoff_number: [''],
    dropoff_complement: [''],
    dropoff_reference: [''],
    cep: [''],
    dropoff_neighborhood_id: [null as number | null, [Validators.required]],
    recipient_name: ['', [Validators.required, Validators.minLength(2)]],
    recipient_phone: ['', [Validators.required]],
    items_description: ['', [Validators.required]],
    items_quantity: ['1'],
    declared_value: [''],
    weight_kg: [''],
    length_cm: [''],
    width_cm: [''],
    height_cm: [''],
    reference_number: [''],
    notes: [''],
    proof_method: ['photo'],
    payment_method: ['direct'],
    receipt_method: ['dinheiro'],
  });

  protected readonly packageSizes = [
    {
      nome: 'Pequeno',
      descricao: 'Medicamentos, cosméticos, acessórios, documentos, lanches.',
      comprimentoCm: 20, larguraCm: 15, alturaCm: 10, pesoMaximoKg: 1,
    },
    {
      nome: 'Médio',
      descricao: 'Roupas, calçados, refeições, eletrônicos compactos.',
      comprimentoCm: 30, larguraCm: 25, alturaCm: 20, pesoMaximoKg: 3,
    },
    {
      nome: 'Grande',
      descricao: 'Caixas de bebidas, brinquedos, compras de mercado pequenas.',
      comprimentoCm: 40, larguraCm: 35, alturaCm: 30, pesoMaximoKg: 8,
    },
    {
      nome: 'Extra Grande',
      descricao: 'Compras de supermercado, galões, eletroportáteis, estoque.',
      comprimentoCm: 50, larguraCm: 40, alturaCm: 40, pesoMaximoKg: 15,
    },
  ];
  protected readonly selectedPackage = signal<string>('Pequeno');

  protected selectPackage(pkg: typeof this.packageSizes[number]): void {
    this.selectedPackage.set(pkg.nome);
    this.form.patchValue({
      weight_kg: String(pkg.pesoMaximoKg),
      length_cm: String(pkg.comprimentoCm),
      width_cm: String(pkg.larguraCm),
      height_cm: String(pkg.alturaCm),
    });
  }

  protected readonly neighborhoods = signal<NeighborhoodOption[]>([]);
  protected readonly submitting = signal(false);
  protected readonly submitError = signal<string | null>(null);

  // ── Wizard state ──────────────────────────────────────────────────────────
  protected readonly step = signal<1 | 2>(1);
  protected readonly resolving = signal(false);
  protected readonly resolveError = signal<string | null>(null);
  protected readonly zonaId = signal<number | null>(null);
  protected readonly zonaNome = signal<string | null>(null);

  // Teams shown in step 2 (filtered by zone).
  protected readonly teamsOnline = signal<TeamOnline[]>([]);
  protected readonly openTeamId = signal<number | null>(null);
  protected readonly selectedTeamIds = signal<Set<number>>(new Set());

  // E1 (out of area) and E4 (plan limit) state.
  protected readonly outOfArea = signal(false);
  protected readonly showUpgrade = signal(false);
  protected readonly upgradePlanName = signal<string>('');
  protected readonly upgradePlanLimit = signal<number>(0);
  protected readonly upgradePlanUsed = signal<number>(0);

  protected readonly paymentMethod = signal<'direct' | 'pix' | 'card'>('direct');
  protected readonly iconBox = faBoxOpen;
  protected readonly iconCamera = faCamera;
  protected readonly iconXmark = faXmark;
  protected readonly imagePreview = signal<string | null>(null);
  protected readonly lightboxUrl = signal<string | null>(null);
  protected readonly submitLabel = signal('Chamar entregador');
  protected imageFile: File | null = null;
  protected readonly proofMethod = signal<string>('photo');
  protected readonly receiptMethod = signal<string>('dinheiro');
  protected readonly deliveryRefused = signal(false);
  protected readonly deliveryMode = signal<'immediate' | 'scheduled'>('immediate');
  protected readonly scheduledAt = signal<string>('');
  protected readonly scheduledAtError = signal<string | null>(null);
  private cardBlob: string | null = null;

  constructor() {
    const destroyRef = inject(DestroyRef);
    void this.loadNeighborhoods();
    // Refresh team list every minute while on step 2.
    interval(60_000).pipe(takeUntilDestroyed(destroyRef)).subscribe(() => {
      if (this.step() === 2) void this.refreshTeams();
    });
    const me = this.auth.me();
    const parts = [me?.address, me?.address_number, me?.address_neighborhood].filter(Boolean);
    const pickup = parts.length ? parts.join(', ') : me?.trade_name;
    if (pickup) {
      this.form.controls.pickup_address.setValue(pickup);
    }
    this.selectPackage(this.packageSizes[0]);
    this.form.controls.cep.valueChanges.subscribe((v) => {
      const masked = maskCep(v ?? '');
      if (masked !== v) this.form.controls.cep.setValue(masked, { emitEvent: false });
      if (isCepComplete(masked)) this.outOfArea.set(false);
    });
    this.form.controls.recipient_phone.valueChanges.subscribe((v) => {
      const masked = maskPhone(v ?? '');
      if (masked !== v) this.form.controls.recipient_phone.setValue(masked, { emitEvent: false });
    });
    this.form.controls.declared_value.valueChanges.subscribe((v) => {
      const masked = maskBrl(v ?? '');
      if (masked !== v) this.form.controls.declared_value.setValue(masked, { emitEvent: false });
    });
    this.form.controls.payment_method.valueChanges.subscribe((v) => {
      this.paymentMethod.set((v as 'direct' | 'pix' | 'card') ?? 'direct');
      this.deliveryRefused.set(false);
      if (v !== 'card') this.cardBlob = null;
    });
    this.form.controls.proof_method.valueChanges.subscribe((v) => {
      this.proofMethod.set(v ?? 'photo');
      const ref = this.form.controls.reference_number;
      if (v === 'photo_reference') {
        ref.setValidators([Validators.required]);
      } else {
        ref.clearValidators();
      }
      ref.updateValueAndValidity();
    });
    this.form.controls.receipt_method.valueChanges.subscribe((v) => {
      this.receiptMethod.set(v ?? 'dinheiro');
    });
  }

  // ── Step 1 validation ─────────────────────────────────────────────────────

  protected step1Valid(): boolean {
    const c = this.form.controls;
    if (c.pickup_address.invalid) return false;
    if (c.dropoff_address.invalid) return false;
    if (!c.dropoff_neighborhood_id.value) return false;
    if (c.recipient_name.invalid) return false;
    if (!c.recipient_phone.value || !isPhoneComplete(c.recipient_phone.value)) return false;
    if (c.items_description.invalid) return false;
    return true;
  }

  protected async advanceToStep2(): Promise<void> {
    if (!this.step1Valid()) {
      this.form.controls.pickup_address.markAsTouched();
      this.form.controls.dropoff_address.markAsTouched();
      this.form.controls.dropoff_neighborhood_id.markAsTouched();
      this.form.controls.recipient_name.markAsTouched();
      this.form.controls.recipient_phone.markAsTouched();
      this.form.controls.items_description.markAsTouched();
      return;
    }

    this.resolving.set(true);
    this.resolveError.set(null);
    this.selectedTeamIds.set(new Set());

    const v = this.form.getRawValue();
    try {
      const res = await firstValueFrom(
        this.http.post<TeamsForAddressResponse>('/v1/deliveries/teams-for-address', {
          dropoff_address: v.dropoff_address,
          dropoff_number: v.dropoff_number || null,
          dropoff_neighborhood_id: v.dropoff_neighborhood_id,
          cep: v.cep || null,
        })
      );
      this.zonaId.set(res.zona_id);
      this.zonaNome.set(res.zona_name);
      this.teamsOnline.set(res.teams);
      this.step.set(2);
    } catch {
      this.resolveError.set('Não foi possível verificar a cobertura do endereço. Tente de novo.');
    } finally {
      this.resolving.set(false);
    }
  }

  private async refreshTeams(): Promise<void> {
    const v = this.form.getRawValue();
    try {
      const res = await firstValueFrom(
        this.http.post<TeamsForAddressResponse>('/v1/deliveries/teams-for-address', {
          dropoff_address: v.dropoff_address,
          dropoff_number: v.dropoff_number || null,
          dropoff_neighborhood_id: v.dropoff_neighborhood_id,
          cep: v.cep || null,
        })
      );
      this.teamsOnline.set(res.teams);
    } catch { /* keep current list */ }
  }

  protected backToStep1(): void {
    this.step.set(1);
    this.resolveError.set(null);
  }

  // ── Teams ─────────────────────────────────────────────────────────────────

  protected toggleTeam(teamId: number | null): void {
    this.openTeamId.set(this.openTeamId() === teamId ? null : teamId);
  }

  protected toggleTeamSelection(teamId: number): void {
    const current = new Set(this.selectedTeamIds());
    if (current.has(teamId)) current.delete(teamId); else current.add(teamId);
    this.selectedTeamIds.set(current);
  }

  protected isTeamSelected(teamId: number): boolean {
    return this.selectedTeamIds().has(teamId);
  }

  protected get selectedNeighborhoodName(): string {
    const id = this.form.controls.dropoff_neighborhood_id.value;
    return this.neighborhoods().find(n => n.id === id)?.name ?? '';
  }

  // ── Image ─────────────────────────────────────────────────────────────────

  protected onDeliveryCardEncrypted(blob: string): void {
    this.cardBlob = blob;
    void this.submit();
  }

  protected retryPayment(): void { this.deliveryRefused.set(false); }

  protected switchToDirect(): void {
    this.deliveryRefused.set(false);
    this.cardBlob = null;
    this.form.controls.payment_method.setValue('direct');
  }

  protected onImageSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.imageFile = file;
    this.imagePreview.set(URL.createObjectURL(file));
  }

  protected removeImage(): void {
    if (this.imagePreview()) URL.revokeObjectURL(this.imagePreview()!);
    this.imageFile = null;
    this.imagePreview.set(null);
  }

  private async uploadImage(deliveryId: number): Promise<void> {
    if (!this.imageFile) return;
    try {
      const presign = await firstValueFrom(
        this.http.post<{ presigned_url: string; method: string; headers: Record<string, string> }>(
          `/v1/deliveries/${deliveryId}/image/presign`,
          { content_type: this.imageFile.type || 'image/jpeg' }
        )
      );
      await fetch(presign.presigned_url, { method: presign.method, headers: presign.headers, body: this.imageFile });
    } catch { /* non-blocking */ }
  }

  // ── Neighborhoods ─────────────────────────────────────────────────────────

  private async loadNeighborhoods(): Promise<void> {
    try {
      const res = await firstValueFrom(this.http.get<NeighborhoodOption[]>('/v1/neighborhoods/catalog'));
      this.neighborhoods.set(res as NeighborhoodOption[]);
    } catch {
      this.neighborhoods.set([]);
    }
  }

  // ── Validation helpers ────────────────────────────────────────────────────

  protected phoneError(): string | null {
    const c = this.form.controls.recipient_phone;
    if (c.touched && c.value && !isPhoneComplete(c.value)) {
      return 'Telefone incompleto. Use (DD) 9XXXX-XXXX.';
    }
    return null;
  }

  protected get scheduledAtMin(): string {
    const d = new Date(Date.now() + 1 * 60 * 1000);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  protected setDeliveryMode(mode: 'immediate' | 'scheduled'): void {
    this.deliveryMode.set(mode);
    this.scheduledAtError.set(null);
    if (mode === 'immediate') this.scheduledAt.set('');
    this.submitLabel.set(mode === 'scheduled' ? 'Agendar entrega' : 'Chamar entregador');
  }

  protected canSubmit(): boolean {
    if (this.step() !== 2) return false;
    if (!this.form.valid || this.outOfArea() || this.submitting() || this.selectedTeamIds().size === 0) return false;
    if (this.deliveryMode() === 'scheduled' && !this.scheduledAt()) return false;
    return true;
  }

  // ── Submit ────────────────────────────────────────────────────────────────

  protected async submit(): Promise<void> {
    if (!this.canSubmit()) {
      this.form.markAllAsTouched();
      return;
    }
    if (this.deliveryMode() === 'scheduled') {
      const picked = this.scheduledAt();
      if (!picked) { this.scheduledAtError.set('Selecione a data e o horário de agendamento.'); return; }
      if (new Date(picked).getTime() < Date.now() + 60_000) {
        this.scheduledAtError.set('O horário deve ser pelo menos 1 minuto no futuro.'); return;
      }
      this.scheduledAtError.set(null);
    }

    this.submitting.set(true);
    this.submitLabel.set('Salvando os dados...');
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
      dropoff_complement: v.dropoff_complement || null,
      dropoff_reference: v.dropoff_reference || null,
      cep: v.cep || null,
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
      team_ids: [...this.selectedTeamIds()],
      proof_method: this.proofMethod() as 'none' | 'photo' | 'photo_reference' | 'otp',
      payment_method: 'direct',
      receipt_method: this.receiptMethod(),
      scheduled_at: this.deliveryMode() === 'scheduled' && this.scheduledAt()
        ? new Date(this.scheduledAt()).toISOString()
        : null,
    };

    const result = await this.service.create(req);

    if (result.ok) {
      if (this.imageFile) {
        this.submitLabel.set('Enviando imagem...');
        await this.uploadImage(result.data.delivery_id);
      }
      this.submitting.set(false);
      this.submitLabel.set(this.deliveryMode() === 'scheduled' ? 'Agendar entrega' : 'Chamar entregador');
      void this.router.navigate(['/loja/entregas', result.data.delivery_id]);
      return;
    }
    this.submitting.set(false);
    this.submitLabel.set(this.deliveryMode() === 'scheduled' ? 'Agendar entrega' : 'Chamar entregador');

    if (result.planLimit) { this.openUpgrade(result); return; }
    if (result.code === 'dropoff_out_of_area') { this.outOfArea.set(true); return; }
    this.submitError.set(result.message ?? 'Não foi possível criar a entrega. Tente de novo.');
  }

  private openUpgrade(result: { planName?: string; planLimitCount?: number; planUsed?: number }): void {
    this.upgradePlanName.set(result.planName ?? '');
    this.upgradePlanLimit.set(result.planLimitCount ?? 0);
    this.upgradePlanUsed.set(result.planUsed ?? 0);
    this.showUpgrade.set(true);
  }

  protected onUpgradeDismiss(): void { this.showUpgrade.set(false); }
}
