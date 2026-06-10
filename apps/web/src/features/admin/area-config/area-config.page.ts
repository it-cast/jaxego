import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ErrorStateComponent } from '../../../shared/state/error-state.component';
import { maskBrl, parseBrl, formatBrl } from '../../../shared/util/money';
import {
  AdminAreaConfigService,
  AreaConfig,
} from './area-config.service';

interface SensitiveDiffRow {
  label: string;
  before: string;
  after: string;
}

/**
 * Tela 21A — Configurações da área (UI-SPEC §2 / wireframe 21A, REQ-002).
 *
 * Four fieldsets (validação / preços+geofence / despacho), money inputs with the
 * pt-BR `R$ 0,00` mask (NEVER raw type=number), ranges validated on blur with an
 * actionable error, and a SENSITIVE-change confirmation (before→after) before the
 * audited PATCH. Save states: salvando (aria-busy) → sucesso (role=status) /
 * erro (role=alert + retry). Only semantic vars; AA light+dark (DEC-001).
 */
@Component({
  selector: 'jx-area-config-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, ErrorStateComponent],
  templateUrl: './area-config.page.html',
  styleUrl: './area-config.page.scss',
})
export class AreaConfigPage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly service = inject(AdminAreaConfigService);

  // The area id comes from the admin's session/scope; the route is /admin/config.
  // For M1 the area id is resolved by the token scope; a single-area admin has one.
  protected areaId = 1;
  protected readonly areaName = signal('');

  protected readonly saving = signal(false);
  protected readonly saved = signal(false);
  protected readonly saveError = signal<string | null>(null);
  protected readonly confirming = signal(false);
  protected readonly sensitiveDiff = signal<SensitiveDiffRow[]>([]);

  private loaded: AreaConfig | null = null;

  protected readonly form = this.fb.nonNullable.group({
    kyc_level: this.fb.nonNullable.control<'simples' | 'completa'>('simples'),
    piso_entrega: this.fb.nonNullable.control('', [Validators.required]),
    piso_km: this.fb.nonNullable.control('', [Validators.required]),
    geofence_m: this.fb.nonNullable.control(80, [
      Validators.required,
      Validators.min(30),
      Validators.max(300),
    ]),
    timeout_oferta_s: this.fb.nonNullable.control(20, [
      Validators.required,
      Validators.min(10),
      Validators.max(60),
    ]),
    timeout_favoritos_s: this.fb.nonNullable.control(60, [
      Validators.required,
      Validators.min(30),
      Validators.max(180),
    ]),
    politica_retorno_pct: this.fb.nonNullable.control(0, [
      Validators.required,
      Validators.min(0),
      Validators.max(100),
    ]),
  });

  async ngOnInit(): Promise<void> {
    try {
      const area = await this.service.get(this.areaId);
      this.areaName.set(area.name);
      const cfg = area.config as AreaConfig;
      this.loaded = this.normalise(cfg);
      this.form.patchValue({
        kyc_level: this.loaded.kyc_level,
        piso_entrega: formatBrl(parseFloat(this.loaded.piso_entrega || '0')),
        piso_km: formatBrl(parseFloat(this.loaded.piso_km || '0')),
        geofence_m: this.loaded.geofence_m,
        timeout_oferta_s: this.loaded.timeout_oferta_s,
        timeout_favoritos_s: this.loaded.timeout_favoritos_s,
        politica_retorno_pct: this.loaded.politica_retorno_pct,
      });
    } catch {
      this.saveError.set('Não conseguimos carregar a configuração. Tente de novo.');
    }
  }

  private normalise(cfg: Partial<AreaConfig>): AreaConfig {
    return {
      kyc_level: cfg.kyc_level ?? 'simples',
      piso_entrega: cfg.piso_entrega ?? '0',
      piso_km: cfg.piso_km ?? '0',
      geofence_m: cfg.geofence_m ?? 80,
      timeout_oferta_s: cfg.timeout_oferta_s ?? 20,
      timeout_favoritos_s: cfg.timeout_favoritos_s ?? 60,
      politica_retorno_pct: cfg.politica_retorno_pct ?? 0,
    };
  }

  /** Apply the pt-BR money mask as the user types (piso fields). */
  protected onMoneyInput(controlName: 'piso_entrega' | 'piso_km', event: Event): void {
    const masked = maskBrl((event.target as HTMLInputElement).value);
    this.form.controls[controlName].setValue(masked);
  }

  protected rangeError(
    controlName: 'geofence_m' | 'timeout_oferta_s' | 'timeout_favoritos_s' | 'politica_retorno_pct'
  ): string | null {
    const ctrl = this.form.controls[controlName];
    if (!ctrl.touched || ctrl.valid) {
      return null;
    }
    switch (controlName) {
      case 'geofence_m':
        return 'O raio precisa estar entre 30 e 300 metros.';
      case 'timeout_oferta_s':
        return 'O tempo de oferta precisa estar entre 10 e 60 segundos.';
      case 'timeout_favoritos_s':
        return 'A janela de favoritos precisa estar entre 30 e 180 segundos.';
      case 'politica_retorno_pct':
        return 'O retorno precisa estar entre 0 e 100%.';
    }
  }

  private buildConfig(): AreaConfig {
    const v = this.form.getRawValue();
    return {
      kyc_level: v.kyc_level,
      piso_entrega: parseBrl(v.piso_entrega).toFixed(2),
      piso_km: parseBrl(v.piso_km).toFixed(2),
      geofence_m: Number(v.geofence_m),
      timeout_oferta_s: Number(v.timeout_oferta_s),
      timeout_favoritos_s: Number(v.timeout_favoritos_s),
      politica_retorno_pct: Number(v.politica_retorno_pct),
    };
  }

  private computeDiff(next: AreaConfig): SensitiveDiffRow[] {
    if (!this.loaded) {
      return [];
    }
    const labels: Record<keyof AreaConfig, string> = {
      kyc_level: 'Nível de validação',
      piso_entrega: 'Piso por entrega',
      piso_km: 'Piso por km',
      geofence_m: 'Raio de geofence',
      timeout_oferta_s: 'Tempo de oferta',
      timeout_favoritos_s: 'Janela de favoritos',
      politica_retorno_pct: 'Política de retorno',
    };
    const rows: SensitiveDiffRow[] = [];
    (Object.keys(labels) as (keyof AreaConfig)[]).forEach((key) => {
      const before = String(this.loaded![key]);
      const after = String(next[key]);
      if (before !== after) {
        rows.push({ label: labels[key], before, after });
      }
    });
    return rows;
  }

  /** Open the sensitive-change confirmation before saving (saas-dashboard). */
  protected requestSave(): void {
    this.saved.set(false);
    this.saveError.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const next = this.buildConfig();
    this.sensitiveDiff.set(this.computeDiff(next));
    this.confirming.set(true);
  }

  protected cancelConfirm(): void {
    this.confirming.set(false);
  }

  async confirmSave(): Promise<void> {
    this.confirming.set(false);
    this.saving.set(true);
    this.saveError.set(null);
    try {
      const next = this.buildConfig();
      const area = await this.service.patchConfig(this.areaId, next);
      this.loaded = this.normalise(area.config as AreaConfig);
      this.saved.set(true);
    } catch {
      this.saveError.set(
        'Não conseguimos salvar as configurações. Tente de novo em instantes.'
      );
    } finally {
      this.saving.set(false);
    }
  }
}
