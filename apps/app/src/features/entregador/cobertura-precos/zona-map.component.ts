import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { loadLeaflet } from '@jaxego/core/map/leaflet-loader';
import { MAP_DEFAULT_CENTER } from '@jaxego/core/map/map-tiles';
import {
  activeZoneStyle,
  brandTileLayer,
  onThemeChange,
  readMapPalette,
  referenceZoneStyle,
} from '@jaxego/core/map/map-theme';

/** Zona para a visão geral (várias zonas no mesmo mapa). */
export interface ZonaMapItem {
  name: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  boundary: any;
  active: boolean;
}

/**
 * Mapa da zona de cobertura do entregador (somente leitura). Redesign v3
 * (REDESIGN-v3.md §7): polígono tangerina com preenchimento suave lido dos
 * tokens, tiles temáticos, controles grandes para toque; repinta ao trocar tema.
 * Com `[zones]`, desenha a visão geral: ativas em tangerina, inativas tracejadas.
 */
@Component({
  selector: 'jx-zona-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div #mapEl class="jx-zona-map" role="img" [attr.aria-label]="ariaLabel"></div>`,
  styles: [`
    :host { display: block; height: 100%; }
    .jx-zona-map {
      width: 100%;
      height: 100%;
      min-height: var(--jx-zona-map-min, 300px);
    }
    :host ::ng-deep .leaflet-bar a {
      width: 44px !important;
      height: 44px !important;
      line-height: 44px !important;
    }
  `],
})
export class ZonaMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapEl') mapEl!: ElementRef<HTMLDivElement>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @Input() boundary: any = null;
  /** Visão geral: várias zonas (substitui `boundary` quando preenchido). */
  @Input() zones: ZonaMapItem[] | null = null;
  @Input() ariaLabel = 'Mapa da zona de cobertura';

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private L: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private map: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private layer: any = null;
  private loaded = false;
  private destroyed = false;
  private unwatchTheme: (() => void) | null = null;

  async ngAfterViewInit(): Promise<void> {
    this.L = await loadLeaflet();
    if (this.destroyed) return;
    this.initMap();
    this.unwatchTheme = onThemeChange(() => this.drawBoundary(false));
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['boundary'] || changes['zones']) && this.loaded && this.map) {
      // overview keeps the user's viewport when only the active flags change
      this.drawBoundary(!changes['zones'] || changes['zones'].firstChange);
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.unwatchTheme?.();
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  private initMap(): void {
    const L = this.L;
    const first = this.boundary ?? this.zones?.find((z) => z.boundary)?.boundary;
    const center = first?.coordinates?.[0]?.[0]
      ? [first.coordinates[0][0][1], first.coordinates[0][0][0]]
      : MAP_DEFAULT_CENTER;

    this.map = L.map(this.mapEl.nativeElement, { zoomControl: true }).setView(center, 13);
    this.map.zoomControl.setPosition('bottomright');
    brandTileLayer(L).addTo(this.map);

    this.loaded = true;
    this.drawBoundary(true);
  }

  private drawBoundary(fit: boolean): void {
    if (!this.map) return;
    const L = this.L;
    const palette = readMapPalette();
    const items: ZonaMapItem[] = this.zones?.length
      ? this.zones
      : this.boundary
        ? [{ name: '', boundary: this.boundary, active: true }]
        : [];
    this.layer?.remove();
    this.layer = L.featureGroup();
    for (const z of items) {
      if (!z.boundary?.coordinates) continue;
      const coords = z.boundary.coordinates[0].map((c: number[]) => [c[1], c[0]]);
      const poly = L.polygon(
        coords,
        z.active ? activeZoneStyle(palette.zone) : referenceZoneStyle(palette.zoneRef)
      );
      if (z.name) poly.bindTooltip(z.name, { direction: 'center', className: 'jx-map-tooltip' });
      this.layer.addLayer(poly);
    }
    this.layer.addTo(this.map);
    if (fit && this.layer.getLayers().length) {
      this.map.fitBounds(this.layer.getBounds(), { padding: [40, 40] });
    }
  }
}
