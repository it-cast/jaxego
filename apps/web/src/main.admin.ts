import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { makeAppConfig } from './app/app.config';
import { adminAppRoutes } from './app/app.routes';

// App admin (área + plataforma, web) — build físico separado (MR-5).
bootstrapApplication(AppComponent, makeAppConfig(adminAppRoutes)).catch((err) =>
  console.error(err),
);
