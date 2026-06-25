import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';

declare const L: any;

@Component({
  selector: 'jx-area-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div #mapEl class="jx-area-map"></div>`,
  styles: [`
    .jx-area-map { width: 100%; height: 400px; border-radius: 12px; border: 1px solid var(--border, #ddd); }
  `],
})
export class AreaMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapEl') mapEl!: ElementRef<HTMLDivElement>;
  @Input() boundary: any = null;
  @Output() boundaryChange = new EventEmitter<any>();

  private map: any = null;
  private drawnItems: any = null;
  private loaded = false;

  async ngAfterViewInit(): Promise<void> {
    await this.loadLeaflet();
    this.initMap();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['boundary'] && this.loaded && this.map) {
      this.drawExisting();
    }
  }

  ngOnDestroy(): void {
    if (this.map) this.map.remove();
  }

  private async loadLeaflet(): Promise<void> {
    if ((window as any).L) return;
    await this.loadCss('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css');
    await this.loadScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');
    await this.loadCss('https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css');
    await this.loadScript('https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js');
  }

  private initMap(): void {
    const center = this.boundary?.coordinates?.[0]?.[0]
      ? [this.boundary.coordinates[0][0][1], this.boundary.coordinates[0][0][0]]
      : [-21.54, -42.05];

    this.map = L.map(this.mapEl.nativeElement).setView(center, 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19,
    }).addTo(this.map);

    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);

    const drawControl = new L.Control.Draw({
      draw: {
        polygon: { shapeOptions: { color: '#e8722a', weight: 3, fillOpacity: 0.15 } },
        polyline: false,
        rectangle: false,
        circle: false,
        marker: false,
        circlemarker: false,
      },
      edit: { featureGroup: this.drawnItems },
    });
    this.map.addControl(drawControl);

    this.map.on(L.Draw.Event.CREATED, (e: any) => {
      this.drawnItems.clearLayers();
      this.drawnItems.addLayer(e.layer);
      this.emitBoundary();
    });
    this.map.on(L.Draw.Event.EDITED, () => this.emitBoundary());
    this.map.on(L.Draw.Event.DELETED, () => {
      this.boundaryChange.emit(null);
    });

    this.loaded = true;
    this.drawExisting();
  }

  private drawExisting(): void {
    if (!this.drawnItems || !this.boundary?.coordinates) return;
    this.drawnItems.clearLayers();
    const coords = this.boundary.coordinates[0].map((c: number[]) => [c[1], c[0]]);
    const polygon = L.polygon(coords, { color: '#e8722a', weight: 3, fillOpacity: 0.15 });
    this.drawnItems.addLayer(polygon);
    this.map.fitBounds(polygon.getBounds(), { padding: [30, 30] });
  }

  private emitBoundary(): void {
    const layers = this.drawnItems.getLayers();
    if (!layers.length) { this.boundaryChange.emit(null); return; }
    const latlngs = layers[0].getLatLngs()[0];
    const coordinates = [latlngs.map((ll: any) => [ll.lng, ll.lat])];
    coordinates[0].push(coordinates[0][0]);
    this.boundaryChange.emit({ type: 'Polygon', coordinates });
  }

  private loadScript(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = url;
      s.onload = () => resolve();
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  private loadCss(url: string): Promise<void> {
    return new Promise((resolve) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = url;
      link.onload = () => resolve();
      document.head.appendChild(link);
    });
  }
}
