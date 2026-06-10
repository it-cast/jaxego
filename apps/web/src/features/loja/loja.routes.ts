import { Routes } from '@angular/router';

/**
 * Loja public onboarding routes (DRV-004 — lazy, standalone). These are PUBLIC:
 * a new store owner has no account yet. The authenticated loja shell lives under
 * `/loja` in app.routes; these onboarding pages are mounted at the root.
 */
export const lojaOnboardingRoutes: Routes = [
  {
    path: 'cadastro',
    loadComponent: () =>
      import('./cadastro/cadastro.page').then((m) => m.CadastroLojaPage),
  },
  {
    path: 'plano',
    loadComponent: () => import('./plano/plano.page').then((m) => m.PlanoPage),
  },
];
