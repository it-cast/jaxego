# CORRECAO-184 — Fix TypeError editValue.replace no save de zona

## Arquivo modificado
- `apps/web/src/features/equipe/zonas.page.ts`: método `save()` — `ngModel` em `input[type=number]` retorna `number`, não `string`; adicionado `typeof` check antes de chamar `.replace()`
