import { Routes } from '@angular/router';
import { authGuard } from '@jaxego/core/auth/auth.guard';

/**
 * Rotas do app do entregador (mobile). Login e tracking público vêm da lib
 * compartilhada (@jaxego/shared); o miolo (oferta → aceite → entrega ativa →
 * comprovação) vive em src/features/entregador.
 */

/** Login (público) — componente compartilhado. */
const authRoutes: Routes = [
  {
    path: 'entrar',
    loadComponent: () =>
      import('../features/auth/login.page').then((m) => m.AppLoginPage),
  },
];

/** Entregador (mobile) + onboarding público do entregador. */
const entregadorRoutes: Routes = [
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
            (m) => m.ComprovacaoPage
          ),
      },
      {
        path: 'entrega/:id/concluida',
        loadComponent: () =>
          import('../features/entregador/concluida/concluida.page').then(
            (m) => m.EntregadorConcluidaPage
          ),
      },
      {
        path: 'saldo',
        loadComponent: () =>
          import('../features/entregador/saldo/saldo.page').then(
            (m) => m.EntregadorSaldoPage
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

/** Tracking público (token-only) — componente compartilhado. */
const publicRoutes: Routes = [
  {
    path: 'r/:token',
    loadComponent: () =>
      import('@jaxego/shared/features/public-tracking/public-tracking.page').then(
        (m) => m.PublicTrackingPage
      ),
  },
];

const redirectToLogin: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'entrar' },
];

const notFoundRoute: Routes = [
  {
    path: '**',
    loadComponent: () =>
      import('@jaxego/shared/not-found.page').then((m) => m.NotFoundPage),
  },
];

export const entregadorAppRoutes: Routes = [
  ...redirectToLogin,
  ...authRoutes,
  ...entregadorRoutes,
  ...publicRoutes,
  ...notFoundRoute,
];
