import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StateBadgeComponent } from './state-badge.component';

describe('StateBadgeComponent', () => {
  let fixture: ComponentFixture<StateBadgeComponent>;
  let component: StateBadgeComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [StateBadgeComponent] }).compileComponents();
    fixture = TestBed.createComponent(StateBadgeComponent);
    component = fixture.componentInstance;
  });

  function text(): string {
    return (fixture.nativeElement.textContent ?? '').trim();
  }

  it('renders text + icon (never color-only) for CRIADA', () => {
    component.state = 'CRIADA';
    fixture.detectChanges();
    expect(text()).toContain('Procurando');
    const icon = fixture.nativeElement.querySelector('.jx-state-badge__icon');
    expect(icon).toBeTruthy();
    expect(icon.getAttribute('aria-hidden')).toBe('true');
  });

  it('switches label by variant but keeps the canonical state', () => {
    component.state = 'ACEITA';
    component.variant = 'list';
    fixture.detectChanges();
    expect(text()).toContain('Aceita');

    component.variant = 'dashboard';
    fixture.detectChanges();
    expect(text()).toContain('Indo coletar');
  });

  it('covers all 7 states with a label', () => {
    const states = [
      'CRIADA',
      'ACEITA',
      'COLETADA',
      'ENTREGUE',
      'RECUSADA_NO_DESTINO',
      'CANCELADA',
      'FINALIZADA',
    ] as const;
    for (const s of states) {
      component.state = s;
      fixture.detectChanges();
      expect(text().length).toBeGreaterThan(0);
    }
  });
});
