---
description: Criar endpoint REST completo (schema + repo + service + router)
---
Crie o endpoint completo para: $ARGUMENTS

Siga o padrao do projeto (Router > Service > Repository > Model):
1. **Schema** (apps/api/app/schemas/) - Request e Response com Pydantic v2
2. **Repository** (apps/api/app/repositories/) - Queries async com SQLAlchemy
3. **Service** (apps/api/app/services/) - Logica de negocio + validacoes
4. **Router** (apps/api/app/routers/) - Endpoint HTTP com Depends()
5. **Teste** (apps/api/tests/) - Pelo menos 3 cenarios

Garanta:
- Type hints em tudo
- Docstrings em portugues
- HTTPException com codigos corretos
- Auth com get_current_user ou get_admin_user onde necessario
- Resposta sempre como Pydantic model, nunca dict
