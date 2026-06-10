import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { NeighborhoodsPage } from './neighborhoods.page';

interface NbhdInternals {
  geojsonText: string;
  validateGeojson: () => unknown | null;
  geojsonError: () => string | null;
}

describe('NeighborhoodsPage — client GeoJSON validation (UX)', () => {
  function build(): NbhdInternals {
    TestBed.configureTestingModule({
      imports: [NeighborhoodsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return TestBed.createComponent(NeighborhoodsPage)
      .componentInstance as unknown as NbhdInternals;
  }

  it('accepts an empty polygon (name-only is valid)', () => {
    const page = build();
    page.geojsonText = '';
    expect(page.validateGeojson()).toBeNull();
    expect(page.geojsonError()).toBeNull();
  });

  it('accepts a valid Polygon', () => {
    const page = build();
    page.geojsonText = JSON.stringify({
      type: 'Polygon',
      coordinates: [
        [
          [-42.19, -21.82],
          [-42.17, -21.82],
          [-42.17, -21.8],
          [-42.19, -21.8],
          [-42.19, -21.82],
        ],
      ],
    });
    const parsed = page.validateGeojson();
    expect(parsed).toBeTruthy();
    expect(page.geojsonError()).toBeNull();
  });

  it('rejects malformed JSON', () => {
    const page = build();
    page.geojsonText = '{not json';
    expect(page.validateGeojson()).toBeUndefined();
    expect(page.geojsonError()).toContain('GeoJSON inválido');
  });

  it('rejects a non-Polygon type', () => {
    const page = build();
    page.geojsonText = JSON.stringify({ type: 'Point', coordinates: [0, 0] });
    expect(page.validateGeojson()).toBeUndefined();
    expect(page.geojsonError()).toContain('Polygon');
  });

  it('rejects out-of-range coordinates', () => {
    const page = build();
    page.geojsonText = JSON.stringify({
      type: 'Polygon',
      coordinates: [
        [
          [200, 0],
          [201, 0],
          [201, 1],
          [200, 1],
          [200, 0],
        ],
      ],
    });
    expect(page.validateGeojson()).toBeUndefined();
    expect(page.geojsonError()).toContain('fora de faixa');
  });
});
