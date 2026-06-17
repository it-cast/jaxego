import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GeofencePillComponent, GeofenceState } from './geofence-pill.component';

describe('GeofencePillComponent', () => {
  let fixture: ComponentFixture<GeofencePillComponent>;
  let component: GeofencePillComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [GeofencePillComponent] }).compileComponents();
    fixture = TestBed.createComponent(GeofencePillComponent);
    component = fixture.componentInstance;
  });

  function text(): string {
    return (fixture.nativeElement.textContent ?? '').trim();
  }

  it('renders text + icon (never color-only) for every state', () => {
    const states: GeofenceState[] = ['checking', 'ok', 'out', 'missing', 'low_confidence'];
    for (const s of states) {
      component.state = s;
      fixture.detectChanges();
      expect(text().length).toBeGreaterThan(0);
      const icon = fixture.nativeElement.querySelector('.jx-geofence-pill__icon');
      expect(icon.getAttribute('aria-hidden')).toBe('true');
    }
  });

  it('announces via aria-live', () => {
    component.state = 'ok';
    fixture.detectChanges();
    const pill = fixture.nativeElement.querySelector('.jx-geofence-pill');
    expect(pill.getAttribute('aria-live')).toBe('polite');
    expect(text()).toContain('no local');
  });
});
