import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from '@jaxego/shared/app/app.component';
import { makeAppConfig } from '@jaxego/shared/app/app.config';
import { adminAppRoutes } from './app/app.routes';

// App admin (área + plataforma, web) — build físico separado.
bootstrapApplication(AppComponent, makeAppConfig(adminAppRoutes)).catch((err) =>
  console.error(err),
);
