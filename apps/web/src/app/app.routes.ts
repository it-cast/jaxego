import { Routes } from '@angular/router';

// Lazy routes per surface + auth guard are wired in T-05/T-06.
// This placeholder keeps the scaffold buildable at T-01.
export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'entrar',
  },
  {
    path: 'entrar',
    loadComponent: () =>
      import('../app/placeholder.page').then((m) => m.PlaceholderPage),
  },
];
