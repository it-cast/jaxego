import { ComponentFixture, TestBed } from '@angular/core/testing';
import { KycReviewRowComponent } from './review-row.component';

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
