# Correções do Projeto Jaxego

Registro de todas as correções aplicadas ao projeto durante o desenvolvimento.

---

## [001] Porta do MySQL — conflito com MySQL local

**Data:** 2026-06-15
**Arquivo:** `infra/docker-compose.yml`

**Problema:** O MySQL do Docker tentava bindar a porta `3306`, que já estava ocupada por um MySQL local instalado na máquina. O container subia sem expor nenhuma porta, tornando impossível conectar pelo Workbench.

**Correção:** Alterada a porta exposta de `3306:3306` para `3309:3306`.

---

## [002] Validação de senha no formulário de login (frontend + backend + HTML)

**Data:** 2026-06-15
**Arquivos:**
- `apps/web/src/features/auth/login.page.ts`
- `apps/web/src/features/auth/login.page.html`
- `apps/api/app/auth/schemas.py`

**Problema:** O campo de senha tinha validação `minLength(10)` em três lugares: validator TypeScript no `.ts`, atributo `minlength="10"` no HTML (que o Angular converte em validator automaticamente ao usar `formControlName`), e `Field(min_length=PASSWORD_MIN_LENGTH)` no schema Pydantic do backend. Qualquer senha com menos de 10 caracteres fazia o submit não acontecer — sem feedback claro para o usuário.

**Correção:**
- Removido `Validators.minLength(10)` do `login.page.ts`
- Removido atributo `minlength="10"` do `login.page.html`
- Alterado para `min_length=1` no schema de login do backend (`schemas.py`)
- Senha do admin atualizada para `Roger12345` para compatibilidade com a validação existente

**Nota:** Validação de comprimento mínimo pertence ao cadastro/troca de senha, não ao login.

---

## [003] Frontend rodando com Angular CLI em vez de Ionic CLI

**Data:** 2026-06-15
**Arquivo:** `apps/web/package.json`

**Problema:** O script `start` usava `ng serve` (Angular CLI, porta 4200). O projeto é Ionic + Angular Standalone com Capacitor e deve rodar com `ionic serve` na porta 8100.

**Correção:** Alterado o script `start` de `ng serve` para `ionic serve`. Ambos passam `--proxy-config proxy.conf.json` para rotear `/v1/*` para a API em `localhost:8000`.

---

## [004] Redirecionamento após login sempre volta para /entrar

**Data:** 2026-06-15
**Arquivos:**
- `apps/web/src/features/auth/login.page.ts`
- `apps/web/src/core/auth/auth.service.ts`

**Problema:** Após login bem-sucedido, o código navegava para `/` que redireciona incondicionalmente para `/entrar` — o usuário ficava preso na tela de login mesmo autenticado.

**Correção:** O `AuthService` agora decodifica o JWT para expor a `role` do usuário. O `LoginPage` usa essa role para redirecionar para a área correta após login:
- `admin_plataforma` → `/plataforma/visao-geral`
- `admin_area` → `/admin/inicio`
- `courier` → `/entregador/inicio`
- default (merchant) → `/loja/painel`

---

## [005] Tela de enrollment TOTP não implementada no frontend

**Data:** 2026-06-15
**Status:** PENDENTE — requer implementação

**Problema:** O backend exige que `admin_plataforma` configure TOTP antes de acessar qualquer endpoint protegido. Os endpoints de enrollment existem no backend (`POST /v1/auth/totp/enroll` e `POST /v1/auth/totp/verify`), mas a tela de QR code e configuração do autenticador não foi implementada no frontend.

**Contorno (dev):** `totp_enrolled = 1` setado diretamente no banco para o admin de desenvolvimento.

**Correção necessária:** Implementar tela de enrollment TOTP com exibição de QR code para escanear no Google Authenticator / Authy.

---

## [006] Interceptor HTTP ausente — requisições saem sem token de autorização

**Data:** 2026-06-15
**Arquivos:**
- `apps/web/src/core/auth/auth.interceptor.ts` (criado)
- `apps/web/src/app/app.config.ts`

