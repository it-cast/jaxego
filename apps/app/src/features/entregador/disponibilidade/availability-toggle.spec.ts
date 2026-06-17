import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AvailabilityToggleComponent } from './availability-toggle.component';

describe('AvailabilityToggleComponent', () => {
  let fixture: ComponentFixture<AvailabilityToggleComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [AvailabilityToggleComponent] });
    fixture = TestBed.createComponent(AvailabilityToggleComponent);
  });

  function el(): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  it('renders role=switch with aria-checked reflecting online', () => {
    fixture.componentInstance.isOnline = false;
    fixture.detectChanges();
    const sw = el().querySelector('[role="switch"]') as HTMLButtonElement;
    expect(sw.getAttribute('aria-checked')).toBe('false');
    expect(el().textContent).toContain('Offline');
  });

  it('toggles online and emits onlineChange', () => {
    const emitted: boolean[] = [];
    fixture.componentInstance.onlineChange.subscribe((v) => emitted.push(v));
    fixture.detectChanges();
    const sw = el().querySelector('[role="switch"]') as HTMLButtonElement;
    sw.click();
    fixture.detectChanges();
    expect(sw.getAttribute('aria-checked')).toBe('true');
    expect(el().textContent).toContain('Online');
    expect(emitted).toEqual([true]);
  });

  it('when disabled (non-active) shows the warn-banner and does not toggle', () => {
    fixture.componentInstance.disabled = true;
    fixture.detectChanges();
    expect(el().querySelector('jx-warn-banner')).toBeTruthy();
    const sw = el().querySelector('[role="switch"]') as HTMLButtonElement;
    sw.click();
    fixture.detectChanges();
    expect(sw.getAttribute('aria-checked')).toBe('false');
  });
});
