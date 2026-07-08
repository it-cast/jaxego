import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { IonContent, IonInfiniteScroll, IonInfiniteScrollContent } from '@ionic/angular/standalone';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faStar as faStarSolid } from '@fortawesome/free-solid-svg-icons';
import { AuthService } from '@jaxego/core/auth/auth.service';
import { PageHeaderComponent, DotsLoaderComponent } from '@jaxego/shared/components';
import { EmptyStateComponent } from '@jaxego/shared/state';
import { CourierScore, EntregadorService, RatingItem } from '../entregador.service';

@Component({
  selector: 'jx-avaliacoes',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, IonInfiniteScroll, IonInfiniteScrollContent, PageHeaderComponent, DotsLoaderComponent, FaIconComponent, EmptyStateComponent],
  template: `
    <ion-content>
      @if (loading()) {
        <jx-dots-loader />
      } @else {
        <jx-page-header title="Avaliações" [backLink]="backLink()" />
        <div class="jx-aval">
          @if (!displayed().length && !filterStars()) {
            <jx-empty-state
              imgSrc="self-confidence-amico.svg"
              title="Nenhuma avaliação ainda"
              message="Suas avaliações aparecem aqui após as entregas."
            />
          } @else {
            <!-- Panorama -->
            <div class="jx-aval__summary">
              <div class="jx-aval__summary-main">
                <span class="jx-aval__avg">{{ score()?.avg_stars || '-' }}</span>
                <span class="jx-aval__avg-star">
                  <fa-icon [icon]="iconStarSolid" aria-hidden="true" />
                </span>
              </div>
              <span class="jx-aval__count">{{ score()?.total_ratings || 0 }} {{ (score()?.total_ratings ?? 0) > 1 ? 'avaliações' : 'avaliação' }}</span>
            </div>

            <!-- Filter -->
            <div class="jx-aval__filter">
              <label class="jx-aval__filter-label">
                <span>Filtrar por estrelas</span>
                <select class="jx-aval__select" [value]="filterStars()" (change)="onFilter($event)">
                  <option value="0">Todas</option>
                  <option value="5">5 estrelas</option>
                  <option value="4">4 estrelas</option>
                  <option value="3">3 estrelas</option>
                  <option value="2">2 estrelas</option>
                  <option value="1">1 estrela</option>
                </select>
              </label>
            </div>

            <!-- List -->
            @if (!displayed().length) {
              <p class="jx-aval__empty-text">Nenhuma avaliação para este filtro.</p>
            } @else {
              <ul class="jx-aval__list">
                @for (r of displayed(); track r.id) {
                  <li class="jx-aval__item">
                    @if (r.merchant_name) {
                      <span class="jx-aval__merchant">{{ r.merchant_name }}</span>
                    }
                    <div class="jx-aval__item-head">
                      <span class="jx-aval__item-stars">
                        @for (s of [1,2,3,4,5]; track s) {
                          <fa-icon
                            [icon]="iconStarSolid"
                            [class.jx-aval__star-on]="s <= r.stars"
                            [class.jx-aval__star-off]="s > r.stars"
                            aria-hidden="true"
                          />
                        }
                      </span>
                      <span class="jx-aval__item-date">{{ formatDate(r.created_at) }}</span>
                    </div>
                    @if (r.comment) {
                      <p class="jx-aval__item-comment">"{{ r.comment }}"</p>
                    }
                  </li>
                }
              </ul>
            }
          }
        </div>

        <ion-infinite-scroll [disabled]="!hasMore()" (ionInfinite)="loadMore($event)">
          <ion-infinite-scroll-content loadingSpinner="dots" />
        </ion-infinite-scroll>
      }
    </ion-content>
  `,
  styles: [`
    .jx-aval { padding: var(--jx-space-4); display: flex; flex-direction: column; gap: var(--jx-space-3); }
    .jx-aval__summary {
      display: flex; flex-direction: column; align-items: center;
      gap: 4px; padding: var(--jx-space-4) 0;
    }
    .jx-aval__summary-main { display: flex; align-items: baseline; gap: 4px; }
    .jx-aval__avg { font-size: 48px; font-weight: 800; color: var(--text); }
    .jx-aval__avg-star { font-size: 28px; color: var(--brand, #e8722a); }
    .jx-aval__count { font-size: 14px; color: var(--text-muted, #888); }
    .jx-aval__filter { display: flex; }
    .jx-aval__filter-label { display: flex; flex-direction: column; gap: 4px; font-size: 11px; color: var(--text-muted, #888); flex: 1; }
    .jx-aval__select { min-height: 40px; padding: 0 12px; border: 1px solid var(--border, #ddd); border-radius: 12px; font-size: 14px; color: var(--text); background: #fff; }
    .jx-aval__empty-text { text-align: center; color: var(--text-muted, #888); font-size: 14px; margin: 0; }
    .jx-aval__list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
    .jx-aval__item { padding: var(--jx-space-3) 0; border-bottom: 1px solid var(--border, #eee); }
    .jx-aval__merchant { font-size: 14px; font-weight: 600; color: var(--text); display: block; margin-bottom: 2px; }
    .jx-aval__item-head { display: flex; align-items: center; justify-content: space-between; }
    .jx-aval__item-stars { display: flex; gap: 2px; font-size: 16px; }
    .jx-aval__star-on { color: var(--brand, #e8722a); }
    .jx-aval__star-off { color: var(--border, #ddd); }
    .jx-aval__item-date { font-size: 12px; color: var(--text-muted, #888); }
    .jx-aval__item-comment { margin: 4px 0 0; font-size: 14px; color: var(--text-muted, #888); font-style: italic; }
  `],
})
export class AvaliacoesPage implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly svc = inject(EntregadorService);

  protected readonly iconStarSolid = faStarSolid;

  private readonly route = inject(ActivatedRoute);
  protected readonly backLink = signal('/entregador/perfil');
  protected readonly loading = signal(true);
  protected readonly score = signal<CourierScore | null>(null);
  protected readonly ratings = signal<RatingItem[]>([]);
  protected readonly displayed = signal<RatingItem[]>([]);
  protected readonly filterStars = signal(0);
  protected readonly hasMore = signal(true);
  private readonly PAGE_SIZE = 10;

  async ngOnInit(): Promise<void> {
    const from = this.route.snapshot.queryParamMap.get('from');
    if (from === 'inicio') this.backLink.set('/entregador/inicio');
    const id = this.auth.me()?.courier_id;
    if (!id) return;
    const [sc, res] = await Promise.all([
      this.svc.score(id),
      this.svc.listRatings(id, this.PAGE_SIZE, 0),
    ]);
    this.score.set(sc);

    this.ratings.set(res.items);
    this.displayed.set(res.items);
    this.hasMore.set(res.items.length < res.total);
    this.loading.set(false);
  }

  protected async loadMore(event: any): Promise<void> {
    const id = this.auth.me()?.courier_id;
    if (!id) { event.target.complete(); return; }
    const offset = this.ratings().length;
    const res = await this.svc.listRatings(id, this.PAGE_SIZE, offset);
    const all = [...this.ratings(), ...res.items];
    this.ratings.set(all);

    this.applyFilter(all);
    this.hasMore.set(all.length < res.total);
    event.target.complete();
  }

  protected onFilter(e: Event): void {
    const v = Number((e.target as HTMLSelectElement).value);
    this.filterStars.set(v);
    this.applyFilter(this.ratings());
  }

  private applyFilter(list: RatingItem[]): void {
    const v = this.filterStars();
    this.displayed.set(v === 0 ? list : list.filter(r => r.stars === v));
  }

  protected formatDate(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }
}
