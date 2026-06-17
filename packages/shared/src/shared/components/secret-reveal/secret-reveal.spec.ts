import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SecretRevealComponent } from './secret-reveal.component';

describe('SecretRevealComponent (jx-secret-reveal)', () => {
  let fixture: ComponentFixture<SecretRevealComponent>;
  let component: SecretRevealComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SecretRevealComponent],
    }).compileComponents();
    fixture = TestBed.createComponent(SecretRevealComponent);
    component = fixture.componentInstance;
    component.secret = 'jxg_abc123_supersecretvalue';
    fixture.detectChanges();
  });

  function el(selector: string): HTMLElement {
    return fixture.nativeElement.querySelector(selector) as HTMLElement;
  }

  it('shows the full secret in a mono field', () => {
    const value = el('.jx-secret-reveal__value');
    expect(value.textContent?.trim()).toBe('jxg_abc123_supersecretvalue');
  });

  it('keeps a permanent warning in an aria-live region', () => {
    const warning = el('.jx-secret-reveal__warning');
    expect(warning.getAttribute('aria-live')).toBe('polite');
    expect(warning.textContent?.toLowerCase()).toContain('única vez');
  });

  it('copies to the clipboard and shows "Copiado" feedback', async () => {
    const writeText = jasmine
      .createSpy('writeText')
      .and.returnValue(Promise.resolve());
    // Override the clipboard for the test (jsdom/Chrome headless may lack it).
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });

    const button = el('.jx-secret-reveal__copy');
    expect(button.textContent?.trim()).toBe('Copiar');

    button.click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(writeText).toHaveBeenCalledWith('jxg_abc123_supersecretvalue');
    expect(el('.jx-secret-reveal__copy').textContent?.trim()).toBe('Copiado');
  });

  it('falls back to execCommand when the Clipboard API is unavailable', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      value: undefined,
      configurable: true,
    });
    const exec = spyOn(document, 'execCommand').and.returnValue(true);

    el('.jx-secret-reveal__copy').click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(exec).toHaveBeenCalledWith('copy');
    expect(el('.jx-secret-reveal__copy').textContent?.trim()).toBe('Copiado');
  });

  it('does not flip to "Copiado" when the copy fails', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      value: undefined,
      configurable: true,
    });
    spyOn(document, 'execCommand').and.returnValue(false);

    el('.jx-secret-reveal__copy').click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(el('.jx-secret-reveal__copy').textContent?.trim()).toBe('Copiar');
  });

  it('focus() moves focus to the secret field (managed focus, a11y)', () => {
    component.focus();
    const value = el('.jx-secret-reveal__value');
    expect(document.activeElement).toBe(value);
  });

  it('uses a custom label when provided', () => {
    const fresh = TestBed.createComponent(SecretRevealComponent);
    fresh.componentInstance.secret = 'jxg_x_y';
    fresh.componentInstance.label = 'Segredo do webhook';
    fresh.detectChanges();
    const label = fresh.nativeElement.querySelector(
      '.jx-secret-reveal__label',
    ) as HTMLElement;
    expect(label.textContent?.trim()).toBe('Segredo do webhook');
  });
});
