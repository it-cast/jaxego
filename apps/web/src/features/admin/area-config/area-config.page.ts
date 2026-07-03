import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ErrorStateComponent } from '@jaxego/shared/state/error-state.component';
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
 * Fieldsets: validação / despacho. Sensitive-change confirmation (before→after)
 * before the audited PATCH. Save states: salvando (aria-busy) → sucesso
 * (role=status) / erro (role=alert + retry). Only semantic vars; AA light+dark.
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

  protected readonly areaName = signal('');

  protected readonly saving = signal(false);
  protected readonly saved = signal(false);
  protected readonly saveError = signal<string | null>(null);
  protected readonly confirming = signal(false);
  protected readonly sensitiveDiff = signal<SensitiveDiffRow[]>([]);

  private loaded: AreaConfig | null = null;

  protected readonly form = this.fb.nonNullable.group({
    kyc_level: this.fb.nonNullable.control<'simples' | 'completa'>('simples'),
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
  });

  async ngOnInit(): Promise<void> {
    try {
      const area = await this.service.get();
      this.areaName.set(area.name);
      const cfg = area.config as AreaConfig;
      this.loaded = this.normalise(cfg);
      this.form.patchValue({
        kyc_level: this.loaded.kyc_level,
        timeout_oferta_s: this.loaded.timeout_oferta_s,
        timeout_favoritos_s: this.loaded.timeout_favoritos_s,
      });
    } catch {
      this.saveError.set('Não conseguimos carregar a configuração. Tente de novo.');
    }
  }

  private normalise(cfg: Partial<AreaConfig>): AreaConfig {
    return {
      kyc_level: cfg.kyc_level ?? 'simples',
      timeout_oferta_s: cfg.timeout_oferta_s ?? 20,
      timeout_favoritos_s: cfg.timeout_favoritos_s ?? 60,
    };
  }

  protected rangeError(
    controlName: 'timeout_oferta_s' | 'timeout_favoritos_s'
  ): string | null {
    const ctrl = this.form.controls[controlName];
    if (!ctrl.touched || ctrl.valid) {
      return null;
    }
    switch (controlName) {
      case 'timeout_oferta_s':
        return 'O tempo de oferta precisa estar entre 10 e 60 segundos.';
      case 'timeout_favoritos_s':
        return 'A janela de favoritos precisa estar entre 30 e 180 segundos.';
    }
  }

  private buildConfig(): AreaConfig {
    const v = this.form.getRawValue();
    return {
      kyc_level: v.kyc_level,
      timeout_oferta_s: Number(v.timeout_oferta_s),
      timeout_favoritos_s: Number(v.timeout_favoritos_s),
    };
  }

  private computeDiff(next: AreaConfig): SensitiveDiffRow[] {
    if (!this.loaded) {
      return [];
    }
    const labels: Record<keyof AreaConfig, string> = {
      kyc_level: 'Nível de validação',
      timeout_oferta_s: 'Tempo de oferta',
      timeout_favoritos_s: 'Janela de favoritos',
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
      const area = await this.service.patchConfig(next);
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
