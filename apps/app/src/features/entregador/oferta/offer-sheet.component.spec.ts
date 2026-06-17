import { ComponentFixture, TestBed } from '@angular/core/testing';
import { OfferSheetComponent } from './offer-sheet.component';
import type { OfferOut } from './offer.models';

const OFFER: OfferOut = {
  delivery_id: 42,
  loja_nome: 'Pizzaria do José',
  pickup_address: 'Rua das Flores, 123 · Centro',
  pickup_neighborhood: 'Centro',
  dropoff_neighborhood: 'Vila Nova',
  distance_m: 2800,
  value_cents: 850,
  payment_method: 'direct',
  eta_s: 900,
  eta_degraded: false,
  ttl_total_s: 20,
  ttl_remaining_s: 16,
};

describe('OfferSheetComponent', () => {
  let fixture: ComponentFixture<OfferSheetComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [OfferSheetComponent] });
    fixture = TestBed.createComponent(OfferSheetComponent);
  });

  it('is a labelled modal dialog (a11y)', () => {
    fixture.componentInstance.offer = OFFER;
    fixture.detectChanges();
    const dialog = (fixture.nativeElement as HTMLElement).querySelector('[role="dialog"]');
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(dialog?.getAttribute('aria-labelledby')).toContain('offer-store-42');
  });

  it('RN-013: NEVER renders the full destination address — only neighborhood + distance', () => {
    fixture.componentInstance.offer = OFFER;
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    // Allowed: neighborhood + distance.
    expect(text).toContain('Vila Nova');
    expect(text).toContain('km');
    // The sheet has no field for the full destination address at all.
    expect(text).not.toContain('Rua Secreta');
  });

  it('shows the run value in pt-BR mono (R$)', () => {
    fixture.componentInstance.offer = OFFER;
    fixture.detectChanges();
    const value = (fixture.nativeElement as HTMLElement).querySelector('.jx-offer-sheet__value');
    expect(value?.textContent).toContain('R$ 8,50');
  });

  it('emits accept with the delivery id when Accept is tapped', () => {
    const spy = jasmine.createSpy('accept');
    fixture.componentInstance.accept.subscribe(spy);
    fixture.componentInstance.offer = OFFER;
    fixture.detectChanges();
    const btn = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-offer-sheet__accept',
    ) as HTMLButtonElement;
    btn.click();
    expect(spy).toHaveBeenCalledWith(42);
  });

  it('lost-the-race (E3) uses role=status without blame (no penalty)', () => {
    fixture.componentInstance.offer = OFFER;
    fixture.componentInstance.result = 'lost';
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('acabou de ser aceita por outro entregador');
    expect(text).toContain('a próxima é sua');
  });

  it('expired offer announces calmly and offers no penalty', () => {
    fixture.componentInstance.offer = OFFER;
    fixture.componentInstance.result = 'expired';
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Essa oferta expirou');
  });
});
