import { Routes } from '@angular/router';
import { authGuard } from '../core/auth/auth.guard';

/**
 * Route groups by surface (MR-5). Each physical app (admin/loja/entregador)
 * composes its own subset from these named groups; the combined `routes` (below)
 * still serves the all-in-one `web` build. The route objects are identical across
 * builds — only which groups are mounted differs.
 */

/** Login (public). */
export const authRoutes: Routes = [
  {
    path: 'entrar',
    loadComponent: () =>
      import('../features/auth/login.page').then((m) => m.LoginPage),
  },
];

/** Entregador (mobile) surface + public courier onboarding. */
export const entregadorRoutes: Routes = [
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
        path: 'perfil',
        loadComponent: () =>
          import('../features/entregador/perfil.page').then(
            (m) => m.EntregadorPerfilPage
          ),
      },
      {
        path: 'cobertura',
        loadComponent: () =>
          import(
            '../features/entregador/cobertura-precos/cobertura-precos.page'
          ).then((m) => m.CoberturaPrecosPage),
      },
      {
        path: 'entrega-ativa',
        loadComponent: () =>
          import(
            '../features/entregador/entrega-ativa/entrega-ativa.page'
          ).then((m) => m.EntregadorEntregaAtivaPage),
      },
      {
        path: 'entrega/:id/comprovar/:kind',
        loadComponent: () =>
          import('../features/entregador/comprovacao/comprovacao.page').then(
            (m) => m.ComprovacaoPage,
          ),
      },
      {
        path: 'entrega/:id/concluida',
        loadComponent: () =>
          import('../features/entregador/concluida/concluida.page').then(
            (m) => m.EntregadorConcluidaPage,
          ),
      },
      {
        path: 'saldo',
        loadComponent: () =>
          import('../features/entregador/saldo/saldo.page').then(
            (m) => m.EntregadorSaldoPage,
          ),
      },
    ],
  },
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
];

/** Loja (web) surface + public store onboarding. */
export const lojaRoutes: Routes = [
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
      { path: '', pathMatch: 'full', redirectTo: 'painel' },
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
      import('../features/public-tracking/public-tracking.page').then(
        (m) => m.PublicTrackingPage,
      ),
  },
];

/** Wildcard → 404. Always last. */
export const notFoundRoute: Routes = [
  {
    path: '**',
    loadComponent: () =>
      import('../shared/not-found.page').then((m) => m.NotFoundPage),
  },
];

const redirectToLogin: Routes = [{ path: '', pathMatch: 'full', redirectTo: 'entrar' }];

/** Combined route map — the all-in-one `web` build. */
export const routes: Routes = [
  ...redirectToLogin,
  ...authRoutes,
  ...entregadorRoutes,
  ...lojaRoutes,
  ...adminRoutes,
  ...plataformaRoutes,
  ...publicRoutes,
  ...notFoundRoute,
];

/** Per-app route maps (MR-5 — physical app separation). */
export const entregadorAppRoutes: Routes = [
  ...redirectToLogin,
  ...authRoutes,
  ...entregadorRoutes,
  ...publicRoutes,
  ...notFoundRoute,
];

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
