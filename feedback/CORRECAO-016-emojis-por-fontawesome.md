# Correção 016 — Substituição de emojis/glyphs unicode por Font Awesome nos menus

> **Classe:** COD · **Data:** 2026-06-15

---

## Arquivos afetados

- `apps/web/package.json` (dependências adicionadas)
- `apps/web/src/layouts/plataforma-shell.component.ts`
- `apps/web/src/layouts/admin-shell.component.ts`
- `apps/web/src/layouts/loja-shell.component.ts`
- `apps/web/src/layouts/entregador-shell.component.ts`

## Problema

Os menus usavam emojis e caracteres unicode (`☰`, `◧`, `⚙`, `🗺`, `⏻` etc.) como ícones — renderização inconsistente entre sistemas operacionais, sem controle de tamanho/cor via CSS.

## Correção

Instalado `@fortawesome/angular-fontawesome@1.0.0` (compatível com Angular 19) + `@fortawesome/free-solid-svg-icons`. Todos os menus usam `<fa-icon>` com SVG: `faGaugeHigh`, `faUsers`, `faScaleBalanced`, `faGear`, `faMap`, `faKey`, `faHouse`, `faBox`, `faMoneyBill`, `faUser`, `faRightFromBracket`, `faBars`. O entregador-shell teve o `IonIcon`/`addIcons` removidos e substituídos por `FaIconComponent`. O toggle de senha na tela de login também foi migrado de emojis para `faEyeSlash`/`faEye`.
