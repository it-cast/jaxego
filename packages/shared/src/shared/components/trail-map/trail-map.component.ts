import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  ViewChild,
  inject,
} from '@angular/core';
import { loadLeaflet } from '@jaxego/core/map/leaflet-loader';
import { MAP_DEFAULT_CENTER } from '@jaxego/core/map/map-tiles';
import { brandTileLayer, onThemeChange, readMapPalette } from '@jaxego/core/map/map-theme';

import { LinhaHistorico, TrailHistoryComponent } from './trail-history.component';

/** Contrato de GET /v1/admin/couriers/{id}/trail e GET /v1/deliveries/{id}/trail */
export interface TrailPoint {
  lat: number;
  lng: number;
  at: string;
  accuracy_m: number | null;
  delivery_id: number | null;
}
export interface TrailAction {
  action: string;
  lat: number;
  lng: number;
  at: string;
  delivery_id: number;
}
export interface Trail {
  courier_id: number;
  courier_name: string | null;
  start: string;
  end: string;
  delivery_id: number | null;
  points: TrailPoint[];
  actions: TrailAction[];
  distance_km: number;
  retention_days: number;
  truncated: boolean;
}

export const ROTULO_ACAO: Record<string, string> = {
  aceitou: 'Aceitou',
  coletou: 'Coletou',
  chegou_destino: 'Chegou ao destino',
  entregou: 'Entregou',
  recusou_entrega: 'Recusado no destino',
  cancelou_aceite: 'Desistiu',
};

const ORDEM_COR: Record<string, number> = {
  aceitou: 0,
  coletou: 1,
  chegou_destino: 2,
  entregou: 3,
  recusou_entrega: 4,
  cancelou_aceite: 5,
};

/**
 * jx-trail-map — rastro do entregador: a linha do trajeto (pontos periódicos + ações,
 * em ordem de horário), os pontos com horário no toque e os marcos da entrega
 * (aceitou, coletou, chegou, entregou) com cor própria. Leaflet lazy; cores dos tokens.
 */
