import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { ATUALIZADO_EM, LEGAL, LegalTipo } from './legal-content';

/** Corpo de um documento legal (Termos ou Privacidade). Usado na página e no modal. */
@Component({
  selector: 'jx-legal-doc',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="jx-legal">
      <header class="jx-legal__cabeca">
        <h1 class="jx-legal__titulo" [attr.id]="tituloId()" tabindex="-1">{{ doc().titulo }}</h1>
        <p class="jx-legal__data">Última atualização: {{ atualizado }}</p>
        <p class="jx-legal__resumo">{{ doc().resumo }}</p>
      </header>

      @for (s of doc().secoes; track s.titulo) {
        <section class="jx-legal__secao">
          <h2>{{ s.titulo }}</h2>
          @for (p of s.paragrafos ?? []; track $index) {
            <p>{{ p }}</p>
          }
          @if (s.itens?.length) {
            <ul>
              @for (i of s.itens; track $index) {
                <li>{{ i }}</li>
              }
            </ul>
          }
          @for (p of s.depois ?? []; track $index) {
            <p>{{ p }}</p>
          }
        </section>
      }
    </article>
  `,
  styles: `
    :host {
      display: block;
    }
    .jx-legal {
      color: var(--text);
      font-size: var(--jx-text-md);
      line-height: 1.65;
    }
    .jx-legal__cabeca {
      margin-bottom: var(--jx-space-6);
      padding-bottom: var(--jx-space-5);
      border-bottom: 1px solid var(--border);
    }
    .jx-legal__titulo {
      margin: 0 0 var(--jx-space-2);
      font-size: var(--jx-text-3xl);
      font-weight: var(--jx-weight-extrabold);
      letter-spacing: -0.02em;
      line-height: 1.15;
      outline: none;
    }
    .jx-legal__data {
      margin: 0 0 var(--jx-space-3);
      font-family: var(--jx-font-mono);
      font-size: var(--jx-text-xs);
      color: var(--text-muted);
    }
    .jx-legal__resumo {
      margin: 0;
      color: var(--text-muted);
    }
    .jx-legal__secao {
      margin-bottom: var(--jx-space-6);
    }
    .jx-legal__secao h2 {
      margin: 0 0 var(--jx-space-2);
      font-size: var(--jx-text-lg);
      font-weight: var(--jx-weight-bold);
      line-height: 1.3;
    }
    .jx-legal__secao p {
      margin: 0 0 var(--jx-space-3);
    }
    .jx-legal__secao ul {
      margin: 0 0 var(--jx-space-3);
      padding-left: var(--jx-space-5);
    }
    .jx-legal__secao li {
      margin-bottom: var(--jx-space-2);
    }
    .jx-legal__secao li::marker {
      color: var(--brand);
    }
  `,
})
export class LegalDocComponent {
  readonly tipo = input.required<LegalTipo>();
  readonly tituloId = input<string | null>(null);
  protected readonly doc = computed(() => LEGAL[this.tipo()]);
  protected readonly atualizado = ATUALIZADO_EM;
}
