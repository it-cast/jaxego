import { ComponentFixture, TestBed } from '@angular/core/testing';
import { UpgradeModalComponent } from './upgrade-modal.component';
import { UPGRADE_PLANS } from './upgrade-modal.stories';

describe('UpgradeModalComponent', () => {
  let fixture: ComponentFixture<UpgradeModalComponent>;
  let component: UpgradeModalComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [UpgradeModalComponent] }).compileComponents();
    fixture = TestBed.createComponent(UpgradeModalComponent);
    component = fixture.componentInstance;
    component.plans = UPGRADE_PLANS;
    component.limit = 2;
    fixture.detectChanges();
  });

  it('renders an accessible dialog with a factual title', () => {
    const dialog = fixture.nativeElement.querySelector('[role="dialog"]');
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(fixture.nativeElement.textContent).toContain('Você usou suas 2 entregas do mês');
  });

  it('exposes an "Agora não" of equal weight (reachable button, not faded link)', () => {
    const later: HTMLButtonElement = fixture.nativeElement.querySelector('.jx-upgrade__later');
    expect(later).toBeTruthy();
    expect(later.textContent?.trim()).toBe('Agora não');
    expect(later.tagName).toBe('BUTTON');
  });

  it('emits dismiss on "Agora não"', () => {
    const spy = jasmine.createSpy('dismiss');
    component.dismiss.subscribe(spy);
    const later: HTMLButtonElement = fixture.nativeElement.querySelector('.jx-upgrade__later');
    later.click();
    expect(spy).toHaveBeenCalled();
  });

  it('emits dismiss on Escape', () => {
    const spy = jasmine.createSpy('dismiss');
    component.dismiss.subscribe(spy);
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(spy).toHaveBeenCalled();
  });

  it('renders the plan comparison data-driven (no hardcoded plan)', () => {
    const cards = fixture.nativeElement.querySelectorAll('jx-plan-card');
    expect(cards.length).toBe(UPGRADE_PLANS.length);
  });
});
