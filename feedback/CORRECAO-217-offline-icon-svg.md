# CORRECAO-217 — Ícone offline do entregador: emoji → imagem SVG

**Data:** 2026-07-08

## Problema
A tela offline do entregador (`/entregador/inicio`) exibia o emoji 🛵 como ícone decorativo, sem a identidade visual do projeto.

## Solução

**`apps/app/public/take-away-amico.svg`** (novo)
- SVG copiado de `/home/itcast/Área de Trabalho/Take Away-amico.svg` para a pasta `public/` (pasta de assets estáticos do Angular)

**`apps/app/src/features/entregador/inicio.page.ts`**
- Template: substituído `<div class="jx-home-offline__icon">🛵</div>` por `<img src="take-away-amico.svg" class="jx-home-offline__icon" alt="Entregador offline" />`
- CSS: `.jx-home-offline__icon` alterado de `font-size: 48px` para `width: 220px; height: auto`
