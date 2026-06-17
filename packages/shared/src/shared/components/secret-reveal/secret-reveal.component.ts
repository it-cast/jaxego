import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  Output,
  ViewChild,
  inject,
  signal,
} from '@angular/core';

/**
 * jx-secret-reveal — exibe um segredo (API key / secret de webhook) UMA ÚNICA vez
 * (UI-SPEC §Componentes/Novo, D-01/D-10).
 *
 * Campo monoespaçado read-only + botão "Copiar" com feedback textual ("Copiado")
 * + aviso PERMANENTE ("Guarde agora — não exibiremos novamente"). a11y
 * (accessibility-pro): o aviso vive em `aria-live="polite"`; o foco é gerenciado
 * para o campo do segredo ao montar (o consumidor o exibe num modal foco-preso).
 * Tokens semânticos apenas — zero hex (Gate 2); funciona nos 2 temas (DEC-001).
 */
@Component({
  selector: 'jx-secret-reveal',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="jx-secret-reveal">
      <p class="jx-secret-reveal__label" id="secret-reveal-label">{{ label }}</p>

      <div class="jx-secret-reveal__row">
        <code
          #secretField
          class="jx-secret-reveal__value"
          tabindex="0"
          aria-describedby="secret-reveal-label secret-reveal-warning"
          >{{ secret }}</code
        >
        <button
          type="button"
          class="jx-secret-reveal__copy"
          (click)="copy()"
        >
          {{ copied() ? 'Copiado' : 'Copiar' }}
        </button>
      </div>

      <p
        class="jx-secret-reveal__warning"
        id="secret-reveal-warning"
        role="status"
        aria-live="polite"
      >
        {{ warning }}
      </p>
    </div>
  `,
  styleUrl: './secret-reveal.component.scss',
})
export class SecretRevealComponent {
  private readonly host = inject(ElementRef<HTMLElement>);

  /** O segredo completo a exibir (ex.: `jxg_...`). Mostrado apenas aqui. */
  @Input({ required: true }) secret = '';
  /** Rótulo do campo (ex.: "Segredo da chave"). */
  @Input() label = 'Segredo';
  /** Aviso permanente — a única vez que o segredo é exibido. */
  @Input() warning =
    'Esta é a única vez que mostramos o segredo completo. Copie e guarde em local seguro.';

  /** Emitido quando o segredo foi copiado com sucesso (telemetria/UX opcional). */
  @Output() readonly copied$ = new EventEmitter<void>();

  @ViewChild('secretField', { static: false })
  protected secretField?: ElementRef<HTMLElement>;

  protected readonly copied = signal(false);

  /** Move o foco ao campo do segredo (o modal já prende o foco). */
  focus(): void {
    this.secretField?.nativeElement.focus();
  }

  protected async copy(): Promise<void> {
    const ok = await this.writeClipboard(this.secret);
    if (ok) {
      this.copied.set(true);
      this.copied$.emit();
    }
  }

  private async writeClipboard(text: string): Promise<boolean> {
    const nav = (this.host.nativeElement.ownerDocument?.defaultView ?? window).navigator;
    if (nav?.clipboard?.writeText) {
      try {
        await nav.clipboard.writeText(text);
        return true;
      } catch {
        return this.fallbackCopy(text);
      }
    }
    return this.fallbackCopy(text);
  }

  /** Fallback para ambientes sem Clipboard API (ex.: contexto não-seguro). */
  private fallbackCopy(text: string): boolean {
    const doc = this.host.nativeElement.ownerDocument;
    const ta = doc.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'absolute';
    ta.style.left = '-9999px';
    doc.body.appendChild(ta);
    ta.select();
    let ok = false;
    try {
      ok = doc.execCommand('copy');
    } catch {
      ok = false;
    }
    doc.body.removeChild(ta);
    return ok;
  }
}
