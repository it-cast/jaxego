import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { EmptyStateComponent } from './state';

/** 404 — wildcard route. Uses jx-empty-state (UI-SPEC §6.2). */
@Component({
  selector: 'jx-not-found',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [EmptyStateComponent],
  template: `
    <main>
      <jx-empty-state
        icon="∅"
        title="Página não encontrada."
        message="O endereço que você abriu não existe ou foi movido."
        ctaLabel="Voltar ao início"
        (cta)="goHome()"
      />
    </main>
  `,
})
export class NotFoundPage {
  private readonly router = inject(Router);
  protected goHome(): void {
    void this.router.navigate(['/']);
  }
}
