import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FavoriteRowComponent } from './favorite-row.component';

describe('FavoriteRowComponent', () => {
  let fixture: ComponentFixture<FavoriteRowComponent>;

  beforeEach(() => {
    fixture = TestBed.configureTestingModule({
      imports: [FavoriteRowComponent],
    }).createComponent(FavoriteRowComponent);
    fixture.componentInstance.position = 1;
    fixture.componentInstance.name = 'Ana Favorita';
    fixture.componentInstance.scoreLevel = 'ouro';
  });

  it('renders the position (mono) + name + score chip', () => {
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.jx-favorite-row__pos')?.textContent).toContain('1·');
    expect(el.querySelector('.jx-favorite-row__name')?.textContent).toContain('Ana Favorita');
    expect(el.querySelector('jx-score-chip')).toBeTruthy();
  });

  it('disables move-up on the first row (aria-disabled, not drag)', () => {
    fixture.componentInstance.canMoveUp = false;
    fixture.detectChanges();
    const up = (fixture.nativeElement as HTMLElement).querySelector(
      '.jx-favorite-row__move',
    ) as HTMLButtonElement;
    expect(up.disabled).toBe(true);
    expect(up.getAttribute('aria-disabled')).toBe('true');
  });

  it('emits moveUp / moveDown / remove', () => {
    const up = jasmine.createSpy('up');
    const down = jasmine.createSpy('down');
    const remove = jasmine.createSpy('remove');
    fixture.componentInstance.moveUp.subscribe(up);
    fixture.componentInstance.moveDown.subscribe(down);
    fixture.componentInstance.remove.subscribe(remove);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const moves = el.querySelectorAll<HTMLButtonElement>('.jx-favorite-row__move');
    moves[0].click();
    moves[1].click();
    el.querySelector<HTMLButtonElement>('.jx-favorite-row__remove')!.click();
    expect(up).toHaveBeenCalled();
    expect(down).toHaveBeenCalled();
    expect(remove).toHaveBeenCalled();
  });
});
