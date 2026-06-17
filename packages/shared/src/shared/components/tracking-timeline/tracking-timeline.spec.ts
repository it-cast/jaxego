import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TrackingTimelineComponent } from './tracking-timeline.component';

describe('TrackingTimelineComponent', () => {
  let fixture: ComponentFixture<TrackingTimelineComponent>;
  let component: TrackingTimelineComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TrackingTimelineComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(TrackingTimelineComponent);
    component = fixture.componentInstance;
  });

  it('marks the current step distinctly (shape + class, not color-only)', () => {
    component.state = 'COLETADA';
    component.entries = [
      { state: 'CRIADA', at: '2026-06-10T10:00:00Z' },
      { state: 'ACEITA', at: '2026-06-10T10:05:00Z' },
      { state: 'COLETADA', at: '2026-06-10T10:20:00Z' },
    ];
    fixture.detectChanges();
    const current = fixture.nativeElement.querySelector('.jx-timeline__step--current');
    expect(current).toBeTruthy();
    expect(current.getAttribute('aria-current')).toBe('step');
    const done = fixture.nativeElement.querySelectorAll('.jx-timeline__step--done');
    expect(done.length).toBe(2); // CRIADA + ACEITA
  });

  it('diverts the tail for a terminal refusal state', () => {
    component.state = 'RECUSADA_NO_DESTINO';
    component.entries = [
      { state: 'CRIADA', at: null },
      { state: 'ACEITA', at: null },
      { state: 'COLETADA', at: null },
      { state: 'RECUSADA_NO_DESTINO', at: null },
    ];
    fixture.detectChanges();
    const text = (fixture.nativeElement.textContent ?? '').toLowerCase();
    expect(text).toContain('não foi possível entregar');
    // ENTREGUE/FINALIZADA are not shown on the refused path.
    expect(text).not.toContain('concluído');
  });
});
