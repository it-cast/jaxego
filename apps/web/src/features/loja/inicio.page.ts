import { ChangeDetectionStrategy, Component } from '@angular/core';
import { EmptyStateComponent } from '../../shared/state';

@Component({
  selector: 'jx-loja-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [EmptyStateComponent],
  template: `
    <jx-empty-state
      icon="🏪"
      title="Painel da sua loja."
      message="Fretes, entregadores e relatórios aparecem aqui em breve."
    />
  `,
})
export class LojaInicioPage {}
