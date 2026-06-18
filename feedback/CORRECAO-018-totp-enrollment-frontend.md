# Correção 018 — Tela de enrollment TOTP para admin de plataforma

> **Classe:** COD · **Data:** 2026-06-15 · **Resolve:** Correção 005

---

## Arquivos afetados

- `apps/web/src/features/auth/totp-setup.page.ts` (criado)
- `apps/web/src/features/auth/totp-setup.page.html` (criado)
- `apps/web/src/features/auth/totp-setup.page.scss` (criado)
- `apps/web/src/app/app.routes.ts`
- `apps/web/src/core/auth/auth.interceptor.ts`
- `apps/web/src/core/auth/auth.models.ts`
- `apps/api/app/auth/router.py`

## Problema

O admin de plataforma (`admin_plataforma`) precisava configurar o Google Authenticator antes de acessar qualquer recurso protegido. O backend já impedia o acesso retornando `403 totp_enrollment_required`, mas não havia tela de configuração no frontend. O workaround era setar `totp_enrolled=1` diretamente no banco de dados (Correção 005).

## Fluxo implementado

1. Admin faz login → navega para `/plataforma/visao-geral`
2. Qualquer chamada à API retorna `403 { code: "totp_enrollment_required" }`
3. O `authInterceptor` detecta esse código e redireciona para `/plataforma/totp-setup`
4. A tela de setup chama `POST /v1/auth/totp/enroll` → recebe `{ provisioning_uri, secret }`
5. Gera QR code com a lib `qrcode` (npm) e exibe na tela
6. Mostra a chave manual em formato `XXXX XXXX XXXX` para quem não consegue escanear
7. Usuário escaneia com Google Authenticator / Authy, digita o código de 6 dígitos
8. Frontend chama `POST /v1/auth/totp/verify` com o código
9. Em caso de sucesso, exibe tela de confirmação e redireciona para `/plataforma/visao-geral`

## Proteção contra re-enrollment

O backend agora rejeita `POST /v1/auth/totp/enroll` com `422` se o usuário já tiver `totp_enrolled=True`. O frontend redireciona para a plataforma ao receber esse status.
