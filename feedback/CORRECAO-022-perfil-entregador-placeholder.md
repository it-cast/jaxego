# Correção 022 — Tela de Perfil do entregador era placeholder: implementação completa

> **Classe:** COD/PROC · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/app/src/features/entregador/perfil.page.ts`
- `apps/app/src/features/entregador/perfil.page.html` (criado)
- `apps/app/src/features/entregador/perfil.page.scss` (criado)

## Problema

A tela de Perfil (aba Perfil) existia apenas como placeholder — stub sem dados reais.

## Implementação

Tela completa espelhando `c-profile` do protótipo:

- Header com avatar de iniciais, nome e `<jx-theme-toggle>`
- Cartão de score: nota total (`number:'1.1-1'`), badge de nível (bronze/prata/ouro/platina), breakdown por componente com barras animadas (`transition: width 0.4s ease`, desativado com `prefers-reduced-motion`)
- Cartão de documentos: lista de `CourierDoc[]` com pills coloridas (ok/warn/err) e label de status em PT-BR
- Cartão de chave PIX: input + botão salvar (`PATCH /v1/couriers/{id}/pix-key`), estados de saving/saved/error
- `courierId = 1` como placeholder (padrão do projeto para M1)
