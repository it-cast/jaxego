import { TestBed } from '@angular/core/testing';
import {
  provideHttpClient,
} from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { AreaConfigPage } from './area-config.page';
import { maskBrl, parseBrl } from '@jaxego/shared/util/money';

describe('money mask (br/brazilian-forms)', () => {
  it('masks raw digits into pt-BR R$ 0,00', () => {
    expect(maskBrl('800')).toBe('R$ 8,00');
    expect(maskBrl('1250')).toBe('R$ 12,50');
    expect(maskBrl('')).toBe('');
  });

  it('parses a masked value back into reais', () => {
    expect(parseBrl('R$ 8,00')).toBe(8);
    expect(parseBrl('R$ 1.234,56')).toBe(1234.56);
  });
});

describe('AreaConfigPage', () => {
  function build(): AreaConfigPage {
    TestBed.configureTestingModule({
      imports: [AreaConfigPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return TestBed.createComponent(AreaConfigPage).componentInstance;
  }

  it('reports a range error for geofence out of 30..300', () => {
    const page = build() as unknown as {
      form: { controls: Record<string, { setValue: (v: number) => void; markAsTouched: () => void }> };
      rangeError: (k: string) => string | null;
    };
    page.form.controls['geofence_m'].setValue(10);
    page.form.controls['geofence_m'].markAsTouched();
    expect(page.rangeError('geofence_m')).toContain('30 e 300');
  });

  it('has no range error for a valid geofence', () => {
    const page = build() as unknown as {
      form: { controls: Record<string, { setValue: (v: number) => void; markAsTouched: () => void }> };
      rangeError: (k: string) => string | null;
    };
    page.form.controls['geofence_m'].setValue(80);
    page.form.controls['geofence_m'].markAsTouched();
    expect(page.rangeError('geofence_m')).toBeNull();
  });
});
