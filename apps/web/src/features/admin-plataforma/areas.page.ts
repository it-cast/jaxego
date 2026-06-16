import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  EmptyStateComponent,
  ErrorStateComponent,
  LoadingSkeletonComponent,
} from '../../shared/state';
import { Area, PlatformAdminService } from './platform-admin.service';

/**
 * Áreas (plataforma) — criar/editar/arquivar cidade + % de repasse (F3.1/F3.2).
 * O CRUD existia no backend (/v1/areas) sem UI; esta é a tela do "adicionar área".
 * O % de repasse é dado de negócio (TD-13-01), não move dinheiro no M1. Tokens only.
 */
@Component({
  selector: 'jx-plataforma-areas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, EmptyStateComponent, ErrorStateComponent, LoadingSkeletonComponent],
  template: `
    <section class="jx-areas">
      <h1 class="jx-areas__title">Áreas</h1>

      <form class="jx-areas__card" (submit)="create($event)">
        <h2 class="jx-areas__h2">Nova área</h2>
        <div class="jx-areas__form">
          <label>
            <span>Identificador (slug)</span>
            <input name="codename" [(ngModel)]="newCodename" placeholder="ex.: padua" required />
          </label>
          <label>
            <span>Nome</span>
            <input name="name" [(ngModel)]="newName" placeholder="ex.: Pádua" required />
          </label>
          <label>
            <span>Validação exigida</span>
            <select name="kyc" [(ngModel)]="newKyc">
              <option value="simples">Simples (CPF + selfie)</option>
              <option value="completa">Completa (CNH + CRLV + MEI)</option>
            </select>
          </label>
          <button type="submit" class="jx-areas__primary" [disabled]="saving()">
            Criar área
          </button>
        </div>
        @if (createError()) {
          <p class="jx-areas__err" role="alert">{{ createError() }}</p>
        }
      </form>

      @if (loading()) {
        <jx-loading-skeleton />
      } @else if (error()) {
        <jx-error-state message="Não foi possível carregar as áreas." (retry)="reload()" />
      } @else if (!areas().length) {
        <jx-empty-state icon="◰" title="Nenhuma área" message="Crie a primeira área acima." />
      } @else {
        @for (a of areas(); track a.id) {
          <article class="jx-areas__card">
            <div class="jx-areas__row">
              <label class="jx-areas__grow">
                <span>Nome</span>
                <input [(ngModel)]="a.name" />
              </label>
              <label>
                <span>Slug</span>
                <input class="jx-areas__mono" [value]="a.codename" disabled />
              </label>
              <label>
                <span>Validação</span>
                <select [ngModel]="kycOf(a)" (ngModelChange)="setKyc(a, $event)">
                  <option value="simples">Simples</option>
                  <option value="completa">Completa</option>
                </select>
              </label>
            </div>
            <div class="jx-areas__row">
              <label>
                <span>Repasse (%)</span>
                <input
                  class="jx-areas__mono"
                  type="number"
                  min="0"
                  max="100"
                  [(ngModel)]="revenue[a.id]"
                  placeholder="10"
                />
              </label>
              <button type="button" class="jx-areas__ghost" (click)="save(a)">
                Salvar
              </button>
              <button type="button" class="jx-areas__danger" (click)="archive(a)">
                Arquivar
              </button>
            </div>
          </article>
        }
      }
    </section>
  `,
  styles: [
    `
      .jx-areas {
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-3);
        max-width: 720px;
      }
      .jx-areas__title {
        font-family: var(--jx-font-display);
        font-size: var(--jx-text-2xl);
        margin: 0;
      }
      .jx-areas__card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-lg);
        padding: var(--jx-space-3);
        display: flex;
        flex-direction: column;
        gap: var(--jx-space-2);
      }
      .jx-areas__h2 {
        font-size: var(--jx-text-md);
        margin: 0;
      }
      .jx-areas__form,
      .jx-areas__row {
        display: flex;
        gap: var(--jx-space-2);
        align-items: flex-end;
        flex-wrap: wrap;
      }
      .jx-areas__grow {
        flex: 1 1 200px;
      }
      label {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: var(--jx-text-xs);
        color: var(--text-muted);
      }
      input,
      select {
        padding: var(--jx-space-2);
        border: 1px solid var(--border);
        border-radius: var(--jx-radius-md);
        background: var(--surface);
        color: var(--text);
        font-size: var(--jx-text-sm);
      }
      .jx-areas__mono {
        font-family: var(--jx-font-mono);
      }
      .jx-areas__primary,
      .jx-areas__ghost,
      .jx-areas__danger {
        border: 0;
        border-radius: var(--jx-radius-md);
        padding: var(--jx-space-2) var(--jx-space-3);
        font-weight: var(--jx-weight-bold);
        cursor: pointer;
        min-height: 40px;
      }
      .jx-areas__primary {
        background: var(--jx-color-brand-500);
        color: var(--jx-neutral-50);
      }
      .jx-areas__ghost {
        background: var(--surface-sunken);
        color: var(--text);
      }
      .jx-areas__danger {
        background: transparent;
        color: var(--jx-color-semantic-error);
        border: 1px solid var(--border);
      }
      .jx-areas__err {
        color: var(--jx-color-semantic-error);
        font-size: var(--jx-text-sm);
        margin: 0;
      }
    `,
  ],
})
export class PlataformaAreasPage implements OnInit {
  private readonly svc = inject(PlatformAdminService);

  protected readonly areas = signal<Area[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly saving = signal(false);
  protected readonly createError = signal<string | null>(null);
  protected readonly revenue: Record<number, number | null> = {};

  protected newCodename = '';
  protected newName = '';
  protected newKyc = 'simples';

  async ngOnInit(): Promise<void> {
    await this.reload();
  }

  protected async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(false);
    try {
      this.areas.set(await this.svc.listAreas());
    } catch {
      this.error.set(true);
    } finally {
      this.loading.set(false);
    }
  }

  protected kycOf(a: Area): string {
    return (a.config?.['kyc_level'] as string) ?? 'simples';
  }

  protected setKyc(a: Area, value: string): void {
    a.config = { ...(a.config ?? {}), kyc_level: value };
  }

  protected async create(ev: Event): Promise<void> {
    ev.preventDefault();
    this.createError.set(null);
    if (!this.newCodename.trim() || !this.newName.trim()) return;
    this.saving.set(true);
    try {
      await this.svc.createArea({
        codename: this.newCodename.trim(),
        name: this.newName.trim(),
        config: { kyc_level: this.newKyc },
      });
      this.newCodename = '';
      this.newName = '';
      this.newKyc = 'simples';
      await this.reload();
    } catch {
      this.createError.set('Não foi possível criar (slug já existe?). Tente outro identificador.');
    } finally {
      this.saving.set(false);
    }
  }

  protected async save(a: Area): Promise<void> {
    await this.svc.updateArea(a.id, { name: a.name, config: a.config });
    const pct = this.revenue[a.id];
    if (pct !== null && pct !== undefined && !Number.isNaN(pct)) {
      await this.svc.setRevenueShare(a.id, Number(pct));
    }
    await this.reload();
  }

  protected async archive(a: Area): Promise<void> {
    await this.svc.archiveArea(a.id);
    await this.reload();
  }
}
