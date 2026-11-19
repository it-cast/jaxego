import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Location } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faArrowLeft } from '@fortawesome/free-solid-svg-icons';
import { LegalDocComponent } from './legal-doc.component';
import { EMPRESA, LegalTipo } from './legal-content';

/** Página pública /termos e /privacidade (o tipo vem de `data.tipo` da rota). */
@Component({
  selector: 'jx-legal-page',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, FaIconComponent, LegalDocComponent],
  template: `
    <div class="jx-lp">
      <header class="jx-lp__topo">
        <div class="jx-lp__wrap jx-lp__topo-inner">
          <a routerLink="/" class="jx-lp__marca" aria-label="Jaxegô, página inicial">
            <span class="jx-lp__logo" aria-hidden="true">J</span>
            <span class="jx-lp__nome">Jaxegô</span>
          </a>
          <button type="button" class="jx-lp__voltar" (click)="voltar()">
            <fa-icon [icon]="seta" aria-hidden="true" /> Voltar
          </button>
        </div>
      </header>

      <main class="jx-lp__wrap jx-lp__conteudo">
        <jx-legal-doc [tipo]="tipo" />
      </main>

      <footer class="jx-lp__rodape">
        <div class="jx-lp__wrap jx-lp__rodape-inner">
          <nav aria-label="Documentos">
            <a routerLink="/termos" [class.jx-lp__atual]="tipo === 'termos'">Termos de Uso</a>
            <a routerLink="/privacidade" [class.jx-lp__atual]="tipo === 'privacidade'">Política de Privacidade</a>
          </nav>
          <p>Dúvidas: <a [href]="'mailto:' + email">{{ email }}</a></p>
        </div>
      </footer>
    </div>
  `,
  styles: `
    :host {
      display: block;
    }
    .jx-lp {
      min-height: 100vh;
      min-height: 100dvh;
      background: var(--surface);
      color: var(--text);
    }
    .jx-lp__wrap {
      width: 100%;
      max-width: 760px;
      margin: 0 auto;
      padding: 0 var(--jx-space-4);
    }
    .jx-lp__topo {
      position: sticky;
      top: 0;
      z-index: 10;
      background: var(--surface-elevated);
      border-bottom: 1px solid var(--border);
    }
    .jx-lp__topo-inner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 64px;
    }
    .jx-lp__marca {
      display: inline-flex;
      align-items: center;
      gap: var(--jx-space-2);
      color: var(--text);
      text-decoration: none;
    }
    .jx-lp__logo {
      display: grid;
      place-items: center;
      width: 36px;
      height: 36px;
      border-radius: var(--jx-radius-md);
      background: var(--brand-gradient);
      color: var(--jx-neutral-0);
      font-weight: var(--jx-weight-extrabold);
    }
    .jx-lp__nome {
      font-size: var(--jx-text-lg);
      font-weight: var(--jx-weight-extrabold);
      letter-spacing: -0.03em;
    }
    .jx-lp__voltar {
      display: inline-flex;
      align-items: center;
      gap: var(--jx-space-2);
      min-height: 44px;
      padding: 0 var(--jx-space-3);
      background: transparent;
      border: 1px solid var(--border);
      border-radius: var(--jx-radius-md);
      color: var(--text);
      font: inherit;
      font-size: var(--jx-text-sm);
      font-weight: var(--jx-weight-semibold);
      cursor: pointer;
    }
    .jx-lp__voltar:hover {
      background: var(--surface-hover);
    }
    .jx-lp__voltar:focus-visible,
    .jx-lp a:focus-visible {
      outline: none;
      box-shadow: var(--focus-ring);
    }
    .jx-lp__conteudo {
      padding-top: var(--jx-space-7);
      padding-bottom: var(--jx-space-7);
    }
    .jx-lp__rodape {
      border-top: 1px solid var(--border);
      background: var(--surface-sunken);
      font-size: var(--jx-text-sm);
      color: var(--text-muted);
    }
    .jx-lp__rodape-inner {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: var(--jx-space-3);
      padding-top: var(--jx-space-5);
      padding-bottom: var(--jx-space-5);
    }
    .jx-lp__rodape nav {
      display: flex;
      flex-wrap: wrap;
      gap: var(--jx-space-4);
    }
    .jx-lp__rodape p {
      margin: 0;
    }
    .jx-lp__rodape a {
      color: var(--brand);
      font-weight: var(--jx-weight-semibold);
      text-decoration: none;
    }
    .jx-lp__rodape a:hover {
      text-decoration: underline;
    }
    .jx-lp__rodape a.jx-lp__atual {
      color: var(--text);
    }
  `,
})
export class LegalPage {
  private readonly location = inject(Location);
  protected readonly tipo = (inject(ActivatedRoute).snapshot.data['tipo'] as LegalTipo) ?? 'termos';
  protected readonly email = EMPRESA.email;
  protected readonly seta = faArrowLeft;

  /** Volta para onde estava; aberta direto (nova aba), vai para a página inicial. */
  protected voltar(): void {
    if (window.history.length > 1) this.location.back();
    else window.location.href = '/';
  }
}
