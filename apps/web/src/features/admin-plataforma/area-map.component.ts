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

export interface AreaMapDraft {
  id: string;
  name: string;
  boundary: any;
  color: string;
}

/**
 * Mapa de polígono (Leaflet + leaflet-draw). Dois modos:
 *
 * - **Single** (padrão, usado em "editar zona"): `[boundary]`/`(boundaryChange)`,
 *   um polígono editável, comportamento inalterado desde antes do CORRECAO-261.
 * - **Multi** (`[multiMode]=true`, usado no fluxo de adicionar/editar zonas em
 *   massa): mostra `drafts` — zonas novas E zonas já cadastradas sendo
 *   editadas juntas nesta sessão, cada uma com sua cor. Só o draft com
 *   id === `activeDraftId` é editável por vez; os demais ficam como camada de
 *   referência, fora do featureGroup editável do leaflet-draw.
 *   `(draftBoundaryChange)` emite `{id, boundary}` toda vez que o polígono do
 *   draft ativo muda.
 */
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

  // Modo single (compatibilidade — "editar zona").
  @Input() boundary: any = null;
  @Output() boundaryChange = new EventEmitter<any>();

  // Modo multi (adicionar/editar zonas em massa — CORRECAO-261).
  @Input() multiMode = false;
  @Input() drafts: AreaMapDraft[] = [];
  @Input() activeDraftId: string | null = null;
  @Output() draftBoundaryChange = new EventEmitter<{ id: string; boundary: any }>();

  private map: any = null;
  /** Camada editável pelo leaflet-draw — o polígono único (single) ou só o draft ativo (multi). */
  private drawnItems: any = null;
  /** Multi mode apenas: zonas existentes + drafts inativos, só visuais, sem interação. */
  private referenceItems: any = null;
  private loaded = false;

  async ngAfterViewInit(): Promise<void> {
    await this.loadLeaflet();
    this.initMap();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.loaded || !this.map) return;
    if (this.multiMode) {
      if (changes['drafts'] || changes['activeDraftId']) {
        this.redrawMulti();
      }
    } else if (changes['boundary']) {
      this.drawSingle();
    }
  }

  ngOnDestroy(): void {
    if (this.map) this.map.remove();
  }

  private async loadLeaflet(): Promise<void> {
    if (!(window as any).L) {
      await this.loadCss('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css');
      await this.loadScript('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js');
    }
    if (!(window as any).L?.Control?.Draw) {
      await this.loadCss('https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css');
      await this.loadScript('https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js');
    }
  }

  private initMap(): void {
    const firstBoundary = this.multiMode
      ? this.drafts.find((d) => d.boundary)?.boundary
      : this.boundary;
    const center = firstBoundary?.coordinates?.[0]?.[0]
      ? [firstBoundary.coordinates[0][0][1], firstBoundary.coordinates[0][0][0]]
      : [-21.54, -42.05];

    this.map = L.map(this.mapEl.nativeElement).setView(center, 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
      maxZoom: 19,
    }).addTo(this.map);

    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);
    this.referenceItems = new L.FeatureGroup();
    this.map.addLayer(this.referenceItems);

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
      if (this.multiMode && !this.activeDraftId) return; // sem linha ativa — ignora
      this.drawnItems.clearLayers();
      this.drawnItems.addLayer(e.layer);
      this.emitBoundary();
    });
    this.map.on(L.Draw.Event.EDITED, () => this.emitBoundary());
    this.map.on(L.Draw.Event.DELETED, () => this.emitBoundary());

    this.loaded = true;
    if (this.multiMode) this.redrawMulti();
    else this.drawSingle();
  }

  private emitBoundary(): void {
    const layers = this.drawnItems.getLayers();
    const boundary = layers.length ? this.layerToGeoJson(layers[0]) : null;
    if (this.multiMode) {
      if (this.activeDraftId) this.draftBoundaryChange.emit({ id: this.activeDraftId, boundary });
    } else {
      this.boundaryChange.emit(boundary);
    }
  }

  private layerToGeoJson(layer: any): any {
    const latlngs = layer.getLatLngs()[0];
    const coordinates = [latlngs.map((ll: any) => [ll.lng, ll.lat])];
    coordinates[0].push(coordinates[0][0]);
    return { type: 'Polygon', coordinates };
  }

  private geoJsonToLayer(boundary: any, style: object): any {
    const coords = boundary.coordinates[0].map((c: number[]) => [c[1], c[0]]);
    return L.polygon(coords, style);
  }

  private drawSingle(): void {
    if (!this.drawnItems || !this.boundary?.coordinates) return;
    this.drawnItems.clearLayers();
    const polygon = this.geoJsonToLayer(this.boundary, { color: '#e8722a', weight: 3, fillOpacity: 0.15 });
    this.drawnItems.addLayer(polygon);
    this.map.fitBounds(polygon.getBounds(), { padding: [30, 30] });
  }

  private redrawMulti(): void {
    if (!this.referenceItems || !this.drawnItems) return;
    this.referenceItems.clearLayers();
    this.drawnItems.clearLayers();
    let combined: any = null;
    const extend = (bounds: any) => {
      combined = combined ? combined.extend(bounds) : bounds;
    };

    for (const d of this.drafts) {
      if (!d.boundary?.coordinates) continue;
      const isActive = d.id === this.activeDraftId;
      const layer = this.geoJsonToLayer(d.boundary, {
        color: d.color,
        weight: 3,
        fillOpacity: isActive ? 0.25 : 0.12,
      });
      layer.bindTooltip(d.name || '(sem nome)', { direction: 'center' });
      (isActive ? this.drawnItems : this.referenceItems).addLayer(layer);
      extend(layer.getBounds());
    }

    if (combined) this.map.fitBounds(combined, { padding: [30, 30] });
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
