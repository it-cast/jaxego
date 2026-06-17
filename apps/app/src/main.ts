import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from '@jaxego/shared/app/app.component';
import { makeAppConfig } from '@jaxego/shared/app/app.config';
import { entregadorAppRoutes } from './app/app.routes';

// App do entregador (mobile / Ionic + Capacitor). Consome o design system e o
// core/auth de @jaxego/shared; empacotado nativamente via Capacitor (dist/app/browser).
bootstrapApplication(AppComponent, makeAppConfig(entregadorAppRoutes)).catch((err) =>
  console.error(err),
);
