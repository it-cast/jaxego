import { ChangeDetectionStrategy, Component } from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { EmptyStateComponent } from '../../shared/state';

@Component({
  selector: 'jx-entregador-entregas',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, EmptyStateComponent],
  template: `
    <ion-content>
      <jx-empty-state
        icon="📦"
        title="Nenhuma corrida ainda."
        message="Quando você aceitar uma corrida, ela aparece aqui."
      />
    </ion-content>
  `,
})
export class EntregadorEntregasPage {}