**Problema:** O `provideHttpClient` não tinha nenhum interceptor registrado. Todas as requisições HTTP do frontend saíam sem o header `Authorization: Bearer <token>`, resultando em 401/403 em todos os endpoints protegidos.

**Correção:** Criado `authInterceptor` funcional que injeta o token em memória do `AuthService` em cada requisição. Registrado via `withInterceptors([authInterceptor])` no `app.config.ts`.

---

## [007] JWT com role incorreta para courier e merchant

**Data:** 2026-06-15
**Arquivos:**
- `apps/api/app/auth/service.py`
- `apps/web/src/features/auth/login.page.ts`

**Problema:** A função `_resolve_session_context` só verificava a tabela `area_admins`. Couriers e merchants sempre recebiam `role: "user"` no JWT, causando redirect errado para `/loja/painel` mesmo para entregadores.

**Correção:**
- Backend: `_resolve_session_context` agora verifica `couriers` e `merchant_users` quando não há membership em `area_admins`, retornando `"courier"` ou `"merchant"` respectivamente
- Frontend: redirect do login atualizado para tratar `"merchant"` e `admin_area:*` (com startsWith)

---

## [008] Sessão perdida ao recarregar a página (F5)

**Data:** 2026-06-15
**Arquivos:**
- `apps/web/src/core/auth/auth.service.ts`
- `apps/web/src/app/app.config.ts`

**Problema:** O access token ficava apenas em memória. Ao recarregar a página, o Angular reiniciava e o token era perdido — o authGuard redirecionava para `/entrar` mesmo com sessão válida. O refresh token existia no cookie httpOnly mas nunca era usado para restaurar a sessão.

**Correção:** Adicionado método `tryRestoreSession()` no `AuthService` que chama `POST /v1/auth/refresh` com `withCredentials: true` ao inicializar. Registrado via `APP_INITIALIZER` no `app.config.ts` para executar antes das rotas serem resolvidas.

---

## [009] Padding insuficiente entre rows da tabela

**Data:** 2026-06-15
**Arquivo:** `apps/web/src/shared/components/data-table/data-table.component.scss`

**Problema:** As rows da `jx-data-table` estavam muito coladas. Tentativa de aumentar o `padding` no `td` não funcionou porque os `<td>` são conteúdo projetado via `@ContentChild` / `<ng-template #row let-item>` — eles carregam o atributo de encapsulamento do componente **pai** (ex: `visao-geral.page`), não do `data-table`. O Angular compila o selector `.jx-data-table tbody td` com o atributo do `data-table`, mas os elementos reais têm o atributo do pai — os estilos não batem.

**Correção:** Adicionado `height: 52px` na regra `tbody tr`. O `<tr>` pertence ao template do próprio `data-table`, então o atributo de encapsulamento é aplicado corretamente e o estilo funciona. A `height` num `<tr>` com `border-collapse: collapse` funciona como altura mínima, criando o espaço vertical entre linhas sem depender do `<td>`.

---

## [010] Padding horizontal dos `<td>` colado na borda da tabela

**Data:** 2026-06-15
**Arquivo:** `apps/web/src/styles/global.scss`

**Problema:** Mesmo após a correção [009], o texto das células estava colado na borda esquerda da tabela. O `padding` definido em `data-table.component.scss` para `tbody td` não era aplicado porque os `<td>` são conteúdo projetado (via `ng-template` do componente pai) e carregam o atributo de encapsulamento do pai, não do `data-table`.

**Correção:** Regra `.jx-data-table tbody td { padding: var(--jx-space-3) var(--jx-space-4) }` movida para `global.scss`, que não tem encapsulamento Angular e aplica o estilo independente de qual componente projetou o `<td>`.

---

## [011] Botão de sair ausente nos menus

