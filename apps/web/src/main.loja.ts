import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { makeAppConfig } from './app/app.config';
import { lojaAppRoutes } from './app/app.routes';

// App da loja (web) — build físico separado (MR-5).
bootstrapApplication(AppComponent, makeAppConfig(lojaAppRoutes)).catch((err) =>
  console.error(err),
);
