import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from '@jaxego/shared/app/app.component';
import { makeAppConfig } from '@jaxego/shared/app/app.config';
import { lojaAppRoutes } from './app/app.routes';

// App da loja (web) — build físico separado.
bootstrapApplication(AppComponent, makeAppConfig(lojaAppRoutes)).catch((err) =>
  console.error(err),
);
