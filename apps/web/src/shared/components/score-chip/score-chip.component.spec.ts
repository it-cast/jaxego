import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScoreChipComponent, type ScoreLevel } from './score-chip.component';

describe('ScoreChipComponent', () => {
  let fixture: ComponentFixture<ScoreChipComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ScoreChipComponent] });
    fixture = TestBed.createComponent(ScoreChipComponent);
  });

  const LEVELS: ScoreLevel[] = ['probation', 'bronze', 'prata', 'ouro', 'diamante'];

  it('renders the level as TEXT (never color-only — a11y)', () => {
    for (const level of LEVELS) {
      fixture.componentInstance.level = level;
      fixture.detectChanges();
      const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
      // Each level has a non-empty pt-BR label rendered in text.
      expect(text.trim().length).toBeGreaterThan(0);
    }
  });

  it('binds the color to the matching --score-* var (token, no hex)', () => {
    fixture.componentInstance.level = 'ouro';
    fixture.detectChanges();
    const chip = (fixture.nativeElement as HTMLElement).querySelector('.jx-score-chip')!;
    const styleVar = (chip as HTMLElement).style.getPropertyValue('--score-color');
    expect(styleVar).toContain('--score-ouro');
  });

  it('renders the numeric value in pt-BR (comma decimal)', () => {
    fixture.componentInstance.level = 'ouro';
    fixture.componentInstance.value = 87.4;
    fixture.detectChanges();
    const valueEl = (fixture.nativeElement as HTMLElement).querySelector('.jx-score-chip__value');
    expect(valueEl?.textContent).toContain('87,4');
  });

  it('omits the value element when no score is given', () => {
    fixture.componentInstance.level = 'prata';
    fixture.componentInstance.value = null;
    fixture.detectChanges();
    const valueEl = (fixture.nativeElement as HTMLElement).querySelector('.jx-score-chip__value');
    expect(valueEl).toBeNull();
  });

  it('exposes an accessible label combining score + level', () => {
    fixture.componentInstance.level = 'diamante';
    fixture.componentInstance.value = 95;
    fixture.detectChanges();
    const chip = (fixture.nativeElement as HTMLElement).querySelector('.jx-score-chip')!;
    expect(chip.getAttribute('aria-label')).toContain('diamante');
    expect(chip.getAttribute('aria-label')).toContain('95');
  });
});
