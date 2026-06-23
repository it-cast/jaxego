import {
  ChangeDetectionStrategy,
  Component,
  Input,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { FaIconComponent } from '@fortawesome/angular-fontawesome';
import { faChevronLeft } from '@fortawesome/free-solid-svg-icons';

@Component({
  selector: 'jx-page-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, FaIconComponent],
  template: `
    <header class="jx-page-header">
      @if (backLink) {
        <a [routerLink]="backLink" class="jx-page-header__back" aria-label="Voltar">
          <fa-icon [icon]="iconBack" aria-hidden="true" />
        </a>
      } @else {
        <span class="jx-page-header__spacer"></span>
      }
      <h1 class="jx-page-header__title">{{ title }}</h1>
      <span class="jx-page-header__spacer"></span>
    </header>
  `,
  styles: [`
    .jx-page-header {
      display: flex;
      align-items: center;
      min-height: 56px;
      padding: 0 var(--jx-space-3);
      background: #fff;
      border-bottom: 1px solid var(--border, hsl(0 0% 90%));
    }
    .jx-page-header__back {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      color: var(--brand);
      text-decoration: none;
      font-size: var(--jx-text-lg);
    }
    .jx-page-header__title {
      flex: 1;
      margin: 0;
      text-align: center;
      font-family: var(--jx-font-display);
      font-size: var(--jx-text-md);
      font-weight: var(--jx-weight-bold);
      color: var(--text);
    }
    .jx-page-header__spacer {
      width: 40px;
    }
  `],
})
export class PageHeaderComponent {
  @Input({ required: true }) title!: string;
  @Input() backLink: string | null = null;

  protected readonly iconBack = faChevronLeft;
}