@Component({
  selector: 'jx-trail-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TrailHistoryComponent],
  template: `
    <div class="jx-trail">
      <div class="jx-trail__map" role="img" [attr.aria-label]="ariaLabel">
        <div #mapHost class="jx-trail__host"></div>
        @if (vazio) {
          <div class="jx-trail__empty">Sem registros de posição nesse período.</div>
        }
      </div>
      @if (trail; as t) {
        <div class="jx-trail__resumo">
          <span><strong>{{ t.distance_km.toLocaleString('pt-BR') }} km</strong> percorridos</span>
          <span>{{ t.points.length }} posições</span>
          <span>{{ hora(t.start) }} – {{ hora(t.end) }}</span>
        </div>
        <div class="jx-trail__barra">
          <button type="button" class="jx-trail__hist-btn" (click)="historicoAberto = true" data-teste="rastro-historico">
            Histórico de localizações
            <span class="jx-trail__count">{{ t.points.length + t.actions.length }}</span>
          </button>
          @if (legenda.length) {
            <ul class="jx-trail__legenda" aria-label="Legenda do mapa">
              @for (a of legenda; track a) {
                <li><span class="jx-trail__dot" [style.background]="corAcao(a)"></span>{{ rotulo(a) }}</li>
              }
            </ul>
          }
        </div>
        @if (t.truncated) {
          <p class="jx-trail__aviso">Período com muitas posições: mostrando as primeiras 5.000. Diminua o intervalo.</p>
        }
        @if (historicoAberto) {
          <jx-trail-history
            [trail]="t"
            [mostrarEntrega]="mostrarEntrega"
            [corAcao]="corAcaoFn"
            (fechar)="historicoAberto = false"
            (verNoMapa)="focar($event)"
          />
        }
      }
    </div>
  `,
  styles: [
    `
      :host { display: block; }
      .jx-trail { display: grid; gap: var(--jx-space-3); }
      .jx-trail__map {
        position: relative;
        height: var(--jx-map-height, 420px);
        border-radius: var(--jx-radius-xl);
        overflow: hidden;
        border: 1px solid var(--border);
        background: var(--surface-sunken);
        isolation: isolate;
      }
      .jx-trail__host { position: absolute; inset: 0; z-index: 0; }
      .jx-trail__empty {
        position: absolute; inset: auto 12px 12px 12px; z-index: 500;
        padding: var(--jx-space-2) var(--jx-space-3);
        border-radius: var(--jx-radius-lg);
        background: var(--surface-elevated);
        box-shadow: var(--shadow-sm);
        font-size: var(--jx-text-sm);
        text-align: center;
      }
      .jx-trail__resumo { display: flex; flex-wrap: wrap; gap: var(--jx-space-2) var(--jx-space-4); font-size: var(--jx-text-sm); color: var(--text-muted); }
      .jx-trail__resumo strong { color: var(--text); }
      .jx-trail__barra { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--jx-space-2) var(--jx-space-4); }
      .jx-trail__hist-btn {
        display: inline-flex; align-items: center; gap: 8px;
        min-height: 40px; padding: 0 var(--jx-space-4);
        border: 1px solid var(--border-strong, var(--border)); border-radius: var(--jx-radius-lg);
        background: var(--surface); color: var(--brand);
        font-weight: 700; font-size: var(--jx-text-sm); cursor: pointer;
      }
      .jx-trail__hist-btn:hover { border-color: var(--brand); }
      .jx-trail__count {
        min-width: 22px; padding: 1px 7px; border-radius: 999px;
        background: var(--surface-sunken); color: var(--text-muted);
        font-size: 12px; font-weight: 600; text-align: center;
      }
      .jx-trail__legenda { margin: 0; padding: 0; list-style: none; display: flex; flex-wrap: wrap; gap: var(--jx-space-1) var(--jx-space-3); font-size: var(--jx-text-sm); color: var(--text-muted); }
      .jx-trail__legenda li { display: inline-flex; align-items: center; gap: 6px; }
      .jx-trail__dot { width: 10px; height: 10px; border-radius: 50%; flex: none; }
      .jx-trail__aviso { margin: 0; font-size: var(--jx-text-sm); color: var(--text-muted); }
    `,
  ],
})
export class TrailMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapHost', { static: true }) mapHost!: ElementRef<HTMLDivElement>;
  @Input() trail: Trail | null = null;
  @Input() ariaLabel = 'Mapa do trajeto do entregador';
  /** Mostra o nº da entrega nos marcos (rastro de um período, com várias entregas) */
  @Input() mostrarEntrega = false;

  private readonly cdr = inject(ChangeDetectorRef);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private L: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private map: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private camada: any = null;
  private destroyed = false;
  private offTheme: (() => void) | null = null;
  protected vazio = false;
  protected historicoAberto = false;
  /** Ações presentes no rastro, na ordem da legenda */
  protected legenda: string[] = [];
  protected readonly corAcaoFn = (acao: string) => this.corAcao(acao);

  async ngAfterViewInit(): Promise<void> {
    this.L = await loadLeaflet();
    if (this.destroyed) return;
    this.map = this.L.map(this.mapHost.nativeElement, { zoomControl: true, scrollWheelZoom: false }).setView(
      MAP_DEFAULT_CENTER,
      13,
    );
    this.map.zoomControl.setPosition('bottomright');
    brandTileLayer(this.L).addTo(this.map);
    this.offTheme = onThemeChange(() => this.desenhar());
    this.desenhar();
  }

  ngOnChanges(): void {
    this.desenhar();
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.offTheme?.();
    this.map?.remove();
  }

  protected hora(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  }

  protected rotulo(acao: string): string {
    return ROTULO_ACAO[acao] ?? acao;
  }

  protected corAcao(acao: string): string {
    const cores = readMapPalette(this.mapHost?.nativeElement).categorical;
    return cores[(ORDEM_COR[acao] ?? 6) % cores.length] || 'currentColor';
  }

  private desenhar(): void {
    const L = this.L;
    if (!L || !this.map) return;
    this.camada?.remove();
    this.camada = L.layerGroup().addTo(this.map);
    const t = this.trail;
    const pontos = t?.points ?? [];
    const acoes = t?.actions ?? [];
    this.vazio = !!t && pontos.length === 0 && acoes.length === 0;
    this.legenda = [...new Set(acoes.map((a) => a.action))].sort((a, b) => (ORDEM_COR[a] ?? 9) - (ORDEM_COR[b] ?? 9));
    this.cdr.markForCheck();
    if (!t || (pontos.length === 0 && acoes.length === 0)) return;

    const pal = readMapPalette(this.mapHost.nativeElement);
    const linha = [
      ...pontos.map((p) => ({ at: p.at, lat: p.lat, lng: p.lng })),
      ...acoes.map((a) => ({ at: a.at, lat: a.lat, lng: a.lng })),
    ].sort((a, b) => a.at.localeCompare(b.at));
    const coords = linha.map((p) => [p.lat, p.lng]);

    if (coords.length > 1) {
      L.polyline(coords, { color: pal.route || pal.pin, weight: 4, opacity: 0.85 }).addTo(this.camada);
    }
    for (const p of pontos) {
      L.circleMarker([p.lat, p.lng], {
        radius: 4,
        color: pal.route || pal.pin,
        weight: 1,
        fillColor: pal.surface || '#fff',
        fillOpacity: 1,
      })
        .bindTooltip(this.hora(p.at) + (p.accuracy_m ? ` · ±${Math.round(p.accuracy_m)} m` : ''))
        .addTo(this.camada);
    }
    for (const a of acoes) {
      L.circleMarker([a.lat, a.lng], {
        radius: 9,
        color: pal.surface || '#fff',
        weight: 3,
        fillColor: this.corAcao(a.action),
        fillOpacity: 1,
      })
        .bindTooltip(`${this.rotulo(a.action)} · ${this.hora(a.at)}`)
        .addTo(this.camada);
    }
    // Início e fim do trajeto
    const ini = linha[0];
    const fim = linha[linha.length - 1];
    L.marker([ini.lat, ini.lng], { icon: this.rotuloIcone(L, 'Início'), keyboard: false }).addTo(this.camada);
    if (linha.length > 1) {
      L.marker([fim.lat, fim.lng], { icon: this.rotuloIcone(L, 'Fim'), keyboard: false }).addTo(this.camada);
    }
    if (coords.length === 1) this.map.setView(coords[0], 16);
    else this.map.fitBounds(L.latLngBounds(coords), { padding: [32, 32], maxZoom: 17 });
  }

  /** "Ver no mapa" do histórico: fecha o modal, centraliza o ponto e mostra o horário */
  protected focar(l: LinhaHistorico): void {
    this.historicoAberto = false;
    this.cdr.markForCheck();
    if (!this.L || !this.map) return;
    const texto = `${l.tipo === 'posicao' ? 'Posição' : this.rotulo(l.tipo)} · ${this.hora(l.at)}`;
    this.map.setView([l.lat, l.lng], Math.max(this.map.getZoom(), 17));
    this.L.popup({ closeButton: true, autoPan: true }).setLatLng([l.lat, l.lng]).setContent(texto).openOn(this.map);
    this.mapHost.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private rotuloIcone(L: any, texto: string): any {
    return L.divIcon({
      className: 'jx-map-chip jx-trail-tag',
      html: `<span>${texto}</span>`,
      iconSize: null,
      iconAnchor: [-8, 12],
    });
  }
}
