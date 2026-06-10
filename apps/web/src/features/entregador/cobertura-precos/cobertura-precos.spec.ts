import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { CoberturaPrecosPage } from './cobertura-precos.page';
import type { CoverageItem } from './coverage-list.component';

interface PageInternals {
  pisoEntrega: number;
  pisoKm: number;
  mode: { set: (m: 'neighborhood' | 'km') => void };
  items: { set: (i: CoverageItem[]) => void; (): CoverageItem[] };
  saveError: () => string | null;
  save: () => Promise<void>;
  warnMessage: string;
}

describe('CoberturaPrecosPage — floor validation (RN-015)', () => {
  function build(): PageInternals {
    TestBed.configureTestingModule({
      imports: [CoberturaPrecosPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return TestBed.createComponent(CoberturaPrecosPage)
      .componentInstance as unknown as PageInternals;
  }

  it('blocks save and cites the floor when a price is below it', async () => {
    const page = build();
    page.pisoEntrega = 8;
    page.mode.set('neighborhood');
    page.items.set([
      { neighborhoodId: 1, name: 'Centro', covered: true, excluded: false, price: 'R$ 5,00' },
    ]);
    await page.save();
    expect(page.saveError()).toContain('abaixo do piso');
    // The blocked item carries an inline error that cites the floor (R$ 8,00).
    const item = page.items()[0];
    expect(item.priceError).toContain('R$ 8,00');
  });

  it('the RN-003 warn message cites the floor (never hardcoded)', () => {
    const page = build();
    page.pisoEntrega = 8;
    page.mode.set('neighborhood');
    expect(page.warnMessage).toContain('R$ 8,00');
    expect(page.warnMessage).toContain('coleta');
  });
});
