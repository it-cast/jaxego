# Correção 050 — Botão "Sair" movido do menu de tabs para a página de Perfil

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/layouts/entregador-shell.component.ts`
- `apps/app/src/features/entregador/perfil.page.ts`

## Problema

O botão "Sair" ocupava espaço na tab bar junto com Início, Ganhos, Bairros e Perfil — 5 itens no total. Em telas pequenas ficava apertado, e "Sair" não é uma ação de navegação frequente.

## Correção

- **Shell**: removido o botão "Sair" e as dependências de `AuthService`, `Router`, `faRightFromBracket`
- **Perfil**: adicionado botão "Sair da conta" com ícone `faRightFromBracket`, estilo outline vermelho, no final da página. Chama `AuthService.logout()` e navega para `/entrar`
- Tab bar agora tem 4 itens (Início, Ganhos, Bairros, Perfil) — mais limpo e padrão mobile
