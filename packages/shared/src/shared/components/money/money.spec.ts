import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MoneyComponent } from './money.component';

describe('MoneyComponent', () => {
  let fixture: ComponentFixture<MoneyComponent>;
  let component: MoneyComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [MoneyComponent] }).compileComponents();
    fixture = TestBed.createComponent(MoneyComponent);
    component = fixture.componentInstance;
  });

  function text(): string {
    return (fixture.nativeElement.textContent ?? '').replace(/\s+/g, ' ').trim();
  }

  /** Normalise the non-breaking space (U+00A0) that toLocaleString inserts. */
  function normSpace(s: string | null): string {
    return (s ?? '').replace(/\u00A0/g, ' ');
  }

  it('formats integer cents as pt-BR currency (cents→reais at the edge)', () => {
    component.cents = 9990;
    fixture.detectChanges();
    expect(normSpace(text())).toContain('R$ 99,90');
  });

  it('renders zero as R$ 0,00 (never blank)', () => {
    component.cents = 0;
    fixture.detectChanges();
    expect(normSpace(text())).toContain('R$ 0,00');
  });

  it('adds a textual + glyph for a credit (never colour-only)', () => {
    component.cents = 4500;
    component.sign = 'credit';
    fixture.detectChanges();
    const sign = fixture.nativeElement.querySelector('.jx-money__sign');
    expect(sign).toBeTruthy();
    expect(sign.textContent.trim()).toBe('+');
    expect(sign.getAttribute('aria-hidden')).toBe('true');
  });

  it('adds a textual − glyph for a debit', () => {
    component.cents = 2000;
    component.sign = 'debit';
    fixture.detectChanges();
    const sign = fixture.nativeElement.querySelector('.jx-money__sign');
    expect(sign.textContent.trim()).toBe('−');
  });

  it('exposes a descriptive aria-label when a label is given', () => {
    component.cents = 12000;
    component.label = 'Saldo disponível';
    fixture.detectChanges();
    const el = fixture.nativeElement.querySelector('.jx-money');
    expect(el.getAttribute('aria-label')).toContain('Saldo disponível');
    expect(normSpace(el.getAttribute('aria-label'))).toContain('R$ 120,00');
  });

  it('announces the sign in words in the aria-label for ledger rows', () => {
    component.cents = 4500;
    component.sign = 'credit';
    component.label = 'Corrida';
    fixture.detectChanges();
    const el = fixture.nativeElement.querySelector('.jx-money');
    expect(el.getAttribute('aria-label')).toContain('mais');
  });
});
