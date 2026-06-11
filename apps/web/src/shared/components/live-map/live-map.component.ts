import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  ViewChild,
  inject,
} from '@angular/core';
import { ThemeService } from '../../../core/theme/theme.service';

/**
 * jx-live-map — MapLibre raster (OSM) map for the public tracker (tela 26).
 *
 * PERFORMANCE (performance-web-vitals): MapLibre is imported DYNAMICALLY only after
 * the element scrolls into view (IntersectionObserver) — so `maplibre-gl` lives in a
 * SEPARATE lazy chunk, never the main bundle, and the LCP (the timeline + ETA banner)
 * does not wait for it. A skeleton reserves the height (no CLS). The page is fully
 * usable without the map (it is decorative; the timeline is the textual alternative).
 *
 * ACCESSIBILITY: `role="img"` + `aria-label` (the courier's approximate position); the
 * textual alternative is the timeline. DARK MODE (DEC-001): a CSS filter inverts the
 * raster tiles in the dark theme (reacts to ThemeService without reload). Tokens only.
 */
@Component({
  selector: 'jx-live-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      class="jx-live-map"
      [class.jx-live-map--dark]="theme.theme() === 'dark'"
      role="img"
      [attr.aria-label]="ariaLabel"
    >
      <div #mapHost class="jx-live-map__host"></div>
      @if (!loaded) {
        <div class="jx-live-map__skeleton" aria-hidden="true"></div>
      }
    </div>
  `,
  styleUrl: './live-map.component.scss',
})
export class LiveMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapHost', { static: true }) mapHost!: ElementRef<HTMLDivElement>;

  @Input() lat: number | null = null;
  @Input() lng: number | null = null;
  @Input() ariaLabel = 'Posição aproximada do entregador no mapa';

  protected readonly theme = inject(ThemeService);
  protected loaded = false;

  private observer: IntersectionObserver | null = null;
  // The MapLibre instances are `unknown` until the lazy module loads.
  private map: { setCenter: (c: [number, number]) => void; remove: () => void } | null = null;
  private marker: { setLngLat: (c: [number, number]) => void } | null = null;

  ngAfterViewInit(): void {
    // Defer the heavy import until the map scrolls into view (after first paint).
    if (typeof IntersectionObserver === 'undefined') {
      void this.loadMap();
      return;
    }
    this.observer = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        this.observer?.disconnect();
        void this.loadMap();
      }
    });
    this.observer.observe(this.mapHost.nativeElement);
  }

  ngOnChanges(): void {
    if (this.map && this.lat != null && this.lng != null) {
      this.map.setCenter([this.lng, this.lat]);
      this.marker?.setLngLat([this.lng, this.lat]);
    }
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    this.map?.remove();
  }

  /** Dynamic import → MapLibre lives in a separate lazy chunk (out of main bundle). */
  private async loadMap(): Promise<void> {
    if (this.lat == null || this.lng == null) return;
    const maplibre = (await import('maplibre-gl')).default;
    const center: [number, number] = [this.lng, this.lat];
    this.map = new maplibre.Map({
      container: this.mapHost.nativeElement,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            // Pilot tile source (TD-019 — single point of config, swap to self-host).
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap',
          },
        },
        layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
      },
      center,
      zoom: 14,
      attributionControl: true,
    }) as unknown as { setCenter: (c: [number, number]) => void; remove: () => void };
    this.marker = new maplibre.Marker().setLngLat(center).addTo(this.map as never) as unknown as {
      setLngLat: (c: [number, number]) => void;
    };
    this.loaded = true;
  }
}
