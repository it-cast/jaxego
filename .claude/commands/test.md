---
description: Gerar testes automatizados para um modulo
---
Gere testes completos para: $ARGUMENTS

Regras:
1. Use pytest-asyncio para API, Jasmine/Karma para Angular
2. Padrao AAA (Arrange-Act-Assert)
3. Nomes descritivos em portugues: "deve_retornar_erro_quando_email_duplicado"
4. Teste o caminho feliz + pelo menos 3 edge cases
5. Mock dependencias externas (banco, {gateway-pagamento}, {storage-provider})
6. Teste codigos HTTP corretos (201, 400, 401, 404, 409, 422)
7. Confira se o CLAUDE.md tem regra especifica para esse modulo

Gere o arquivo de teste completo, pronto para rodar.
