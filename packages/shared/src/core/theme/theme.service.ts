import { Injectable, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'jx-theme';
const DARK_QUERY = '(prefers-color-scheme: dark)';

/**
 * ThemeService — single source of truth for the active theme after bootstrap.
 *
 * The anti-FOUC inline script in index.html already applied `data-theme` before
 * the first paint (UI-SPEC §1.2). This service reads that same attribute /
 * localStorage key and keeps a signal in sync, so toggling never re-flashes.
 *
 * Precedence (matches the inline script): localStorage -> prefers-color-scheme
 * -> light. A manual toggle persists the choice; without a stored choice the
 * system preference is followed live.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly _theme = signal<Theme>(this.resolveInitial());

  /** Reactive current theme. */
  readonly theme = this._theme.asReadonly();

  constructor() {
    // Apply once so the signal and the DOM attribute are guaranteed in sync.
    this.apply(this._theme());
    this.watchSystemPreference();
  }

  /** Whether the user has an explicit stored choice (vs. following system). */
  hasStoredChoice(): boolean {
    return this.readStored() !== null;
  }

  set(theme: Theme): void {
    this._theme.set(theme);
    this.apply(theme);
    this.persist(theme);
  }

  toggle(): void {
    this.set(this._theme() === 'dark' ? 'light' : 'dark');
  }

  // --- internals ----------------------------------------------------------

  private resolveInitial(): Theme {
    const stored = this.readStored();
    if (stored) return stored;
    // Trust the attribute the inline script already set, else system, else light.
    const attr = document.documentElement.getAttribute('data-theme');
    if (attr === 'light' || attr === 'dark') return attr;
    return this.systemPrefersDark() ? 'dark' : 'light';
  }

  private readStored(): Theme | null {
    try {
      const v = localStorage.getItem(STORAGE_KEY);
      return v === 'light' || v === 'dark' ? v : null;
    } catch {
      return null;
    }
  }

  private persist(theme: Theme): void {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Storage unavailable (private mode); in-memory signal still works.
    }
  }

  private apply(theme: Theme): void {
    document.documentElement.setAttribute('data-theme', theme);
  }

  private systemPrefersDark(): boolean {
    try {
      return matchMedia(DARK_QUERY).matches;
    } catch {
      return false;
    }
  }

  private watchSystemPreference(): void {
    try {
      const mq = matchMedia(DARK_QUERY);
      mq.addEventListener('change', (e) => {
        // Only follow the system live when the user has no explicit choice.
        if (!this.hasStoredChoice()) {
          const next: Theme = e.matches ? 'dark' : 'light';
          this._theme.set(next);
          this.apply(next);
        }
      });
    } catch {
      // matchMedia unavailable — ignore.
    }
  }
}
