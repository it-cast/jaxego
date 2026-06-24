import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faCircleCheck, faRightToBracket } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'jx-cadastro-sucesso',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, FaIconComponent],
  template: `
    <div class="jx-sucesso">
      <div class="jx-sucesso__icon">
        <fa-icon [icon]="iconCheck" aria-hidden="true" />
      </div>

      <h1 class="jx-sucesso__title">Cadastro realizado!</h1>

      <p class="jx-sucesso__text">
        Sua loja foi cadastrada com sucesso na plataforma.
        Agora você já pode acessar o painel e começar a gerenciar suas entregas.
      </p>

      <p class="jx-sucesso__hint">
        Clique no botão abaixo para fazer login e começar a usar o sistema.
      </p>

      <a class="jx-sucesso__btn" routerLink="/entrar">
        <fa-icon [icon]="iconLogin" aria-hidden="true" />
        Ir para o login
      </a>
    </div>
  `,
  styles: [`
    :host { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--bg, #f9f9f9); }

    .jx-sucesso {
      max-width: 440px; width: 100%; margin: 0 auto;
      padding: var(--jx-space-6, 48px) var(--jx-space-4, 16px);
      display: flex; flex-direction: column; align-items: center; gap: var(--jx-space-3, 12px);
      text-align: center;
    }

    .jx-sucesso__icon { font-size: 64px; color: var(--success, #2e7d32); }

    .jx-sucesso__title {
      margin: 0;
      font-family: var(--jx-font-display, sans-serif);
      font-size: var(--jx-text-2xl, 28px);
      font-weight: 800;
      color: var(--text, #1a1a1a);
    }

    .jx-sucesso__text {
      margin: 0;
      font-size: var(--jx-text-sm, 15px);
      color: var(--text-muted, #666);
      line-height: 1.6;
    }

    .jx-sucesso__hint {
      margin: 0;
      font-size: var(--jx-text-xs, 13px);
      color: var(--text-muted, #888);
    }

    .jx-sucesso__btn {
      display: flex; align-items: center; justify-content: center; gap: 8px;
      width: 100%; min-height: 50px; margin-top: var(--jx-space-3, 12px);
      border: 0; border-radius: 999px;
      background: var(--brand, #e8722a); color: #fff;
      font-size: 16px; font-weight: 700;
      text-decoration: none; cursor: pointer;
    }
    .jx-sucesso__btn:hover { opacity: 0.9; }
  `],
})
export class CadastroSucessoPage {
  protected readonly iconCheck = faCircleCheck;
  protected readonly iconLogin = faRightToBracket;
}
