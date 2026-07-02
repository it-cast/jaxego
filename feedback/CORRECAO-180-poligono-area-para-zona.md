# CORRECAO-180 — Move polígono do form de área para o form de zona

## Mudanças
- `areas.page.html`: removido bloco `<jx-area-map>` e hint
- `areas.page.ts`: removido `formBoundary`, import `AreaMapComponent`, e referências de boundary no `save()`/`showEdit()`/`showCreate()`
- `platform-admin.service.ts`: removido `boundary` da interface `Area`, de `createArea()` e `updateArea()`
- `zonas.page.ts`: adicionado `formBoundary`, `<jx-area-map>` no form, populado no `showEdit()` e enviado no `save()`
