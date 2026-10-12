import {
  ChangeDetectionStrategy,
  Component,
  HostListener,
  computed,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import {
  faAnglesLeft,
  faAnglesRight,
  faBars,
  faMoon,
  faRightFromBracket,
  faSun,
  faXmark,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons';
import { ThemeService } from '@jaxego/core/theme/theme.service';

export interface ShellNavItem {
  path: string;
  label: string;
  icon: IconDefinition;
}

const COLLAPSE_KEY = 'jx-nav-collapsed';

/**
 * jx-app-shell — shell web unificado (redesign v3, REDESIGN-v3.md §6.1).
 *
 * Serve loja, admin de área, equipe e plataforma: cada shell de perfil vira um
 * wrapper fino que só informa a navegação e o contexto. Sidebar azul-noite
 * (âncora de confiança, nos dois temas), item ativo em gradiente tangerina,
 * recolhível no desktop e drawer com overlay no mobile (< 960px).
 */
@Component({
  selector: 'jx-app-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, FaIconComponent],
  templateUrl: './app-shell.component.html',
  styleUrl: './app-shell.component.scss',
})
export class AppShellComponent {
  private readonly theme = inject(ThemeService);

  /** Perfil exibido sob a marca ("Loja", "Admin de área"…). */
  readonly surfaceLabel = input.required<string>();
  readonly nav = input.required<ShellNavItem[]>();
  /** Cartão de contexto (nome da loja/área). Vazio = cartão oculto. */
  readonly contextTitle = input<string>('');
  readonly contextSubtitle = input<string>('');
  readonly navAriaLabel = input<string>('Navegação principal');

  readonly logout = output<void>();

  protected readonly menuOpen = signal(false);
  protected readonly collapsed = signal(this.readCollapsed());
  protected readonly isDark = computed(() => this.theme.theme() === 'dark');
  protected readonly initials = computed(() =>
    this.contextTitle()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0]!.toUpperCase())
      .join('')
  );

  protected readonly iconBars = faBars;
  protected readonly iconClose = faXmark;
  protected readonly iconLogout = faRightFromBracket;
  protected readonly iconSun = faSun;
  protected readonly iconMoon = faMoon;
  protected readonly iconCollapse = faAnglesLeft;
  protected readonly iconExpand = faAnglesRight;

  protected toggleTheme(): void {
    this.theme.toggle();
  }

  protected toggleCollapsed(): void {
    const next = !this.collapsed();
    this.collapsed.set(next);
    try {
      localStorage.setItem(COLLAPSE_KEY, next ? '1' : '0');
    } catch {
      /* storage indisponível — preferência só nesta sessão */
    }
  }

  protected closeMenu(): void {
    this.menuOpen.set(false);
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void {
    if (this.menuOpen()) this.menuOpen.set(false);
  }

  private readCollapsed(): boolean {
    try {
      return localStorage.getItem(COLLAPSE_KEY) === '1';
    } catch {
      return false;
    }
  }
}
