import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { makeAppConfig } from '@jaxego/shared/app/app.config';
import { entregadorAppRoutes } from './app/app.routes';
import { environment } from './environments/environment';

// App do entregador (mobile / Ionic + Capacitor). Usa AppComponent local com
// <ion-app> + <ion-router-outlet> (necessário para IonTabs navegar).
// apiBaseUrl: vazio em dev (usa proxy.conf.json), URL absoluta em produção —
// o APK não tem dev server pra resolver caminhos relativos.
bootstrapApplication(
  AppComponent,
  makeAppConfig(entregadorAppRoutes, { apiBaseUrl: environment.apiUrl }),
).catch((err) => console.error(err));
