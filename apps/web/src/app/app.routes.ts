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
      {
        path: 'cobertura',
        loadComponent: () =>
          import(
            '../features/entregador/cobertura-precos/cobertura-precos.page'
          ).then((m) => m.CoberturaPrecosPage),
      },
      // Phase 9 (F-06): proof capture for an active delivery (telas 06/07).
      {
        path: 'entrega/:id/comprovar/:kind',
        loadComponent: () =>
          import('../features/entregador/comprovacao/comprovacao.page').then(
            (m) => m.ComprovacaoPage,
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
      { path: '', pathMatch: 'full', redirectTo: 'painel' },
      {
        path: 'inicio',
        loadComponent: () =>
          import('../features/loja/inicio.page').then((m) => m.LojaInicioPage),
      },
      // Phase 7 (F-03): dashboard (tela 11), new delivery (tela 12), list (tela 14).
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
      // Phase 9 (F-06): store delivery detail (tela 13) — timeline + cancel + link.
      {
        path: 'entregas/:id',
        loadComponent: () =>
          import('../features/loja/entrega-detalhe/entrega-detalhe.page').then(
            (m) => m.EntregaDetalhePage,
          ),
      },
      // Phase 8 (F-05): favoritos e bloqueados (tela 15).
      {
        path: 'favoritos',
        loadComponent: () =>
          import('../features/loja/favoritos/favoritos.page').then((m) => m.FavoritosPage),
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
      // Phase 12 (tela 22 / D-10): chaves de API + webhook da área.
      {
        path: 'api-keys',
        loadComponent: () =>
          import('../features/admin/api-keys/api-keys.page').then(
            (m) => m.AdminApiKeysPage
          ),
      },
      // Phase 13 (tela 09 / D-08): disputas + suspensões da área.
      {
        path: 'disputas',
        loadComponent: () =>
          import('../features/admin/governanca/disputas.page').then(
            (m) => m.AdminGovernancaDisputasPage
          ),
      },
      // Phase 13 (telas 19/20 / D-04/D-05): detalhe do entregador + score + suspensão.
      {
        path: 'entregadores/:courierId',
        loadComponent: () =>
          import('../features/admin/governanca/entregador-detalhe.page').then(
            (m) => m.AdminEntregadorDetalhePage
          ),
      },
    ],
  },
  // Phase 13 (D-06): platform-admin shell (telas 23-25). Lazy, auth-guarded; the
  // backend enforces require_platform_admin + TOTP (ADR-005) on every endpoint, so
  // a non-platform admin simply sees empty/error states. Cross-area reads are audited.
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
  // Public tracking (tela 26, F-06 / Phase 9): token-only, NO auth guard. The map
  // (MapLibre) is lazy inside the page so it never bloats this route's chunk.
  {
    path: 'r/:token',
    loadComponent: () =>
      import('../features/public-tracking/public-tracking.page').then(
        (m) => m.PublicTrackingPage,
      ),
  },
  {
    path: '**',
    loadComponent: () =>
      import('../shared/not-found.page').then((m) => m.NotFoundPage),
  },
];
