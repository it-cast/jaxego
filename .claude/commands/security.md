---
description: Auditoria de seguranca no codigo
---
Audite seguranca para: $ARGUMENTS

Checklist (baseado nas regras do CLAUDE.md):
1. SQL injection (raw queries, string concatenation)
2. XSS em templates/outputs
3. CSRF protection
4. Auth/authz falhas (rotas sem is_admin, sem get_current_user)
5. Secrets hardcoded (API keys, tokens, senhas no codigo)
6. Input sem validacao Pydantic
7. Erros que expoem stack trace
8. Uploads sem validacao de MIME/tamanho
9. Rate limiting ausente
10. WebSocket sem auth
11. Webhook sem idempotencia
12. CORS muito permissivo
13. Dados pessoais em logs

Classifique: CRITICO > ALTO > MEDIO > BAIXO
Forneca fix concreto para cada achado.
