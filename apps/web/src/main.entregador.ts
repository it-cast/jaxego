import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { makeAppConfig } from './app/app.config';
import { entregadorAppRoutes } from './app/app.routes';

// App do entregador (mobile / Ionic+Capacitor) — build físico separado (MR-5).
bootstrapApplication(AppComponent, makeAppConfig(entregadorAppRoutes)).catch((err) =>
  console.error(err),
);
