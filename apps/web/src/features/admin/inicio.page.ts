import { ChangeDetectionStrategy, Component } from '@angular/core';
import { EmptyStateComponent } from '../../shared/state';

@Component({
  selector: 'jx-admin-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [EmptyStateComponent],
  template: `
    <jx-empty-state
      icon="⚙️"
      title="Painel administrativo."
      message="Áreas, validações e operação aparecem aqui em breve."
    />
  `,
})
export class AdminInicioPage {}
