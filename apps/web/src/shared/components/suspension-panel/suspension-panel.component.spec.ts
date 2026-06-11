import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  SuspensionPanelComponent,
  type SuspensionAppeal,
} from './suspension-panel.component';

function makeAppeal(overrides: Partial<SuspensionAppeal> = {}): SuspensionAppeal {
  return {
    id: 1,
    subject_type: 'courier',
    subject_id: 10,
    reason: 'Reclamações recorrentes de atraso.',
    opened_at: '2026-06-10T12:00:00Z',
    sla_due_at: '2026-06-13T12:00:00Z',
    decision: null,
    decided_at: null,
    reverted_at: null,
    ...overrides,
  };
}

describe('SuspensionPanelComponent', () => {
  let fixture: ComponentFixture<SuspensionPanelComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [SuspensionPanelComponent] });
    fixture = TestBed.createComponent(SuspensionPanelComponent);
  });

  it('shows the motivo (suspension is never silent — D-04)', () => {
    fixture.componentInstance.appeal = makeAppeal();
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Reclamações recorrentes de atraso.');
  });

  it('renders a live SLA countdown with aria-live for an open appeal', () => {
    const future = new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString();
    fixture.componentInstance.appeal = makeAppeal({ sla_due_at: future });
    fixture.detectChanges();
    const sla = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-suspension-panel__sla',
    );
    expect(sla?.getAttribute('aria-live')).toBe('polite');
    expect(sla?.textContent).toContain('Tempo restante');
  });

  it('marks the SLA as overdue when the deadline has passed', () => {
    const past = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    fixture.componentInstance.appeal = makeAppeal({ sla_due_at: past });
    fixture.detectChanges();
    const sla = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-suspension-panel__sla',
    );
    expect(sla?.classList.contains('jx-suspension-panel__sla--overdue')).toBe(true);
    expect(sla?.textContent).toContain('revertida automaticamente');
  });

  it('emits the decision when the admin acts', () => {
    fixture.componentInstance.appeal = makeAppeal();
    fixture.detectChanges();
    const emitted: string[] = [];
    fixture.componentInstance.decide.subscribe((d: string) => {
      emitted.push(d);
    });
    const revert = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-suspension-panel__btn--revert',
    ) as HTMLButtonElement;
    revert.click();
    expect(emitted).toEqual(['overturned']);
  });

  it('hides the actions and shows a resolved note once reverted', () => {
    fixture.componentInstance.appeal = makeAppeal({
      reverted_at: '2026-06-13T12:00:00Z',
    });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector(
        '.jx-suspension-panel__actions',
      ),
    ).toBeNull();
    const note = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-suspension-panel__resolved-note',
    );
    expect(note?.textContent).toContain('revertida');
  });

  it('shows "mantida" when the appeal was upheld', () => {
    fixture.componentInstance.appeal = makeAppeal({
      decision: 'upheld',
      decided_at: '2026-06-12T12:00:00Z',
    });
    fixture.detectChanges();
    const status = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-suspension-panel__status',
    );
    expect(status?.textContent).toContain('Mantida');
  });

  it('labels a merchant subject correctly', () => {
    fixture.componentInstance.appeal = makeAppeal({ subject_type: 'merchant' });
    fixture.detectChanges();
    const title = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-suspension-panel__title',
    );
    expect(title?.textContent).toContain('Lojista');
  });
});
