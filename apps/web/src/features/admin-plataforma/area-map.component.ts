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
import { loadLeaflet, loadLeafletDraw } from '@jaxego/core/map/leaflet-loader';
import { MAP_DEFAULT_CENTER } from '@jaxego/core/map/map-tiles';
import {
  activeZoneStyle,
  brandTileLayer,
  onThemeChange,
  readMapPalette,
  referenceZoneStyle,
} from '@jaxego/core/map/map-theme';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let L: any;

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
 *
 * Redesign v3 (REDESIGN-v3.md §7): cores lidas dos tokens (`--map-*`) em
 * runtime, tiles temáticos, legenda sobreposta, altura responsiva; o desenho é
 * re-estilizado quando o tema muda.
 */
@Component({
  selector: 'jx-area-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-area-map-frame">
      <div #mapEl class="jx-area-map" role="application" aria-label="Mapa de zonas — desenhe o polígono com a ferramenta de desenho"></div>
      <div class="jx-area-map__legend" aria-hidden="true">
        @if (readonly) {
          @for (d of drafts; track d.id) {
            <span class="jx-area-map__legend-item">
              <span class="jx-area-map__swatch" [style.border-color]="d.color"></span>{{ d.name || '(sem nome)' }}
            </span>
          }
        } @else if (multiMode) {
          <span class="jx-area-map__legend-item"><span class="jx-area-map__swatch jx-area-map__swatch--active"></span>Em edição</span>
          <span class="jx-area-map__legend-item"><span class="jx-area-map__swatch jx-area-map__swatch--ref"></span>Demais zonas</span>
        } @else {
          <span class="jx-area-map__legend-item"><span class="jx-area-map__swatch jx-area-map__swatch--active"></span>Zona</span>
        }
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .jx-area-map-frame {
      position: relative;
      border-radius: var(--jx-radius-xl);
      overflow: hidden;
      border: 1px solid var(--border);
      box-shadow: var(--shadow-sm);
      background: var(--surface-sunken);
      isolation: isolate;
    }
    .jx-area-map { width: 100%; height: var(--jx-area-map-height, clamp(360px, 58vh, 620px)); }
    .jx-area-map__legend {
      position: absolute; left: var(--jx-space-3); bottom: var(--jx-space-3); z-index: 500;
      display: flex; flex-wrap: wrap; gap: var(--jx-space-1) var(--jx-space-3);
      max-width: calc(100% - 80px);
      padding: 6px 12px; border-radius: var(--jx-radius-full);
      background: var(--topbar-bg); backdrop-filter: blur(10px);
      border: 1px solid var(--border); box-shadow: var(--shadow-md);
      font-size: var(--jx-text-xs); font-weight: var(--jx-weight-semibold); color: var(--text);
    }
    .jx-area-map__legend-item { display: inline-flex; align-items: center; gap: 6px; }
    .jx-area-map__swatch { width: 14px; height: 10px; border-radius: 3px; border: 2px solid var(--map-zone); background: var(--brand-wash); }
    .jx-area-map__swatch--ref { border-style: dashed; border-color: var(--map-zone-ref); background: transparent; }
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

  /** Visão geral somente leitura (redesign v3): todos os `drafts` coloridos, sem ferramenta de desenho. Implica multiMode. */
  @Input() readonly = false;

  private map: any = null;
  /** Camada editável pelo leaflet-draw — o polígono único (single) ou só o draft ativo (multi). */
  private drawnItems: any = null;
  /** Multi mode apenas: zonas existentes + drafts inativos, só visuais, sem interação. */
  private referenceItems: any = null;
  private loaded = false;
  private destroyed = false;
  private unwatchTheme: (() => void) | null = null;

  async ngAfterViewInit(): Promise<void> {
    if (this.readonly) this.multiMode = true;
    L = this.readonly ? await loadLeaflet() : await loadLeafletDraw();
    if (this.destroyed) return;
    this.initMap();
    // Polygons carry inline colors — repaint them when the theme flips.
    this.unwatchTheme = onThemeChange(() => this.redraw(false));
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
    this.destroyed = true;
    this.unwatchTheme?.();
    if (this.map) this.map.remove();
  }

  private redraw(fit: boolean): void {
    if (!this.loaded) return;
    if (this.multiMode) this.redrawMulti(fit);
    else this.drawSingle(fit);
  }

  private initMap(): void {
    const firstBoundary = this.multiMode
      ? this.drafts.find((d) => d.boundary)?.boundary
      : this.boundary;
    const center = firstBoundary?.coordinates?.[0]?.[0]
      ? [firstBoundary.coordinates[0][0][1], firstBoundary.coordinates[0][0][0]]
      : MAP_DEFAULT_CENTER;

    this.map = L.map(this.mapEl.nativeElement, { scrollWheelZoom: true }).setView(center, 13);
    brandTileLayer(L).addTo(this.map);

    this.drawnItems = new L.FeatureGroup();
    this.map.addLayer(this.drawnItems);
    this.referenceItems = new L.FeatureGroup();
    this.map.addLayer(this.referenceItems);

    this.loaded = true;
    if (this.readonly) {
      this.redraw(true);
      return;
    }

    const drawControl = new L.Control.Draw({
      draw: {
        polygon: { shapeOptions: activeZoneStyle(readMapPalette().zone), showArea: false },
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

    this.redraw(true);
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

  private drawSingle(fit = true): void {
    if (!this.drawnItems || !this.boundary?.coordinates) return;
    this.drawnItems.clearLayers();
    const polygon = this.geoJsonToLayer(this.boundary, activeZoneStyle(readMapPalette().zone));
    this.drawnItems.addLayer(polygon);
    if (fit) this.map.fitBounds(polygon.getBounds(), { padding: [30, 30] });
  }

  private redrawMulti(fit = true): void {
    if (!this.referenceItems || !this.drawnItems) return;
    this.referenceItems.clearLayers();
    this.drawnItems.clearLayers();
    let combined: any = null;
    const extend = (bounds: any) => {
      combined = combined ? combined.extend(bounds) : bounds;
    };

    for (const d of this.drafts) {
      if (!d.boundary?.coordinates) continue;
      const isActive = this.readonly || d.id === this.activeDraftId;
      const layer = this.geoJsonToLayer(
        d.boundary,
        isActive ? { ...activeZoneStyle(d.color), fillOpacity: this.readonly ? 0.2 : 0.26 } : referenceZoneStyle(d.color)
      );
      layer.bindTooltip(d.name || '(sem nome)', {
        direction: 'center',
        className: 'jx-map-tooltip',
        permanent: this.readonly,
      });
      (isActive ? this.drawnItems : this.referenceItems).addLayer(layer);
      extend(layer.getBounds());
    }

    if (combined && fit) this.map.fitBounds(combined, { padding: [30, 30] });
  }
}
