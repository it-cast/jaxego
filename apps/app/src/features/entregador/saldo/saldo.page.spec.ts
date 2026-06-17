import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EntregadorSaldoPage } from './saldo.page';
import {
  Balance,
  ExtractEntry,
  SaldoService,
  WithdrawalHistoryRow,
  WithdrawalResult,
} from './saldo.service';

class MockSaldoService {
  balanceValue: Balance = { balance_cents: 12000, minimum_cents: 2000 };
  extractValue: ExtractEntry[] = [];
  historyValue: WithdrawalHistoryRow[] = [];
  lastRequested: { amount: number; key?: string } | null = null;
  withdrawalResult: WithdrawalResult = {
    id: 1,
    amount_cents: 12000,
    status: 'pending',
    transaction_id: null,
  };

  async balance(): Promise<Balance> {
    return this.balanceValue;
  }
  async extract(): Promise<ExtractEntry[]> {
    return this.extractValue;
  }
  async history(): Promise<WithdrawalHistoryRow[]> {
    return this.historyValue;
  }
  async requestWithdrawal(amount: number, key?: string): Promise<WithdrawalResult> {
    this.lastRequested = { amount, key };
    return this.withdrawalResult;
  }
}

async function setup(
  configure?: (svc: MockSaldoService) => void,
): Promise<{ fixture: ComponentFixture<EntregadorSaldoPage>; svc: MockSaldoService }> {
  const svc = new MockSaldoService();
  configure?.(svc);
  await TestBed.configureTestingModule({
    imports: [EntregadorSaldoPage],
    providers: [{ provide: SaldoService, useValue: svc }],
  }).compileComponents();
  const fixture = TestBed.createComponent(EntregadorSaldoPage);
  fixture.detectChanges();
  // Let the constructor's async loads settle.
  await fixture.whenStable();
  fixture.detectChanges();
  return { fixture, svc };
}

describe('EntregadorSaldoPage', () => {
  afterEach(() => TestBed.resetTestingModule());

  it('shows the balance in mono and cites the backend minimum (R$ 20,00)', async () => {
    const { fixture } = await setup();
    const text = (fixture.nativeElement.textContent ?? '').replace(/\s+/g, ' ');
    expect(text.replace(/ /g, ' ')).toContain('R$ 120,00');
    expect(text).toContain('Saque mínimo de');
    expect(text.replace(/ /g, ' ')).toContain('R$ 20,00');
  });

  it('renders the empty extract copy when there are no movements', async () => {
    const { fixture } = await setup((svc) => (svc.extractValue = []));
    const text = fixture.nativeElement.textContent ?? '';
    expect(text).toContain('Sem movimentações ainda');
  });

  it('blocks below-minimum with a semantic error in an aria-live region', async () => {
    const { fixture } = await setup(
      (svc) => (svc.balanceValue = { balance_cents: 1500, minimum_cents: 2000 }),
    );
    // The CTA is disabled when below the minimum (cannot withdraw).
    const cta = fixture.nativeElement.querySelector('.jx-saldo__cta');
    expect(cta.disabled).toBe(true);

    // Force the guard (e.g. programmatic) and assert the aria-live error renders.
    fixture.componentInstance['openConfirm']();
    fixture.detectChanges();
    const live = fixture.nativeElement.querySelector('[aria-live="assertive"]');
    expect(live.textContent).toContain('Saque mínimo de');
  });

  it('opens the sensitive confirmation modal with aria-modal when allowed', async () => {
    const { fixture } = await setup();
    fixture.nativeElement.querySelector('.jx-saldo__cta').click();
    fixture.detectChanges();
    const modal = fixture.nativeElement.querySelector('[role="dialog"]');
    expect(modal).toBeTruthy();
    expect(modal.getAttribute('aria-modal')).toBe('true');
  });

  it('requests a withdrawal of the full balance with an idempotency key', async () => {
    const { fixture, svc } = await setup();
    fixture.nativeElement.querySelector('.jx-saldo__cta').click();
    fixture.detectChanges();
    await fixture.componentInstance['confirmWithdrawal']();
    expect(svc.lastRequested?.amount).toBe(12000);
    expect(svc.lastRequested?.key).toBeTruthy();
  });
});
