import { ChangeDetectionStrategy, Component } from '@angular/core';

/**
 * Painel de marca do login (redesign v3 §6.3) — decorativo (aria-hidden):
 * gradiente azul-noite → tangerina, headline com Fraunces italic, mini-mapa
 * ilustrado com rota animada (desligada em prefers-reduced-motion) e 3 provas
 * de valor. Só CSS/SVG, sem imagem.
 */
@Component({
  selector: 'jx-login-brand-panel',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <aside class="jx-login-visual" aria-hidden="true">
      <div class="jx-login-visual__inner">
        <p class="jx-login-visual__eyebrow">Entregas na sua cidade</p>
        <p class="jx-login-visual__headline">
          Entregador <em>rapidinho</em>, quando o motoboy não dá conta.
        </p>

        <div class="jx-login-visual__map">
          <svg viewBox="0 0 360 220" class="jx-login-visual__svg" preserveAspectRatio="xMidYMid slice">
            <g class="jx-lv-streets">
              <path d="M0 40 H360 M0 110 H360 M0 180 H360 M60 0 V220 M150 0 V220 M250 0 V220 M320 0 V220" />
              <path class="jx-lv-streets--minor" d="M0 75 H360 M0 145 H360 M105 0 V220 M200 0 V220 M285 0 V220" />
            </g>
            <rect class="jx-lv-block" x="160" y="120" width="80" height="50" rx="8" />
            <rect class="jx-lv-block jx-lv-block--zone" x="190" y="20" width="150" height="80" rx="14" />
            <path class="jx-lv-route" d="M60 180 H150 V110 H250 V40" />
            <circle class="jx-lv-store" cx="60" cy="180" r="9" />
            <g class="jx-lv-dest" transform="translate(250 40)">
              <circle class="jx-lv-dest__pulse" r="10" />
              <circle class="jx-lv-dest__dot" r="9" />
            </g>
            <circle class="jx-lv-courier" r="7" />
          </svg>
          <span class="jx-login-visual__eta">
            <span class="jx-login-visual__eta-dot"></span>
            Chega em <strong>8 min</strong>
          </span>
        </div>

        <ul class="jx-login-visual__props">
          <li><span class="jx-login-visual__num">&lt; 60s</span> para um entregador aceitar</li>
          <li><span class="jx-login-visual__num">foto + GPS</span> em toda entrega</li>
          <li><span class="jx-login-visual__num">PIX</span>, cartão ou pagamento direto</li>
        </ul>
      </div>
    </aside>
  `,
  styleUrl: './login-brand-panel.component.scss',
})
export class LoginBrandPanelComponent {}
