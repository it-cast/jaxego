# Correção 095 — Redesign da tela inicial do entregador

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/inicio.page.ts`
- `apps/app/src/features/entregador/inicio.page.scss`

## Problema

A tela inicial tinha um layout com cards escuros e eyebrows mono que não seguiam o padrão visual atualizado do app.

## Correção

- **Header**: "Olá!" em destaque + status "● Online / ○ Offline" com cor verde quando online
- **Card de ganhos**: fundo brand (laranja) com texto branco, valor grande, saldo e link "Ver extrato"
- **Score**: row limpa com fundo branco, clicável → navega para perfil
- **Waiting**: centralizado com pulse animado
- **Entregas recentes**: lista clean com separadores, header "Recentes" + "Ver todas →"
- **Entrega em andamento**: card com fundo brand-wash, borda brand, botão pill laranja
- **Offer hint**: centralizado com ícone
- **Offline**: ícone grande centralizado com título e mensagem
