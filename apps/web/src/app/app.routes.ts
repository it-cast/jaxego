import { Routes } from '@angular/router';
import { authGuard } from '../core/auth/auth.guard';

/**
 * Route map (UI-SPEC §6.2):
 *  - /entrar is public (login).
 *  - /entregador, /loja, /admin are lazy (DRV-004) and protected by authGuard.
 *  - wildcard -> 404 (jx-empty-state).
 * Post-login surface routing is added with user-type data in a later phase;
 * for now '/' redirects to /entrar (the guard sends unauthenticated users there).
 */
export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'entrar',
  },
  {
    path: 'entrar',
    loadComponent: () =>
      import('../features/auth/login.page').then((m) => m.LoginPage),
  },
  {
    path: 'entregador',
    canActivate: [authGuard],
    loadComponent: () =>
      import('../layouts/entregador-shell.component').then(
        (m) => m.EntregadorShellComponent
      ),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      {
        path: 'inicio',
        loadComponent: () =>
          import('../features/entregador/inicio.page').then(
            (m) => m.EntregadorInicioPage
          ),
      },
      {
        path: 'entregas',
        loadComponent: () =>
          import('../features/entregador/entregas.page').then(
            (m) => m.EntregadorEntregasPage
          ),
      },
      {
        path: 'ganhos',
        loadComponent: () =>
          import('../features/entregador/ganhos.page').then(
            (m) => m.EntregadorGanhosPage
          ),
      },
      {
        path: 'perfil',
        loadComponent: () =>
          import('../features/entregador/perfil.page').then(
            (m) => m.EntregadorPerfilPage
          ),
      },
    ],
  },
  // Public courier onboarding (F-02): the wizard + post-submit "em análise" are
  // lazy and unauthenticated — a new courier has no account yet (Phase 5).
  {
    path: 'entregador/cadastro',
    loadComponent: () =>
      import('../features/entregador/cadastro/cadastro.page').then(
        (m) => m.CadastroEntregadorPage
      ),
  },
  {
    path: 'entregador/cadastro/em-analise',
    loadComponent: () =>
      import('../features/entregador/cadastro/em-analise.component').then(
        (m) => m.EntregadorEmAnalisePage
      ),
  },
  // Public store onboarding (F-01): cadastro + plano are lazy and unauthenticated
  // — a new store owner has no account yet (Phase 4). Mounted under `loja/` but
  // OUTSIDE the auth-protected shell below.
  {
    path: 'loja/cadastro',
    loadComponent: () =>
      import('../features/loja/cadastro/cadastro.page').then(
        (m) => m.CadastroLojaPage
      ),
  },
  {
    path: 'loja/plano',
    loadComponent: () =>
      import('../features/loja/plano/plano.page').then((m) => m.PlanoPage),
  },
  {
    path: 'loja',
    canActivate: [authGuard],
    loadComponent: () =>
      import('../layouts/loja-shell.component').then((m) => m.LojaShellComponent),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      {
        path: 'inicio',
        loadComponent: () =>
          import('../features/loja/inicio.page').then((m) => m.LojaInicioPage),
      },
    ],
  },
  {
    path: 'admin',
    canActivate: [authGuard],
    loadComponent: () =>
      import('../layouts/admin-shell.component').then(
        (m) => m.AdminShellComponent
      ),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },
      {
        path: 'inicio',
        loadComponent: () =>
          import('../features/admin/inicio.page').then((m) => m.AdminInicioPage),
      },
      {
        path: 'kyc/:courierId',
        loadComponent: () =>
          import('../features/admin/kyc/kyc-detalhe.page').then(
            (m) => m.AdminKycDetalhePage
          ),
      },
      {
        path: 'config',
        loadComponent: () =>
          import('../features/admin/area-config/area-config.page').then(
            (m) => m.AreaConfigPage
          ),
      },
      {
        path: 'bairros',
        loadComponent: () =>
          import('../features/admin/neighborhoods/neighborhoods.page').then(
            (m) => m.NeighborhoodsPage
          ),
      },
    ],
  },
  {
    path: '**',
    loadComponent: () =>
      import('../shared/not-found.page').then((m) => m.NotFoundPage),
  },
];
