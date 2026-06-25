import { Routes } from '@angular/router';
import { authGuard } from '@jaxego/core/auth/auth.guard';

/**
 * Route groups by surface. apps/web monta as superfícies web (loja + admin +
 * plataforma + auth + tracking público). O entregador (mobile) vive em apps/app.
 */

/** Login (public). */
export const authRoutes: Routes = [
  {
    path: 'entrar',
    loadComponent: () =>
      import('@jaxego/shared/features/auth/login.page').then((m) => m.LoginPage),
  },
];

/** Loja (web) surface + public store onboarding. */
export const lojaRoutes: Routes = [
  {
    path: 'loja/cadastro/sucesso',
    loadComponent: () =>
      import('../features/loja/cadastro/cadastro-sucesso.page').then(
        (m) => m.CadastroSucessoPage
      ),
  },
  {
    path: 'loja/cadastro',
    loadComponent: () =>
      import('../features/loja/cadastro/cadastro.page').then(
        (m) => m.CadastroLojaPage
      ),
  },
  {
    path: 'loja',
    canActivate: [authGuard],
    loadComponent: () =>
      import('../layouts/loja-shell.component').then((m) => m.LojaShellComponent),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'painel' },
      {
        path: 'plano',
        loadComponent: () =>
          import('../features/loja/plano/plano.page').then((m) => m.PlanoPage),
      },
      {
        path: 'config',
        loadComponent: () =>
          import('../features/loja/config/config.page').then((m) => m.LojaConfigPage),
      },
      {
        path: 'inicio',
        loadComponent: () =>
          import('../features/loja/inicio.page').then((m) => m.LojaInicioPage),
      },
      {
        path: 'painel',
        loadComponent: () =>
          import('../features/loja/dashboard/dashboard.page').then((m) => m.LojaDashboardPage),
      },
      {
        path: 'entregas/nova',
        loadComponent: () =>
          import('../features/loja/entregas/nova-entrega.page').then((m) => m.NovaEntregaPage),
      },
      {
        path: 'entregas',
        loadComponent: () =>
          import('../features/loja/entregas/entregas-list.page').then((m) => m.EntregasListPage),
      },
      {
        path: 'entregas/:id',
        loadComponent: () =>
          import('../features/loja/entrega-detalhe/entrega-detalhe.page').then(
            (m) => m.EntregaDetalhePage,
          ),
      },
      {
        path: 'favoritos',
        loadComponent: () =>
          import('../features/loja/favoritos/favoritos.page').then((m) => m.FavoritosPage),
      },
      {
        path: 'faturas',
        loadComponent: () =>
          import('../features/loja/financeiro/fatura.page').then(
            (m) => m.LojaFaturaPage,
          ),
      },
      {
        path: 'entregas/:id/recibo',
        loadComponent: () =>
          import('../features/loja/financeiro/recibo.page').then(
            (m) => m.LojaReciboPage,
          ),
      },
    ],
  },
];

/** Admin da área surface. */
export const adminRoutes: Routes = [
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
      {
        path: 'lojas',
        loadComponent: () =>
          import('../features/admin/lojas/lojas-list.page').then(
            (m) => m.AdminLojasPage
          ),
      },
      {
        path: 'api-keys',
        loadComponent: () =>
          import('../features/admin/api-keys/api-keys.page').then(
            (m) => m.AdminApiKeysPage
          ),
      },
      {
        path: 'disputas',
        loadComponent: () =>
          import('../features/admin/governanca/disputas.page').then(
            (m) => m.AdminGovernancaDisputasPage
          ),
      },
      {
        path: 'equipes',
        loadComponent: () =>
          import('../features/admin/equipes/equipes.page').then(
            (m) => m.AdminEquipesPage
          ),
      },
      {
        path: 'entregadores',
        loadComponent: () =>
          import(
            '../features/admin/entregadores/entregadores-list.page'
          ).then((m) => m.AdminEntregadoresPage),
      },
      {
        path: 'entregadores/:courierId',
        loadComponent: () =>
          import('../features/admin/governanca/entregador-detalhe.page').then(
            (m) => m.AdminEntregadorDetalhePage
          ),
      },
    ],
  },
];

/** Admin da plataforma (super-admin) surface. Ships in the admin app. */
export const plataformaRoutes: Routes = [
  // TOTP enrollment gate (Correção #018): shown when admin_plataforma hasn't enrolled
  // yet. Auth-guarded but NOT inside the shell so the enrollment page é acessível
  // antes do TOTP estar configurado.
  {
    path: 'plataforma/totp-setup',
    canActivate: [authGuard],
    loadComponent: () =>
      import('../features/auth/totp-setup.page').then((m) => m.TotpSetupPage),
  },
  // Phase 13 (D-06): platform-admin shell (telas 23-25). Lazy, auth-guarded; the
  // backend enforces require_platform_admin + TOTP (ADR-005) on every endpoint.
  {
    path: 'plataforma',
    canActivate: [authGuard],
    loadComponent: () =>
      import('../layouts/plataforma-shell.component').then(
        (m) => m.PlataformaShellComponent,
      ),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'visao-geral' },
      {
        path: 'visao-geral',
        loadComponent: () =>
          import('../features/admin-plataforma/visao-geral.page').then(
            (m) => m.PlataformaVisaoGeralPage,
          ),
      },
      {
        path: 'areas',
        loadComponent: () =>
          import('../features/admin-plataforma/areas.page').then(
            (m) => m.PlataformaAreasPage,
          ),
      },
      {
        path: 'pessoas',
        loadComponent: () =>
          import('../features/admin-plataforma/pessoas.page').then(
            (m) => m.PlataformaPessoasPage,
          ),
      },
      {
        path: 'planos',
        loadComponent: () =>
          import('../features/admin-plataforma/planos.page').then(
            (m) => m.PlataformaPlanosPage,
          ),
      },
      {
        path: 'admins',
        loadComponent: () =>
          import('../features/admin-plataforma/admins.page').then(
            (m) => m.PlataformaAdminsPage,
          ),
      },
      {
        path: 'disputas',
        loadComponent: () =>
          import('../features/admin-plataforma/disputas.page').then(
            (m) => m.PlataformaDisputasPage,
          ),
      },
    ],
  },
];

/** Public tracking (token-only, no guard). */
export const publicRoutes: Routes = [
  {
    path: 'r/:token',
    loadComponent: () =>
      import('@jaxego/shared/features/public-tracking/public-tracking.page').then(
        (m) => m.PublicTrackingPage,
      ),
  },
];

/** Wildcard → 404. Always last. */
export const notFoundRoute: Routes = [
  {
    path: '**',
    loadComponent: () =>
      import('@jaxego/shared/not-found.page').then((m) => m.NotFoundPage),
  },
];

const redirectToLogin: Routes = [{ path: '', pathMatch: 'full', redirectTo: 'entrar' }];

/** Combined web route map — o build `web` guarda-chuva (loja + admin + plataforma). */
export const routes: Routes = [
  ...redirectToLogin,
  ...authRoutes,
  ...lojaRoutes,
  ...adminRoutes,
  ...plataformaRoutes,
  ...publicRoutes,
  ...notFoundRoute,
];

/** Per-app route maps (build físico separado por superfície web). */
export const lojaAppRoutes: Routes = [
  ...redirectToLogin,
  ...authRoutes,
  ...lojaRoutes,
  ...publicRoutes,
  ...notFoundRoute,
];

export const adminAppRoutes: Routes = [
  ...redirectToLogin,
  ...authRoutes,
  ...adminRoutes,
  ...plataformaRoutes,
  ...publicRoutes,
  ...notFoundRoute,
];
