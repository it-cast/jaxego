import { ChangeDetectionStrategy, Component } from '@angular/core';
import { IonContent } from '@ionic/angular/standalone';
import { EmptyStateComponent } from '../../shared/state';
import { ThemeToggleComponent } from '../../core/theme/theme-toggle.component';

@Component({
  selector: 'jx-entregador-perfil',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [IonContent, EmptyStateComponent, ThemeToggleComponent],
  template: `
    <ion-content>
      <div class="jx-perfil">
        <jx-empty-state
          icon="👤"
          title="Seu perfil."
          message="Dados, documentos e score aparecem aqui em breve."
        />
        <div class="jx-perfil__theme">
          <jx-theme-toggle />
        </div>
      </div>
    </ion-content>
  `,
  styles: [
    `
      .jx-perfil {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--jx-space-4);
        padding-bottom: var(--jx-space-6);
      }
      .jx-perfil__theme {
        display: flex;
        justify-content: center;
      }
    `,
  ],
})
export class EntregadorPerfilPage {}
