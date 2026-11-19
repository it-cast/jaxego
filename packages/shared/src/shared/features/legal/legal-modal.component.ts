import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  HostListener,
  input,
  output,
  viewChild,
} from '@angular/core';
import { LegalDocComponent } from './legal-doc.component';
import { LegalTipo } from './legal-content';

/**
 * Termos/Privacidade em um modal, para ler sem sair de um formulário (ex.: cadastro do
 * entregador, onde sair da tela perderia senha e fotos). Esc ou "Entendi" fecham.
 */
@Component({
  selector: 'jx-legal-modal',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LegalDocComponent],
  template: `
    <div class="jx-lm__fundo" (click)="fechar.emit()"></div>
    <div class="jx-lm" role="dialog" aria-modal="true" aria-labelledby="jx-lm-titulo">
      <div class="jx-lm__corpo">
        <jx-legal-doc [tipo]="tipo()" tituloId="jx-lm-titulo" />
      </div>
      <div class="jx-lm__acoes">
        <button #fecharBtn type="button" class="jx-lm__btn" (click)="fechar.emit()">Entendi</button>
      </div>
    </div>
  `,
  styles: `
    :host {
      position: fixed;
      inset: 0;
      z-index: 2000;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }
    .jx-lm__fundo {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.5); /* mesmo fundo do modal de histórico do rastro */
    }
    .jx-lm {
      position: relative;
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 720px;
      max-height: 92dvh;
      background: var(--surface-elevated);
      border-radius: var(--jx-radius-xl) var(--jx-radius-xl) 0 0;
      box-shadow: var(--shadow-lg);
    }
    @media (min-width: 720px) {
      :host {
        align-items: center;
      }
      .jx-lm {
        max-height: 86dvh;
        border-radius: var(--jx-radius-xl);
      }
    }
    .jx-lm__corpo {
      overflow-y: auto;
      padding: var(--jx-space-6) var(--jx-space-5) var(--jx-space-3);
      overscroll-behavior: contain;
    }
    .jx-lm__acoes {
      padding: var(--jx-space-3) var(--jx-space-5) calc(var(--jx-space-4) + env(safe-area-inset-bottom));
      border-top: 1px solid var(--border);
    }
    .jx-lm__btn {
      width: 100%;
      min-height: 50px;
      background: var(--brand-gradient);
      color: var(--brand-contrast);
      border: 0;
      border-radius: var(--jx-radius-lg);
      font: inherit;
      font-weight: var(--jx-weight-bold);
      cursor: pointer;
    }
    .jx-lm__btn:focus-visible {
      outline: none;
      box-shadow: var(--focus-ring);
    }
  `,
})
export class LegalModalComponent implements AfterViewInit {
  readonly tipo = input.required<LegalTipo>();
  readonly fechar = output<void>();
  private readonly fecharBtn = viewChild<ElementRef<HTMLButtonElement>>('fecharBtn');

  ngAfterViewInit(): void {
    // Foco no título (o leitor de tela começa do início do texto).
    queueMicrotask(() => document.getElementById('jx-lm-titulo')?.focus());
  }

  @HostListener('document:keydown.escape')
  protected onEsc(): void {
    this.fechar.emit();
  }

  /** Mantém o foco dentro do modal (Tab no último volta ao botão). */
  @HostListener('keydown.tab', ['$event'])
  protected prenderFoco(e: Event): void {
    const btn = this.fecharBtn()?.nativeElement;
    if (btn && document.activeElement === btn && !(e as KeyboardEvent).shiftKey) {
      e.preventDefault();
      document.getElementById('jx-lm-titulo')?.focus();
    }
  }
}
