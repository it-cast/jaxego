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

/**
 * jx-live-map — Leaflet + OSM para exibir o ponto de destino da entrega.
 * Importado dinamicamente (lazy) para não impactar o bundle principal.
 * Sem @types/leaflet — usa `any` para manter "types": [] no tsconfig.
 */
@Component({
  selector: 'jx-live-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-live-map" role="img" [attr.aria-label]="ariaLabel">
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
  @Input() ariaLabel = 'Posição no mapa';

  private readonly cdr = inject(ChangeDetectorRef);
  protected loaded = false;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private map: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private marker: any = null;

  ngAfterViewInit(): void {
    void this.loadMap();
  }

  ngOnChanges(): void {
    if (this.map && this.marker && this.lat != null && this.lng != null) {
      this.map.setView([this.lat, this.lng], 15);
      this.marker.setLatLng([this.lat, this.lng]);
    }
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  private async loadMap(): Promise<void> {
    if (this.lat == null || this.lng == null) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    // @ts-ignore — leaflet sem @types para manter "types":[] do tsconfig
    const L: any = await import('leaflet');

    const iconDefault = L.icon({
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    });

    const center = [this.lat, this.lng];
    this.map = L.map(this.mapHost.nativeElement, { zoomControl: true }).setView(center, 15);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap',
    }).addTo(this.map);

    this.marker = L.marker(center, { icon: iconDefault }).addTo(this.map);

    this.loaded = true;
    this.cdr.markForCheck();
  }
}
