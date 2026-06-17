import { ComponentFixture, TestBed } from '@angular/core/testing';
import {
  ScoreBreakdownComponent,
  type ScoreComponent,
} from './score-breakdown.component';

const SAMPLE: ScoreComponent[] = [
  { component: 'acceptance', raw: 0.92, weight: 0.25, contribution: 23 },
  { component: 'punctuality', raw: 0.8, weight: 0.25, contribution: 20 },
  { component: 'ratings', raw: 0.9, weight: 0.15, contribution: 13.5 },
];

describe('ScoreBreakdownComponent', () => {
  let fixture: ComponentFixture<ScoreBreakdownComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ScoreBreakdownComponent] });
    fixture = TestBed.createComponent(ScoreBreakdownComponent);
  });

  it('renders one row per component with a pt-BR label', () => {
    fixture.componentInstance.components = SAMPLE;
    fixture.detectChanges();
    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll(
      'tbody tr',
    );
    expect(rows.length).toBe(3);
    const firstHeader = rows[0].querySelector('th[scope="row"]');
    expect(firstHeader?.textContent).toContain('Taxa de aceite');
  });

  it('renders raw and weight as percentages', () => {
    fixture.componentInstance.components = SAMPLE;
    fixture.detectChanges();
    const firstRow = (fixture.nativeElement as HTMLElement).querySelector(
      'tbody tr',
    )!;
    const cells = firstRow.querySelectorAll('td');
    expect(cells[0].textContent).toContain('92%');
    expect(cells[1].textContent).toContain('25%');
  });

  it('renders the contribution in pt-BR points (comma decimal)', () => {
    fixture.componentInstance.components = SAMPLE;
    fixture.detectChanges();
    const lastRow = (fixture.nativeElement as HTMLElement).querySelectorAll(
      'tbody tr',
    )[2];
    expect(lastRow.querySelector('.jx-score-breakdown__contrib')?.textContent).toContain(
      '13,5',
    );
  });

  it('renders a Total footer only when total is provided', () => {
    fixture.componentInstance.components = SAMPLE;
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('tfoot'),
    ).toBeNull();

    fixture.componentInstance.total = 87.4;
    fixture.detectChanges();
    const total = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-score-breakdown__total',
    );
    expect(total?.textContent).toContain('87,4');
  });

  it('always shows the "informativo no piloto" note (ADR-013 transparency)', () => {
    fixture.componentInstance.components = SAMPLE;
    fixture.detectChanges();
    const note = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-score-breakdown__note',
    );
    expect(note?.textContent).toContain('informativo no piloto');
  });

  it('tolerates an empty/null component list', () => {
    fixture.componentInstance.components = null;
    fixture.detectChanges();
    const rows = (fixture.nativeElement as HTMLElement).querySelectorAll(
      'tbody tr',
    );
    expect(rows.length).toBe(0);
  });
});