**Data:** 2026-06-15
**Arquivos:**
- `apps/web/src/core/auth/auth.service.ts`
- `apps/web/src/layouts/plataforma-shell.component.ts`
- `apps/web/src/layouts/admin-shell.component.ts`
- `apps/web/src/layouts/loja-shell.component.ts`
- `apps/web/src/layouts/entregador-shell.component.ts`

**Problema:** Não havia forma de deslogar dentro da aplicação — nenhum shell tinha botão de saída.

**Correção:**
- `AuthService.logout()` atualizado para `async`: chama `POST /v1/auth/logout` (revoga o refresh token no backend) e limpa o access token em memória
- Botão "Sair" adicionado ao final de cada shell: sidebar inferior (plataforma e admin), topbar (loja), tab bar (entregador)
- Todos navegam para `/entrar` após logout

---

## [012] Admin de área sem navegação lateral

**Data:** 2026-06-15
**Arquivo:** `apps/web/src/layouts/admin-shell.component.ts`

**Problema:** O `admin-shell` foi criado sem links de navegação — apenas com o toggle de colapso e o theme toggle. O admin de área (Roger) entrava em `/admin/inicio` e via só um placeholder vazio, sem acesso às páginas disponíveis (config, bairros, disputas, api-keys).

**Correção:** Adicionado menu lateral com links para todas as rotas do admin: Painel (`inicio`), Configurações (`config`), Bairros (`bairros`), Disputas (`disputas`) e Chaves de API (`api-keys`). Mesmo padrão visual do `plataforma-shell` com colapso, `routerLinkActive` e tokens semânticos.

---

## [013] Admin de área sem acesso ao endpoint de configuração da área

**Data:** 2026-06-15
**Arquivos:**
- `apps/api/app/areas/admin_router.py` (criado)
- `apps/api/app/api/v1/router.py`
- `apps/web/src/features/admin/area-config/area-config.service.ts`

**Problema:** O frontend de configuração da área chamava `GET /v1/areas/{id}` e `PATCH /v1/areas/{id}`, endpoints protegidos por `PlatformAdmin`. O admin de área recebia 403, resultando em "Não conseguimos carregar a configuração. Tente de novo."

**Correção:** Criado router dedicado `areas/admin_router.py` com dois endpoints protegidos por `require_role('admin_area')` que lêem o `area_scope` do próprio token (sem parâmetro de path, sem risco de cross-area):
- `GET /v1/admin/area` — retorna a área do admin autenticado
- `PATCH /v1/admin/area/config` — atualiza o config da área com auditoria

O frontend (`area-config.service.ts`) foi atualizado para usar os novos endpoints.

---

## [014] Links de cadastro na tela de login apontando para rotas inexistentes

**Data:** 2026-06-15
**Arquivo:** `apps/web/src/features/auth/login.page.html`

**Problema:** Os links da tela de login usavam `/cadastro`, `/cadastro/loja` e `/cadastro/entregador`, que não existem no roteador. As rotas reais são `/loja/cadastro` e `/entregador/cadastro`. Qualquer clique nessas âncoras caia na tela de 404.

**Correção:** Links corrigidos para `/loja/cadastro` e `/entregador/cadastro`. O link genérico "Criar conta" (que apontava para `/cadastro` sem destino definido) foi removido.

---

## [015] Link "Esqueci a senha" apontando para rota inexistente

**Data:** 2026-06-15
**Arquivo:** `apps/web/src/features/auth/login.page.html`

**Problema:** O link `href="/auth/recuperar-senha"` na tela de login apontava para uma rota que não existe no roteador Angular e não tem página nem endpoint de backend implementados.

**Correção:** Link removido. Funcionalidade de recuperação de senha é uma implementação futura.

---

## [016] Substituição de emojis/glyphs unicode por Font Awesome nos menus

**Data:** 2026-06-15
**Arquivos:**
- `apps/web/package.json` (dependências adicionadas)
- `apps/web/src/layouts/plataforma-shell.component.ts`
- `apps/web/src/layouts/admin-shell.component.ts`
- `apps/web/src/layouts/loja-shell.component.ts`
- `apps/web/src/layouts/entregador-shell.component.ts`

