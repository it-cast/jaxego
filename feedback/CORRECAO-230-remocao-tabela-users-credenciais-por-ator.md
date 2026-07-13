# CORRECAO-230 — Remoção da tabela `users`: cada ator com credenciais próprias

## Data
2026-07-10

## Motivação
A identidade global (`users.email` unique) impedia o mesmo e-mail de ter conta
de loja E de entregador, e o `resolve_surface` com prioridade fixa fazia um
usuário multi-papel cair sempre na tela de entregador. Decisão: eliminar a
tabela `users`; cada tipo de acesso guarda email/senha na própria tabela e loga
no seu próprio endpoint.

## Novo modelo de autenticação

### Tabelas de conta (todas com `CredentialsMixin`: password_hash, is_active, lockout 5/15min)
| Tabela | Identidade | Observações |
|---|---|---|
| `couriers` | email (unique), cpf (unique, novo campo) | perdeu `user_id`; entregador atua na área da equipe |
| `merchants` | email (já era unique) | `merchant_users` **dropada** |
| `teams` | email (novo, unique) | perdeu `responsavel_user_id` |
| `area_admins` | email (novo, unique) + name (novo) | perdeu `user_id`; deixou de ser associação |
| `platform_admins` | **nova tabela** | com TOTP (migrado de users) |

### Endpoints de login (auth/router.py)
```
POST /v1/auth/entregador/login  → couriers
POST /v1/auth/loja/login        → merchants
POST /v1/auth/equipe/login      → teams
POST /v1/auth/admin/login       → area_admins
POST /v1/auth/plataforma/login  → platform_admins (TOTP)
```
Refresh/logout/me continuam únicos. JWT ganhou claim `typ` (tipo de conta);
`sub` é o id na tabela do tipo. `/me` resolve direto do token — cada conta cai
SEMPRE na sua superfície (sem prioridade mágica).

### Backend
- `auth/principals.py` (novo): dataclass `Actor` (type, id, area_id, role, row)
  + `load_actor`/`build_actor`. `CurrentUser` agora injeta `Actor`.
- `auth/service.py`: `authenticate(actor_type=...)` genérico sobre a tabela do
  tipo; lockout genérico; `resolve_surface_for(actor)`; refresh tokens com
  `actor_type`+`actor_id` (renomeado de user_id).
- Guards: `require_role` checa `actor.role`; `require_platform_admin` checa
  `actor.type`; TOTP obrigatório só para platform_admin.
- Scopes diretos do token: `merchant_scope`/`courier_scope`/`_own_courier`/
  `_resolve_team` não fazem mais join — o ator É a linha.
- `write_audit` e `transition` ganharam `actor_type`; colunas novas em
  `audit_log`, `delivery_state_transitions`, `deliveries.cancel_actor_type`,
  `push_subscriptions.actor_type` (linhas antigas ficam NULL — id era users.id).
- LGPD (`workers/lifecycle.py`): anonimização de courier agora limpa cpf e
  password_hash; blocos sobre `users` removidos.

### Cadastros corrigidos
- **Entregador** (`couriers/service.signup`): grava cpf + password_hash no
  courier; colisão genérica por email OU cpf (anti-enumeração).
- **Loja** (`merchants/service.signup`): password_hash no merchant; sem
  User/MerchantUser.
- **Equipe** (`teams/service.create_team/update_team`): email+senha na própria
  linha, unicidade de email na tabela.
- **Admin da cidade** (`areas/service.create_area_admin_with_user`): conta
  criada direto em area_admins.

### Migration `0045_drop_users_actor_credentials`
Backup feito antes (`backup-pre-0045-*.sql` na raiz). Passos: adiciona colunas,
copia credenciais de `users` via JOIN para cada tabela, cria e povoa
`platform_admins`, apaga todos os refresh tokens (re-login geral), renomeia
`refresh_tokens.user_id`→`actor_id` + `actor_type`, adiciona actor_type nas
tabelas de rastro, dropa `merchant_users` e `users`. Downgrade não suportado
(restaurar do backup).

### Frontends
- `auth.service.ts` (shared): `login(req, profile)` → POST `/v1/auth/<profile>/login`.
- Web: rotas de login por perfil — `/entrar` (loja), `/equipe/entrar`,
  `/admin/entrar`, `/plataforma/entrar` (data.profile na LoginPage compartilhada).
- App: login fixo no perfil `entregador`.
- Auto-login pós-cadastro da loja usa perfil `loja`.

## Validado
- Import completo da API e workers OK; migração de dados conferida (senhas
  argon2 presentes em todas as tabelas; platform_admin com TOTP migrado).
- E2E: signup de entregador → login em /entregador/login → JWT typ=courier →
  /me surface=entregador. 401 genérico nos 4 endpoints com senha errada.
- Builds web e app verdes.

## Efeitos colaterais conhecidos
- Todas as sessões foram invalidadas (re-login obrigatório).
- Mesmo e-mail agora pode existir como loja e entregador, cada um com sua senha.
- Testes automatizados (conftest cria `User`) ficaram desatualizados — ajuste pendente.
