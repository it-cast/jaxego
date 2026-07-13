# CORRECAO-233 — Update de admin de cidade com name/email/senha

## Data
2026-07-10

## Problema
Pós CORRECAO-230, o PATCH /v1/plataforma/area-admins/{id} só aceitava
role/area_id. Sem a tabela users, não existia mais nenhum caminho para trocar
e-mail ou resetar a senha de um admin de cidade.

## Mudanças
- `areas/schemas.py` AreaAdminUpdateBody: + name, email (EmailStr), password (min 10)
- `areas/service.py` update_area_admin: aplica os novos campos; e-mail duplicado
  em outra conta → ValidationAppError
- `platform_admin/router.py`: repassa os campos, senha via hash_password
