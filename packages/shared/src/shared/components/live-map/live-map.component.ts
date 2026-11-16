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
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faLocationCrosshairs } from '@fortawesome/free-solid-svg-icons';
import { loadLeaflet } from '@jaxego/core/map/leaflet-loader';
import { brandPinIcon, brandTileLayer, type PinKind } from '@jaxego/core/map/map-theme';

/**
 * jx-live-map — mapa de posição pontual (destino da entrega / entregador).
 * Redesign v3 (REDESIGN-v3.md §7): pin SVG da marca com anel pulsante (sem
 * imagem do unpkg), chip de legenda sobreposto, botão "centralizar", tiles
 * temáticos (claro/escuro via `--map-tiles-filter`). Leaflet lazy (bundle à parte).
 */
@Component({
  selector: 'jx-live-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FaIconComponent],
  template: `
    <div class="jx-live-map" role="img" [attr.aria-label]="ariaLabel">
      <div #mapHost class="jx-live-map__host"></div>
      @if (!loaded) {
        <div class="jx-live-map__skeleton" aria-hidden="true">
          <span class="jx-live-map__skeleton-pin"></span>
        </div>
      }
      @if (label) {
        <span class="jx-map-chip jx-live-map__chip">
          <span class="jx-map-chip__dot" [class.jx-map-chip__dot--live]="live"></span>
          {{ label }}
        </span>
      }
      @if (loaded) {
        <button
          type="button"
          class="jx-live-map__recenter"
          aria-label="Centralizar no ponto"
          title="Centralizar"
          (click)="recenter()"
        >
          <fa-icon [icon]="iconRecenter" aria-hidden="true" />
        </button>
      }
    </div>
  `,
  styleUrl: './live-map.component.scss',
})
export class LiveMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapHost', { static: true }) mapHost!: ElementRef<HTMLDivElement>;

  @Input() lat: number | null = null;
  @Input() lng: number | null = null;
  @Input() ariaLabel = 'Posição no mapa';
  /** Tipo do pin: destino da entrega (tangerina) ou entregador (azul-noite). */
  @Input() kind: PinKind = 'destination';
  /** Texto do chip sobreposto (vazio = sem chip). */
  @Input() label = '';
  /** Chip com ponto "ao vivo" piscando. */
  @Input() live = false;
  @Input() zoom = 15;

  private readonly cdr = inject(ChangeDetectorRef);
  protected loaded = false;
  protected readonly iconRecenter = faLocationCrosshairs;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private map: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private marker: any = null;
  private destroyed = false;

  ngAfterViewInit(): void {
    void this.loadMap();
  }

  ngOnChanges(): void {
    if (this.map && this.marker && this.lat != null && this.lng != null) {
      this.marker.setLatLng([this.lat, this.lng]);
      this.map.panTo([this.lat, this.lng], { animate: true });
    }
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.map?.remove();
  }

  protected recenter(): void {
    if (this.map && this.lat != null && this.lng != null) {
      this.map.flyTo([this.lat, this.lng], this.zoom, { duration: 0.6 });
    }
  }

  private async loadMap(): Promise<void> {
    if (this.lat == null || this.lng == null) return;

    const L = await loadLeaflet();
    if (this.destroyed) return;

    const center = [this.lat, this.lng];
    this.map = L.map(this.mapHost.nativeElement, {
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: false, // não sequestra o scroll da página
    }).setView(center, this.zoom);
    this.map.zoomControl.setPosition('bottomright');

    brandTileLayer(L).addTo(this.map);
    this.marker = L.marker(center, {
      icon: brandPinIcon(L, this.kind),
      keyboard: false,
      title: this.ariaLabel,
    }).addTo(this.map);

    this.loaded = true;
    this.cdr.markForCheck();
  }
}
