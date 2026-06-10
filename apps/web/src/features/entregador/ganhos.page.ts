import { ChangeDetectionStrategy, Component } from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { EmptyStateComponent } from '../../shared/state';

@Component({
  selector: 'jx-entregador-ganhos',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, EmptyStateComponent],
  template: `
    <ion-content>
      <jx-empty-state
        icon="💰"
        title="Sem ganhos por enquanto."
        message="Seus ganhos aparecem aqui depois da primeira corrida."
      />
    </ion-content>
  `,
})
export class EntregadorGanhosPage {}
