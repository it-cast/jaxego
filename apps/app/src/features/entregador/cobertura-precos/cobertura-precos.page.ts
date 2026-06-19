import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { IonContent } from '@ionic/angular/standalone';
import { AuthService } from '@jaxego/core/auth/auth.service';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  WarnBannerComponent,
} from '@jaxego/shared/state';
import { formatBrl, maskBrl, parseBrl } from '@jaxego/shared/util/money';
import {
  CoverageItem,
  CoverageListComponent,
} from './coverage-list.component';
import {
  CoberturaPrecosService,
  CoverageRow,
  PricingRow,
} from './cobertura-precos.service';

interface KmBand {
  upToKm: string; // numeric text
  price: string; // masked
  priceError?: string | null;
}

/**
 * Tela 10 — Bairros e preços (UI-SPEC §4, RN-003/RN-015). Ionic, mobile-first.
 *
 * The courier picks the neighborhoods they serve (coverage valid for pickup AND
 * dropoff — RN-003) and sets the price by neighborhood OR by km. The platform
 * NEVER fixes the price: it only imposes the area floor and rejects below it,
 * CITING the floor (RN-015). The floor comes from the area config (mono, never
 * hardcoded). Touch ≥44px; AA light+dark; safe-area; prefers-reduced-motion.
 */
@Component({
  selector: 'jx-cobertura-precos',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    IonContent,
    CoverageListComponent,
    EmptyStateComponent,
    ErrorStateComponent,
    WarnBannerComponent,
  ],
  templateUrl: './cobertura-precos.page.html',
  styleUrl: './cobertura-precos.page.scss',
})
export class CoberturaPrecosPage implements OnInit {
  private readonly service = inject(CoberturaPrecosService);
  private readonly auth = inject(AuthService);

  protected get courierId(): number {
    return this.auth.me()?.courier_id ?? 0;
  }

  // The floors come from the area config (never hardcoded — single source).
  protected pisoEntrega = 0;
  protected pisoKm = 0;

  protected readonly mode = signal<'neighborhood' | 'km'>('neighborhood');
  protected readonly items = signal<CoverageItem[]>([]);
  protected kmBands: KmBand[] = [{ upToKm: '', price: '' }];
  protected returnPct = 0;

