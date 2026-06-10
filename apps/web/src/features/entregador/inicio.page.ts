import { ChangeDetectionStrategy, Component } from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { EmptyStateComponent } from '../../shared/state';

@Component({
  selector: 'jx-entregador-inicio',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, EmptyStateComponent],
  template: `
    <ion-content>
      <jx-empty-state
        icon="🛵"
        title="Tudo pronto pra rodar."
        message="As corridas da sua área aparecem aqui quando começarem."
      />
    </ion-content>
  `,
})
export class EntregadorInicioPage {}
