import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from '@jaxego/shared/app/app.component';
import { makeAppConfig } from '@jaxego/shared/app/app.config';
import { routes } from './app/app.routes';

// App web guarda-chuva (loja + admin + plataforma + auth + tracking). Os builds
// físicos por superfície usam main.admin.ts / main.loja.ts.
bootstrapApplication(AppComponent, makeAppConfig(routes)).catch((err) =>
  console.error(err),
);