**Problema:** Os menus usavam emojis e caracteres unicode (`☰`, `◧`, `⚙`, `🗺`, `⏻` etc.) como ícones — renderização inconsistente entre sistemas operacionais, sem controle de tamanho/cor via CSS.

**Correção:** Instalado `@fortawesome/angular-fontawesome@1.0.0` (compatível com Angular 19) + `@fortawesome/free-solid-svg-icons`. Todos os menus usam `<fa-icon>` com SVG: `faGaugeHigh`, `faUsers`, `faScaleBalanced`, `faGear`, `faMap`, `faKey`, `faHouse`, `faBox`, `faMoneyBill`, `faUser`, `faRightFromBracket`, `faBars`. O entregador-shell teve o `IonIcon`/`addIcons` removidos e substituídos por `FaIconComponent`. O toggle de senha na tela de login também foi migrado de emojis (`🙈`/`👁`) para `faEyeSlash`/`faEye`.

---

## [017] Listagem de bairros vazia no formulário de nova entrega

**Data:** 2026-06-15
**Arquivos:**
- `apps/api/app/neighborhoods/router.py`
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts`

**Problema:** O frontend chamava `GET /v1/neighborhoods` para popular o select de bairro no formulário de nova entrega. Esse endpoint exige `admin_area` — a loja recebia 403, o `catch` silencioso definia `neighborhoods = []` e o campo aparecia vazio.

**Correção:** Adicionado endpoint `GET /v1/neighborhoods/catalog` no router de bairros, acessível por qualquer usuário autenticado com `area_scope` definido (merchants, couriers, area admins). Retorna os bairros ativos da área do token. O frontend foi atualizado para chamar `/v1/neighborhoods/catalog`.

---

## [018] Tela de enrollment TOTP para admin de plataforma

**Data:** 2026-06-15
**Status:** IMPLEMENTADO — resolve Correção #005 (PENDENTE)
**Arquivos:**
- `apps/web/src/features/auth/totp-setup.page.ts` (criado)
- `apps/web/src/features/auth/totp-setup.page.html` (criado)
- `apps/web/src/features/auth/totp-setup.page.scss` (criado)
- `apps/web/src/app/app.routes.ts`
- `apps/web/src/core/auth/auth.interceptor.ts`
- `apps/web/src/core/auth/auth.models.ts`
- `apps/api/app/auth/router.py`

**Problema:** O admin de plataforma (`admin_plataforma`) precisava configurar o Google Authenticator antes de acessar qualquer recurso protegido. O backend já impedia o acesso retornando `403 totp_enrollment_required`, mas não havia tela de configuração no frontend. O workaround era setar `totp_enrolled=1` diretamente no banco de dados (Correção #005).

**Fluxo implementado:**
1. Admin faz login → navega para `/plataforma/visao-geral`
2. Qualquer chamada à API retorna `403 { code: "totp_enrollment_required" }`
3. O `authInterceptor` detecta esse código e redireciona para `/plataforma/totp-setup`
4. A tela de setup chama `POST /v1/auth/totp/enroll` → recebe `{ provisioning_uri, secret }`
5. Gera QR code com a lib `qrcode` (npm) e exibe na tela
6. Mostra a chave manual em formato `XXXX XXXX XXXX` para quem não consegue escanear
7. Usuário escaneia com Google Authenticator / Authy, digita o código de 6 dígitos
8. Frontend chama `POST /v1/auth/totp/verify` com o código
9. Em caso de sucesso, exibe tela de confirmação e redireciona para `/plataforma/visao-geral`

**Proteção contra re-enrollment:** O backend agora rejeita `POST /v1/auth/totp/enroll` com `422` se o usuário já tiver `totp_enrolled=True`. O frontend redireciona para a plataforma ao receber esse status.

---