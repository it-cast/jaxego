import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BlockedRowComponent } from './blocked-row.component';

describe('BlockedRowComponent', () => {
  let fixture: ComponentFixture<BlockedRowComponent>;

  beforeEach(() => {
    fixture = TestBed.configureTestingModule({
      imports: [BlockedRowComponent],
    }).createComponent(BlockedRowComponent);
    fixture.componentInstance.name = 'Caio Bloqueado';
  });

  it('renders the name and the PRIVATE reason (store-only, RN-014)', () => {
    fixture.componentInstance.blockedAt = '05/06';
    fixture.componentInstance.reason = 'atraso recorrente';
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Caio Bloqueado');
    expect(text).toContain('motivo (privado)');
    expect(text).toContain('atraso recorrente');
  });

  it('emits unblock when the action is tapped', () => {
    const spy = jasmine.createSpy('unblock');
    fixture.componentInstance.unblock.subscribe(spy);
    fixture.detectChanges();
    (fixture.nativeElement as HTMLElement)
      .querySelector<HTMLButtonElement>('.jx-blocked-row__unblock')!
      .click();
    expect(spy).toHaveBeenCalled();
  });

  it('omits the reason fragment when no reason is set', () => {
    fixture.componentInstance.reason = null;
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).not.toContain('motivo (privado)');
  });
});
