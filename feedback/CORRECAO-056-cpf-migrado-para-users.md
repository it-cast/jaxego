# Correção 056 — CPF migrado de couriers para users + correção do signup 500

> **Classe:** COD/ARCH · **Data:** 2026-06-19 · **Relacionada:** Correção 053, 055

---

## Arquivos afetados

- `apps/api/app/auth/models.py` (cpf restaurado como campo de User — nullable, unique)
- `apps/api/app/couriers/models.py` (cpf removido do Courier, constraint alterada para area_id+user_id)
- `apps/api/app/couriers/service.py` (signup escreve cpf no User; unicidade por user_id+area_id)
- `apps/api/app/couriers/router.py` (profile e admin list/detail fazem JOIN com User para cpf_masked)
- `apps/api/app/workers/lifecycle.py` (removido courier.cpf da anonymization)
- Banco: `users.cpf` adicionado (VARCHAR(11) NULL UNIQUE), `couriers.cpf` dropado, constraint `uq_couriers_area_id_user_id` adicionada

## Problema

A correção 053 dropou `cpf` de `users` e a coluna já não existia em `couriers` (dropada anteriormente). O signup falhava com `Unknown column 'couriers.cpf' in 'where clause'` (500).

## Decisão

CPF é dado da **pessoa** (único globalmente), não do papel. Fica em `users`:
- Signup valida CPF e grava em `users.cpf`
- Se o user já existe (mesmo email, outra área), mantém o CPF existente
- Unicidade por área: constraint `(area_id, user_id)` em `couriers` — mesmo user não pode ter 2 couriers na mesma área
- Profile e admin list fazem JOIN `couriers ↔ users` para exibir `cpf_masked`

## Tabela final

| Campo | Tabela |
|---|---|
| cpf | `users` (unique global) |
| full_name, phone_e164, email | `couriers` (dados do papel por área) |
| name | `users` (nome da pessoa) |
