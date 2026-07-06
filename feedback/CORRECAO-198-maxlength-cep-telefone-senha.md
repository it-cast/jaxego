---
classe: ux
data: 2026-07-06
arquivos_afetados:
  - apps/web/src/features/loja/entregas/nova-entrega.page.html
  - apps/web/src/features/loja/cadastro/cadastro.page.html
  - apps/web/src/features/loja/cadastro/cadastro.page.ts
---

## Problema
Campos sem limitação de caracteres permitindo entradas inválidas:
- CEP sem maxlength (formato esperado: 00000-000 = 9 chars)
- Telefone do destinatário sem maxlength (formato: (DD) 9XXXX-XXXX = 15 chars)
- Senha no cadastro com minLength de 10 (tanto no validator Angular quanto no atributo HTML nativo), alterado para 6

## Implementação
- CEP: `[maxlength]="9"` no `jx-field` de CEP em `nova-entrega.page.html`
- Telefone: `[maxlength]="15"` no `jx-field` de telefone do destinatário
- Senha: `Validators.minLength(10)` → `Validators.minLength(6)` em `cadastro.page.ts`
- Senha: `minlength="10"` → `minlength="6"` no `<input>` em `cadastro.page.html` (estava sobrescrevendo o validator Angular)
- Mensagem de erro atualizada: "pelo menos 10 caracteres" → "pelo menos 6 caracteres"
