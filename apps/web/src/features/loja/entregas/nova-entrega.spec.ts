import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { NovaEntregaPage } from './nova-entrega.page';

describe('NovaEntregaPage — F-03 form (UI-SPEC §2)', () => {
  function build(): { page: NovaEntregaPage; http: HttpTestingController } {
    TestBed.configureTestingModule({
      imports: [NovaEntregaPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    const fixture = TestBed.createComponent(NovaEntregaPage);
    const http = TestBed.inject(HttpTestingController);
    // The constructor fires GET /v1/neighborhoods/catalog — flush it.
    http.expectOne('/v1/neighborhoods/catalog').flush([{ id: 1, name: 'Centro' }]);
    return { page: fixture.componentInstance, http };
  }

  it('locks payment_method to direct (card/PIX are "em breve")', () => {
    const { page } = build();
    expect((page as unknown as { form: { value: { payment_method: string } } }).form.value
      .payment_method).toBe('direct');
  });

  it('masks the recipient phone as (DD) 9XXXX-XXXX', () => {
    const { page } = build();
    const form = (page as unknown as { form: { controls: Record<string, { value: string; setValue: (v: string) => void }> } }).form;
    form.controls['recipient_phone'].setValue('22988887777');
    expect(form.controls['recipient_phone'].value).toBe('(22) 98888-7777');
  });

  it('masks the CEP as 00000-000', () => {
    const { page } = build();
    const form = (page as unknown as { form: { controls: Record<string, { value: string; setValue: (v: string) => void }> } }).form;
    form.controls['cep'].setValue('28470000');
    expect(form.controls['cep'].value).toBe('28470-000');
  });

  it('blocks submit until the form is valid', () => {
    const { page } = build();
    expect((page as unknown as { canSubmit: () => boolean }).canSubmit()).toBe(false);
  });

  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
  });
});
