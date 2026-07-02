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

declare const L: any;

@Component({
  selector: 'jx-zona-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<div #mapEl class="jx-zona-map"></div>`,
  styles: [`
    .jx-zona-map {
      width: 100%;
      height: 100%;
      min-height: 300px;
    }
  `],
})
export class ZonaMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapEl') mapEl!: ElementRef<HTMLDivElement>;
  @Input() boundary: any = null;

  private map: any = null;
  private loaded = false;

  async ngAfterViewInit(): Promise<void> {
    await this.loadLeaflet();
    this.initMap();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['boundary'] && this.loaded && this.map) {
      this.drawBoundary();
    }
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  private async loadLeaflet(): Promise<void> {
    if ((window as any).L) return;
    await this.loadCss('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css');
    await this.loadScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');
  }

  private initMap(): void {
    const center = this.boundary?.coordinates?.[0]?.[0]
      ? [this.boundary.coordinates[0][0][1], this.boundary.coordinates[0][0][0]]
      : [-21.54, -42.05];

    this.map = L.map(this.mapEl.nativeElement, { zoomControl: true }).setView(center, 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19,
    }).addTo(this.map);

    this.loaded = true;
    this.drawBoundary();
  }

  private drawBoundary(): void {
    if (!this.boundary?.coordinates) return;
    const coords = this.boundary.coordinates[0].map((c: number[]) => [c[1], c[0]]);
    const polygon = L.polygon(coords, {
      color: '#e8722a',
      weight: 3,
      fillOpacity: 0.15,
    }).addTo(this.map);
    this.map.fitBounds(polygon.getBounds(), { padding: [30, 30] });
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
