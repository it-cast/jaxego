import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AcceptedCourierCardComponent } from './accepted-courier-card.component';

describe('AcceptedCourierCardComponent', () => {
  let fixture: ComponentFixture<AcceptedCourierCardComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [AcceptedCourierCardComponent] });
    fixture = TestBed.createComponent(AcceptedCourierCardComponent);
  });

  it('renders the name, mono plate and ACEITA state badge', () => {
    fixture.componentInstance.name = 'Ana Silva';
    fixture.componentInstance.plate = 'ABC1D23';
    fixture.componentInstance.scoreLevel = 'ouro';
    fixture.componentInstance.scoreValue = 87;
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.jx-accepted-card__name')?.textContent).toContain('Ana Silva');
    expect(el.querySelector('.jx-accepted-card__plate')?.textContent).toContain('ABC1D23');
    // State badge reused (jx-state-badge renders ACEITA).
    expect(el.querySelector('jx-state-badge')).toBeTruthy();
    expect(el.querySelector('jx-score-chip')).toBeTruthy();
  });

  it('falls back to initials when there is no photo (no location ever — TH-3)', () => {
    fixture.componentInstance.name = 'João Pedro';
    fixture.componentInstance.photoUrl = null;
    fixture.detectChanges();
    const initials = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-accepted-card__initials',
    );
    expect(initials?.textContent?.trim()).toBe('JP');
    // No location is ever rendered for the store (ADR-007 / TH-3).
    expect((fixture.nativeElement as HTMLElement).textContent).not.toContain('lat');
  });

  it('shows the photo when provided', () => {
    fixture.componentInstance.name = 'Maria';
    fixture.componentInstance.photoUrl = 'https://example/photo.webp';
    fixture.detectChanges();
    const img = (fixture.nativeElement as HTMLElement).querySelector(
      'img.jx-accepted-card__photo',
    ) as HTMLImageElement | null;
    expect(img?.src).toContain('photo.webp');
  });
});
