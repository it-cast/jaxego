import { TestBed } from '@angular/core/testing';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let store: Record<string, string>;

  function mockMatchMedia(prefersDark: boolean): void {
    spyOn(window, 'matchMedia').and.callFake(
      (query: string) =>
        ({
          matches: query.includes('dark') ? prefersDark : false,
          media: query,
          addEventListener: () => undefined,
          removeEventListener: () => undefined,
          addListener: () => undefined,
          removeListener: () => undefined,
          dispatchEvent: () => false,
          onchange: null,
        }) as unknown as MediaQueryList
    );
  }

  beforeEach(() => {
    store = {};
    spyOn(localStorage, 'getItem').and.callFake((k: string) => store[k] ?? null);
    spyOn(localStorage, 'setItem').and.callFake((k: string, v: string) => {
      store[k] = v;
    });
    document.documentElement.removeAttribute('data-theme');
  });

  function create(): ThemeService {
    TestBed.configureTestingModule({ providers: [ThemeService] });
    return TestBed.inject(ThemeService);
  }

  it('precedence: localStorage wins over system preference', () => {
    store['jx-theme'] = 'light';
    mockMatchMedia(true); // system says dark
    const svc = create();
    expect(svc.theme()).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('precedence: falls back to prefers-color-scheme when no stored choice', () => {
    mockMatchMedia(true);
    const svc = create();
    expect(svc.theme()).toBe('dark');
  });

  it('precedence: defaults to light when no choice and system is light', () => {
    mockMatchMedia(false);
    const svc = create();
    expect(svc.theme()).toBe('light');
  });

  it('toggle flips theme, applies attribute and persists', () => {
    mockMatchMedia(false);
    const svc = create();
    expect(svc.theme()).toBe('light');

    svc.toggle();
    expect(svc.theme()).toBe('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(store['jx-theme']).toBe('dark');

    svc.toggle();
    expect(svc.theme()).toBe('light');
    expect(store['jx-theme']).toBe('light');
  });

  it('set persists an explicit choice', () => {
    mockMatchMedia(false);
    const svc = create();
    svc.set('dark');
    expect(svc.hasStoredChoice()).toBeTrue();
    expect(store['jx-theme']).toBe('dark');
  });
});
