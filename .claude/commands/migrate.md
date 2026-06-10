---
description: Criar migration do Alembic para alteracao no banco
---
Crie uma migration para: $ARGUMENTS

Passos:
1. Identifique qual model em apps/api/app/models/ precisa mudar
2. Faca a alteracao no model Python
3. Gere a migration: uv run alembic revision --autogenerate -m "$ARGUMENTS"
4. Revise o SQL gerado
5. Aplique: uv run alembic upgrade head
6. Atualize o CLAUDE.md se a estrutura do banco mudou significativamente
