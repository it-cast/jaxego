import { ComponentFixture, TestBed } from '@angular/core/testing';
import { OfferTimerComponent } from './offer-timer.component';

describe('OfferTimerComponent', () => {
  let fixture: ComponentFixture<OfferTimerComponent>;

  beforeEach(() => {
    fixture = TestBed.configureTestingModule({ imports: [OfferTimerComponent] }).createComponent(
      OfferTimerComponent,
    );
  });

  afterEach(() => {
    fixture.destroy();
  });

  it('renders the seconds as mono TEXT (not color-only — a11y)', () => {
    fixture.componentInstance.ttlTotalS = 20;
    fixture.componentInstance.ttlRemainingS = 16;
    fixture.detectChanges();
    const seconds = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-offer-timer__seconds',
    );
    expect(seconds?.textContent).toContain('16s');
  });

  it('reaches the urgent phase under ~25% remaining', () => {
    fixture.componentInstance.ttlTotalS = 20;
    fixture.componentInstance.ttlRemainingS = 3;
    fixture.detectChanges();
    const timer = (fixture.nativeElement as HTMLElement).querySelector('.jx-offer-timer');
    expect(timer?.classList).toContain('jx-offer-timer--urgent');
  });

  it('uses the attention phase between ~25% and ~50%', () => {
    fixture.componentInstance.ttlTotalS = 20;
    fixture.componentInstance.ttlRemainingS = 8;
    fixture.detectChanges();
    const timer = (fixture.nativeElement as HTMLElement).querySelector('.jx-offer-timer');
    expect(timer?.classList).toContain('jx-offer-timer--attention');
  });

  it('announces the opening milestone via a polite live region', () => {
    fixture.componentInstance.ttlTotalS = 20;
    fixture.componentInstance.ttlRemainingS = 18;
    fixture.detectChanges();
    const live = (fixture.nativeElement as HTMLElement).querySelector('[aria-live="polite"]');
    expect(live?.textContent).toContain('18 segundos para decidir');
  });
});
