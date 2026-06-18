import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { makeAppConfig } from '@jaxego/shared/app/app.config';
import { entregadorAppRoutes } from './app/app.routes';

// App do entregador (mobile / Ionic + Capacitor). Usa AppComponent local com
// <ion-app> + <ion-router-outlet> (necessário para IonTabs navegar).
bootstrapApplication(AppComponent, makeAppConfig(entregadorAppRoutes)).catch((err) =>
  console.error(err),
);
