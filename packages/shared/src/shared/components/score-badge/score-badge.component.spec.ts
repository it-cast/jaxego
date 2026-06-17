import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ScoreBadgeComponent, type ScoreLevel } from './score-badge.component';

describe('ScoreBadgeComponent', () => {
  let fixture: ComponentFixture<ScoreBadgeComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [ScoreBadgeComponent] });
    fixture = TestBed.createComponent(ScoreBadgeComponent);
  });

  const LEVELS: ScoreLevel[] = ['probation', 'bronze', 'prata', 'ouro', 'diamante'];

  it('renders the level as TEXT for every level (never color-only — a11y)', () => {
    for (const level of LEVELS) {
      fixture.componentInstance.level = level;
      fixture.detectChanges();
      const levelEl = (fixture.nativeElement as HTMLElement).querySelector(
        '.jx-score-badge__level',
      );
      expect(levelEl?.textContent?.trim().length ?? 0).toBeGreaterThan(0);
    }
  });

  it('binds the color to the matching --score-* var (token, no hex)', () => {
    fixture.componentInstance.level = 'diamante';
    fixture.detectChanges();
    const badge = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-score-badge',
    )!;
    const styleVar = (badge as HTMLElement).style.getPropertyValue('--score-color');
    expect(styleVar).toContain('--score-diamante');
  });

  it('renders the numeric value in pt-BR (comma decimal)', () => {
    fixture.componentInstance.level = 'ouro';
    fixture.componentInstance.value = 78.6;
    fixture.detectChanges();
    const valueEl = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-score-badge__value',
    );
    expect(valueEl?.textContent).toContain('78,6');
  });

  it('omits the value element when no score is given', () => {
    fixture.componentInstance.level = 'prata';
    fixture.componentInstance.value = null;
    fixture.detectChanges();
    const valueEl = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-score-badge__value',
    );
    expect(valueEl).toBeNull();
  });

  it('exposes an accessible label combining score + level', () => {
    fixture.componentInstance.level = 'bronze';
    fixture.componentInstance.value = 42;
    fixture.detectChanges();
    const badge = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-score-badge',
    )!;
    expect(badge.getAttribute('aria-label')).toContain('Bronze');
    expect(badge.getAttribute('aria-label')).toContain('42');
  });

  it('applies the lg modifier when size is lg', () => {
    fixture.componentInstance.level = 'ouro';
    fixture.componentInstance.size = 'lg';
    fixture.detectChanges();
    const badge = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-score-badge',
    )!;
    expect(badge.classList.contains('jx-score-badge--lg')).toBe(true);
  });
});
