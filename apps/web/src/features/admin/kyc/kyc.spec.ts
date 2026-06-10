import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  KycQueueRow,
  KycQueueTableComponent,
} from './queue-table.component';
import { KycReviewRowComponent } from './review-row.component';

const ROWS: KycQueueRow[] = [
  {
    courierId: 'cou_aaa',
    courierName: 'Ana',
    level: 'completa',
    approvedCount: 1,
    totalCount: 4,
    waitingHours: 5,
  },
  {
    courierId: 'cou_bbb',
    courierName: 'Bruno',
    level: 'simples',
    approvedCount: 0,
    totalCount: 1,
    waitingHours: 53,
  },
];

describe('KycQueueTableComponent', () => {
  let fixture: ComponentFixture<KycQueueTableComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [KycQueueTableComponent] });
    fixture = TestBed.createComponent(KycQueueTableComponent);
  });

  it('renders an empty state (no false CTA) when the queue is empty', () => {
    fixture.componentInstance.rows = [];
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Nenhum entregador na fila');
    expect(fixture.nativeElement.querySelector('jx-empty-state')).toBeTruthy();
  });

  it('flags a ≥48h courier with text + icon (E5, not colour alone)', () => {
    fixture.componentInstance.rows = ROWS;
    fixture.detectChanges();
    const late = fixture.nativeElement.querySelector('.jx-kyc-queue__late');
    expect(late).toBeTruthy();
    expect(late.textContent).toContain('Atrasada');
  });

  it('uses a semantic table with sortable "waiting" column (aria-sort)', () => {
    fixture.componentInstance.rows = ROWS;
    fixture.detectChanges();
    const sortable = fixture.nativeElement.querySelector('th[aria-sort]');
    expect(sortable).toBeTruthy();
    expect(['ascending', 'descending']).toContain(sortable.getAttribute('aria-sort'));
  });

  it('does not show CPF in the queue (only the cou_ id)', () => {
    fixture.componentInstance.rows = ROWS;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('cou_aaa');
    expect(fixture.nativeElement.textContent).not.toContain('.***.***-');
  });
});

describe('KycReviewRowComponent', () => {
  let fixture: ComponentFixture<KycReviewRowComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [KycReviewRowComponent] });
    fixture = TestBed.createComponent(KycReviewRowComponent);
    fixture.componentInstance.title = 'CNH com EAR';
  });

  it('blocks reject without a reason (error-ux)', () => {
    fixture.detectChanges();
    // Open the reject form.
    const rejectBtn: HTMLButtonElement = fixture.nativeElement.querySelector(
      '.jx-review__btn--reject'
    );
    rejectBtn.click();
    fixture.detectChanges();
    // Confirm without selecting a reason → blocked, alert shown, no emit.
    const spy = jasmine.createSpy('decide');
    fixture.componentInstance.decide.subscribe(spy);
    const confirm: HTMLButtonElement = [
      ...fixture.nativeElement.querySelectorAll('.jx-review__btn--reject'),
    ].at(-1);
    confirm.click();
    fixture.detectChanges();
    expect(spy).not.toHaveBeenCalled();
    const alert = fixture.nativeElement.querySelector('[role="alert"]');
    expect(alert.textContent).toContain('Selecione o motivo');
  });

  it('emits an approve decision', () => {
    const spy = jasmine.createSpy('decide');
    fixture.componentInstance.decide.subscribe(spy);
    fixture.detectChanges();
    const approve: HTMLButtonElement = fixture.nativeElement.querySelector(
      '.jx-review__btn--approve'
    );
    approve.click();
    expect(spy).toHaveBeenCalledWith({ action: 'approve' });
  });

  it('auto-approved (MEI) item shows no action buttons', () => {
    fixture.componentInstance.status = 'approved_auto';
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Aprovado (automático)');
    expect(fixture.nativeElement.querySelector('.jx-review__btn--approve')).toBeFalsy();
  });
});
