# Correção 025 — Admin da plataforma bloqueado no login: endpoint /me bloqueado pelo gate TOTP

> **Classe:** PROC/COD · **Data:** 2026-06-18

---

## Arquivo afetado

- `apps/api/app/auth/dependencies.py`

## Problema

O admin da plataforma não conseguia fazer login — recebia "Sua conta ainda não tem acesso a nenhuma área. Fale com o suporte." mesmo com `platform_role = admin_plataforma` correto no banco.

## Causa raiz (2 problemas combinados)

1. O container Docker estava rodando código antigo onde o endpoint `GET /v1/auth/me` ainda não existia — retornava 404
2. Mesmo após rebuild, o gate TOTP em `get_current_user` bloqueava `/auth/me` quando `totp_enrolled=0`, impedindo o frontend de saber para onde redirecionar (inclusive para a própria tela de configuração TOTP)

## Fluxo do bug

Login → token OK → `loadMe()` chama `/v1/auth/me` → gate TOTP rejeita com 403 → frontend catch silencioso → `me = null` → mostra "sem acesso"

## Correção

`/auth/me` adicionado à lista de bypass do gate TOTP, junto com `/auth/totp/enroll` e `/auth/totp/verify`. O endpoint precisa funcionar sem TOTP para que o frontend saiba rotear o usuário para a tela de configuração.

## Correção secundária

Senha do `admin@gmail.com` resetada para `Admin123123` e container API rebuilt com `docker compose up -d --build api`.
