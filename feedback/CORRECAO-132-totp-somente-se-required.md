# CORRECAO-132 — TOTP obrigatório somente quando totp_required = true

## O que mudou

### Backend (apps/api)
- **auth/dependencies.py**: O guard de TOTP antes forçava todos os platform admins a configurar o authenticator, independente de `totp_required`. Agora a regra é:
  - `totp_required = false` → login normal, sem pedir TOTP
  - `totp_required = true` e `totp_enrolled = false` → bloqueia e pede para configurar
  - `totp_required = true` e `totp_enrolled = true` → exige código no login (já funcionava)

## Arquivos alterados
- apps/api/app/auth/dependencies.py
