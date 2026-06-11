import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  InvoiceSummary,
  InvoiceSummaryComponent,
} from './invoice-summary.component';

const OPEN: InvoiceSummary = {
  id: 1,
  competence: '2026-05',
  amount_cents: 24500,
  status: 'open',
  due_at: '2026-06-10T00:00:00Z',
};

describe('InvoiceSummaryComponent', () => {
  let fixture: ComponentFixture<InvoiceSummaryComponent>;
  let component: InvoiceSummaryComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InvoiceSummaryComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(InvoiceSummaryComponent);
    component = fixture.componentInstance;
  });

  function text(): string {
    return (fixture.nativeElement.textContent ?? '').replace(/\s+/g, ' ').trim();
  }

  it('renders a human pt-BR competence label (month + year)', () => {
    component.invoice = OPEN;
    fixture.detectChanges();
    expect(text()).toContain('maio de 2026');
  });

  it('renders the total via jx-money (mono, formatted at the edge)', () => {
    component.invoice = OPEN;
    fixture.detectChanges();
    expect(text().replace(/ /g, ' ')).toContain('R$ 245,00');
  });

  it('shows the due date copy for an open invoice', () => {
    component.invoice = OPEN;
    fixture.detectChanges();
    expect(text()).toContain('Vence em');
  });

  it('carries the status as text + icon, not colour alone (em aberto)', () => {
    component.invoice = OPEN;
    fixture.detectChanges();
    const badge = fixture.nativeElement.querySelector('.jx-inv__badge');
    expect(badge.textContent).toContain('Em aberto');
    const icon = badge.querySelector('.jx-inv__badge-icon');
    expect(icon.getAttribute('aria-hidden')).toBe('true');
  });

  it('labels an overdue invoice "Vencida"', () => {
    component.invoice = { ...OPEN, status: 'overdue' };
    fixture.detectChanges();
    expect(text()).toContain('Vencida');
  });

  it('emits the invoice id when paying', () => {
    component.invoice = OPEN;
    fixture.detectChanges();
    let emitted: number | null = null;
    component.pay.subscribe((id) => (emitted = id));
    fixture.nativeElement.querySelector('.jx-inv__cta').click();
    expect(emitted).toBe(1);
  });

  it('hides the pay CTA for a paid invoice and shows the paid date', () => {
    component.invoice = {
      ...OPEN,
      status: 'paid',
      paid_at: '2026-04-02T12:00:00Z',
    };
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.jx-inv__cta')).toBeNull();
    expect(text()).toContain('Paga em');
  });

  it('disables the CTA while paying', () => {
    component.invoice = OPEN;
    component.paying = true;
    fixture.detectChanges();
    const cta = fixture.nativeElement.querySelector('.jx-inv__cta');
    expect(cta.disabled).toBe(true);
    expect(cta.getAttribute('aria-busy')).toBe('true');
  });
});
