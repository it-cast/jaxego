# CORRECAO-266 — apps/app: URL absoluta do backend pra build Android

## Data
2026-07-15

## Contexto
Usuário rodou `ionic cap add android` e perguntou onde fica o link do
backend usado nas requisições. Não existia — o `apps/app` só tinha
`proxy.conf.json` (dev-server only, `ng serve`/`ionic serve`); num APK
empacotado pelo Capacitor não há dev server nem proxy, então as chamadas
`/v1/...` relativas sairiam do próprio WebView (`capacitor://localhost`) e
não alcançariam o backend real. Pedido: montar o esquema de environment
pro `apps/app`, igual o `apps/web` já tem.

## O que foi feito

**1. Environments novos** (`apps/app/src/environments/`)
- `environment.ts` (dev) — `apiUrl: ''` (mantém o comportamento atual via
  `proxy.conf.json`, nada muda em dev).
- `environment.prod.ts` — `apiUrl` com URL absoluta. **TEMPORÁRIO**: usei o
  túnel ngrok que já estava configurado em `SAFE2PAY_CALLBACK_URL` no
  `.env` (mesmo link trocado nesta sessão) só pra deixar buildável/testável
  imediatamente — isso muda toda vez que o ngrok reinicia. **Precisa
  trocar por um domínio fixo antes de um build definitivo.**

**2. Interceptor novo** (`packages/shared/src/core/http/api-base-url.interceptor.ts`)
`apiBaseUrlInterceptor` + token `API_BASE_URL` (injection token, default
`''`). Se `API_BASE_URL` estiver vazio ou a requisição já for URL absoluta
(`http(s)://...`), não faz nada — é aí que o `apps/web` cai, comportamento
zero-mudança pra ele. Se tiver valor, prefixa toda chamada relativa.

**3. `makeAppConfig()`** (`packages/shared/src/shared/app/app.config.ts`)
Ganhou um segundo parâmetro opcional `{ apiBaseUrl }`. Registra o token
`API_BASE_URL` e adiciona `apiBaseUrlInterceptor` na cadeia de
interceptors (antes do `authInterceptor` — ordem não importa
funcionalmente aqui, mas assim a URL já chega absoluta pros outros
interceptors que inspecionam `req.url`).

**4. `apps/app/src/main.ts`** — passa `{ apiBaseUrl: environment.apiUrl }`
pro `makeAppConfig`. `apps/web/src/main.ts` **não foi tocado** — continua
chamando `makeAppConfig(routes)` sem o segundo argumento, então
`apiBaseUrl` cai no default `''` (zero mudança de comportamento pra
loja/admin/plataforma).

**5. `apps/app/angular.json`** — `fileReplacements` na configuration
`production` do target `build`, trocando `environment.ts` por
`environment.prod.ts` (mesmo padrão já usado em `apps/web/angular.json`).

## Validado
- `ng build app --configuration production` — verde. `grep` confirmou que
  a URL do ngrok foi embutida de fato no bundle final
  (`dist/app/browser/main-*.js`).
- `ng build web` — verde, sem warning novo, sem regressão (interceptor é
  no-op quando `apiBaseUrl` não é passado).

## Não testado
- Não rodei o APK de verdade num dispositivo/emulador Android pra
  confirmar que as chamadas saem prefixadas corretamente em runtime — só
  validei que o build embute o valor certo.
- **CORS/cookies cross-origin**: o app, rodando de dentro do WebView do
  Capacitor (origem `https://localhost` ou `capacitor://localhost`), vai
  fazer requisições pra um domínio diferente (o `apiUrl`). O fluxo de
  login/refresh usa cookie httpOnly (`withCredentials: true`) — isso exige
  que o backend tenha CORS configurado liberando essa origem *com*
  credentials (`Access-Control-Allow-Credentials: true` +
  `Access-Control-Allow-Origin` explícito, nunca `*`) e o cookie de refresh
  setado com `SameSite=None; Secure` pra sobreviver cross-site. **Não
  verifiquei se `apps/api` já está configurado assim** — se não estiver, o
  refresh vai falhar silenciosamente no app mobile mesmo com a URL certa.
  Vale testar isso especificamente antes de considerar o build pronto.

## Tech debt / pontos em aberto
- `environment.prod.ts` com URL de ngrok é só pra destravar teste imediato
  — trocar por domínio fixo é obrigatório antes de qualquer build "de
  verdade" pra distribuir.
- CORS/cookie cross-origin (ver "Não testado" acima) — provável próximo
  bloqueio ao testar o app mobile de verdade contra o backend.