  protected readonly saving = signal(false);
  protected readonly saved = signal(false);
  protected readonly saveError = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    try {
      const [catalog, coverage, pricing] = await Promise.all([
        this.service.catalog(),
        this.service.getCoverage(this.courierId).catch(() => [] as CoverageRow[]),
        this.service.getPricing(this.courierId).catch(() => [] as PricingRow[]),
      ]);
      const covered = new Set(
        coverage.filter((r) => r.kind === 'include').map((r) => r.neighborhood_id)
      );
      const excluded = new Set(
        coverage.filter((r) => r.kind === 'exclude').map((r) => r.neighborhood_id)
      );
      const priceMap = new Map(
        pricing
          .filter((r) => r.neighborhood_id != null)
          .map((r) => [r.neighborhood_id!, r] as const)
      );
      this.items.set(
        catalog.map((n) => {
          const row = priceMap.get(n.id);
          return {
            neighborhoodId: n.id,
            name: n.name,
            covered: covered.has(n.id),
            excluded: excluded.has(n.id),
            price: row ? maskBrl(String(Math.round(Number(row.price) * 100))) : '',
            priceError: null,
          };
        })
      );
      if (pricing.length > 0) {
        if (pricing[0].return_pct != null) {
          this.returnPct = Number(pricing[0].return_pct);
        }
        const savedMode = pricing[0].mode as 'neighborhood' | 'km' | undefined;
        if (savedMode) {
          this.mode.set(savedMode);
        }
        if (savedMode === 'km') {
          this.kmBands = pricing
            .filter((r) => r.up_to_km != null)
            .map((r) => ({
              upToKm: String(r.up_to_km),
              price: maskBrl(String(Math.round(Number(r.price) * 100))),
            }));
          if (this.kmBands.length === 0) {
            this.kmBands = [{ upToKm: '', price: '' }];
          }
        }
      }
    } catch {
      // Catalog empty or unreachable — empty-state guides the user.
    }
  }

  protected get pisoLabel(): string {
    return this.mode() === 'km' ? formatBrl(this.pisoKm) : formatBrl(this.pisoEntrega);
  }

  protected get warnMessage(): string {
    return `Você só recebe ofertas quando a coleta E a entrega estão nos seus bairros. Piso da cidade: ${this.pisoLabel}.`;
  }

  protected setMode(mode: 'neighborhood' | 'km'): void {
    // Switching mode preserves the data of the other mode.
    this.mode.set(mode);
  }

  protected onReturnInput(event: Event): void {
    const raw = (event.target as HTMLInputElement).value.replace(/\D/g, '');
    this.returnPct = Math.min(100, raw === '' ? 0 : parseInt(raw, 10));
  }

  protected addBand(): void {
    this.kmBands = [...this.kmBands, { upToKm: '', price: '' }];
  }

  protected onBandKm(band: KmBand, event: Event): void {
    band.upToKm = (event.target as HTMLInputElement).value.replace(/[^\d.]/g, '');
  }

  protected onBandPrice(band: KmBand, event: Event): void {
    band.price = maskBrl((event.target as HTMLInputElement).value);
  }

  protected get hasCoverage(): boolean {
    return this.items().some((i) => i.covered && !i.excluded);
  }

  /** Validate a price against the floor; set the inline error citing the floor. */
  private validatePrice(price: number, floor: number, name: string): string | null {
    if (price < floor) {
      return `O preço de ${name} está abaixo do piso da cidade (${formatBrl(
        floor
      )}). Ajuste para salvar.`;
    }
    return null;
  }

  async save(): Promise<void> {
    this.saved.set(false);
    this.saveError.set(null);

    // Coverage payload.
    const includes = this.items()
      .filter((i) => i.covered && !i.excluded)
      .map((i) => i.neighborhoodId);
    const excludes = this.items()
      .filter((i) => i.excluded)
      .map((i) => i.neighborhoodId);

    // Pricing payload + floor validation (cites the floor).
    let pricingRows: PricingRow[] = [];
    let blocked = false;

    if (this.mode() === 'neighborhood') {
      this.items.update((items) =>
        items.map((it) => {
          if (it.covered && !it.excluded) {
            const value = parseBrl(it.price);
            const err = this.validatePrice(value, this.pisoEntrega, it.name);
            return { ...it, priceError: err };
          }
          return { ...it, priceError: null };
        })
      );
      blocked = this.items().some((i) => i.priceError);
      pricingRows = this.items()
        .filter((i) => i.covered && !i.excluded)
        .map((i) => ({
          neighborhood_id: i.neighborhoodId,
          price: parseBrl(i.price),
          return_pct: this.returnPct,
        }));
    } else {
      this.kmBands = this.kmBands.map((b) => {
        const value = parseBrl(b.price);
        const err = this.validatePrice(value, this.pisoKm, `até ${b.upToKm} km`);
        return { ...b, priceError: err };
      });
      blocked = this.kmBands.some((b) => b.priceError);
      pricingRows = this.kmBands
        .filter((b) => b.upToKm !== '')
        .map((b) => ({
          up_to_km: parseFloat(b.upToKm),
          price: parseBrl(b.price),
          return_pct: this.returnPct,
        }));
    }

    if (blocked) {
      this.saveError.set('Há preços abaixo do piso da cidade. Ajuste para salvar.');
      return;
    }

    this.saving.set(true);
    try {
      await this.service.putCoverage(this.courierId, { includes, excludes });
      await this.service.putPricing(this.courierId, {
        mode: this.mode(),
        rows: pricingRows,
      });
      this.saved.set(true);
    } catch (err) {
      if (err instanceof HttpErrorResponse && err.status === 422) {
        this.saveError.set(
          err.error?.error?.message ??
            'Preço abaixo do piso da cidade. Ajuste para salvar.'
        );
      } else {
        this.saveError.set('Não conseguimos salvar. Tente de novo em instantes.');
      }
    } finally {
      this.saving.set(false);
    }
  }
}
