# Correção 053 — Colunas phone e cpf removidas de users; name mantido

> **Classe:** COD/ARCH · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/api/app/auth/models.py` (removidos `phone`, `cpf`; `name` mantido NOT NULL)
- `apps/api/app/couriers/service.py` (signup escreve `name` no User, não escreve phone/cpf)
- `apps/api/app/merchants/service.py` (signup escreve `name` no User, não escreve phone/cpf)
- Banco: `DROP COLUMN phone`, `DROP COLUMN cpf` (com index)

## Decisão

- **`name` fica em `users`** — é identidade da pessoa, independente do papel. Não faz sentido o entregador criar outro nome para entregar em outra área
- **`cpf` fica em `couriers`** — a regra F-02 E2 valida unicidade por área (mesmo CPF pode existir em áreas diferentes)
- **`phone` fica em `couriers`/`merchants`** — pode ter telefones diferentes por contexto (entrega vs loja)

## Tabela final `users`

| Campo | Para quê |
|---|---|
| id | PK |
| email | login (unique) |
| name | nome da pessoa |
| password_hash | autenticação |
| platform_role | admin_plataforma ou user |
| is_active | bloquear acesso |
| totp_* | 2FA |
| failed_attempts / locked_until | lockout |
| deleted_at / anonymized_at | LGPD |

Colunas `phone` e `cpf` foram **dropadas** do banco. Novos cadastros não as preenchem.
