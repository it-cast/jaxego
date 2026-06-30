# CORRECAO-168 — Favoritos/Bloqueados com segment (tabs)

## Páginas afetadas
- `http://localhost:4200/loja/favoritos`
- Menu lateral da loja

## Arquivos alterados
- `apps/web/src/layouts/loja-shell.component.ts` — label "Favoritos" → "Favoritos/Bloqueados"
- `apps/web/src/features/loja/favoritos/favoritos.page.ts` — segment + `tab` signal
- `apps/web/src/features/loja/favoritos/favoritos.page.scss` — estilos dos tabs

## O que mudou
- Menu: label atualizado para "Favoritos/Bloqueados"
- Página: título "Favoritos e Bloqueados" + dois tabs (Favoritos / Bloqueados) com underline ativo, padrão idêntico ao `/plataforma/pessoas`
- Exibe apenas uma lista por vez conforme tab ativa (signal `tab`)
- Tab padrão: "Favoritos"
- Hint contextual aparece acima da lista ativa em vez de sempre visível
- Sem rebuild necessário
