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
import { brandPinIcon, brandTileLayer, onThemeChange, readMapPalette } from '@jaxego/core/map/map-theme';

export interface LatLng {
  lat: number;
  lng: number;
}

/**
 * jx-route-map — coleta → destino (redesign v3 §7). Pin da loja (azul) e pin do
 * destino (tangerina) ligados por uma linha tracejada (sem motor de rota: é
 * orientação visual; a navegação real abre no app de mapas). Sem `to`, mostra
 * só a coleta — respeita a RN-013 (destino exato só após a coleta).
 */
@Component({
  selector: 'jx-route-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-route-map" role="img" [attr.aria-label]="ariaLabel">
      <div #mapHost class="jx-route-map__host"></div>
      @if (!loaded) {
        <div class="jx-route-map__skeleton" aria-hidden="true"></div>
      }
      @if (label) {
        <span class="jx-map-chip jx-route-map__chip">
          <span class="jx-map-chip__dot"></span>{{ label }}
        </span>
      }
    </div>
  `,
  styles: [
    `
      :host { display: block; }
      .jx-route-map {
        position: relative;
        height: var(--jx-map-height, 220px);
        border-radius: var(--jx-map-radius, var(--jx-radius-xl));
        overflow: hidden;
        border: 1px solid var(--border);
        background: var(--surface-sunken);
        box-shadow: var(--shadow-md);
        isolation: isolate;
      }
      .jx-route-map__host { position: absolute; inset: 0; }
      .jx-route-map__skeleton {
        position: absolute; inset: 0; z-index: 1;
        background: var(--surface-sunken);
        animation: jx-route-shimmer 1.4s ease-in-out infinite;
      }
      .jx-route-map__chip {
        position: absolute; left: var(--jx-space-3); top: var(--jx-space-3); z-index: 500;
      }
      @keyframes jx-route-shimmer { 50% { opacity: 0.6; } }
      @media (prefers-reduced-motion: reduce) { .jx-route-map__skeleton { animation: none; } }
    `,
  ],
})
export class RouteMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapHost', { static: true }) mapHost!: ElementRef<HTMLDivElement>;

  @Input() from: LatLng | null = null;
  @Input() to: LatLng | null = null;
  @Input() label = '';
  @Input() ariaLabel = 'Mapa da rota da entrega';

  private readonly cdr = inject(ChangeDetectorRef);
  protected loaded = false;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private L: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private map: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private layer: any = null;
  private destroyed = false;
  private unwatchTheme: (() => void) | null = null;

  async ngAfterViewInit(): Promise<void> {
    if (!this.from && !this.to) return;
    this.L = await loadLeaflet();
    if (this.destroyed) return;
    const first = this.from ?? this.to!;
    this.map = this.L.map(this.mapHost.nativeElement, {
      zoomControl: false,
      attributionControl: true,
      scrollWheelZoom: false,
    }).setView([first.lat, first.lng], 15);
    brandTileLayer(this.L).addTo(this.map);
    this.draw(true);
    this.unwatchTheme = onThemeChange(() => this.draw(false));
    this.loaded = true;
    this.cdr.markForCheck();
  }

  ngOnChanges(): void {
    if (this.map) this.draw(true);
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.unwatchTheme?.();
    this.map?.remove();
  }

  private draw(fit: boolean): void {
    const L = this.L;
    this.layer?.remove();
    this.layer = L.featureGroup();
    const pts: [number, number][] = [];
    if (this.from) {
      pts.push([this.from.lat, this.from.lng]);
      L.marker(pts[pts.length - 1], { icon: brandPinIcon(L, 'store'), keyboard: false, title: 'Coleta' }).addTo(this.layer);
    }
    if (this.to) {
      pts.push([this.to.lat, this.to.lng]);
      L.marker(pts[pts.length - 1], { icon: brandPinIcon(L, 'destination'), keyboard: false, title: 'Entrega' }).addTo(this.layer);
    }
    if (pts.length === 2) {
      L.polyline(pts, {
        color: readMapPalette().route,
        weight: 4,
        opacity: 0.8,
        dashArray: '2 10',
        lineCap: 'round',
      }).addTo(this.layer);
    }
    this.layer.addTo(this.map);
    if (!fit) return;
    if (pts.length === 2) this.map.fitBounds(this.layer.getBounds(), { padding: [48, 48], maxZoom: 16 });
    else if (pts.length === 1) this.map.setView(pts[0], 15);
  }
}
