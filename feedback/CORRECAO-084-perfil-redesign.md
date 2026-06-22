# Correção 084 — Redesign da página de perfil do entregador

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/perfil.page.ts`

## Problema

A página de perfil do entregador usava cards empilhados com eyebrows, sem hierarquia visual clara. Não seguia o padrão de settings/perfil moderno.

## Correção

Redesign inspirado no mockup de referência (perfil.png):
- **Avatar circular** centralizado com ícone `faUser` em fundo `brand-wash`
- **Nome e CPF/veículo** centralizados abaixo do avatar
- **Lista de itens** no estilo settings: situação, documentos (com pills de status coloridas), score — cada item em row com border-bottom
- **Pills de status**: verde (aprovado), vermelho (reprovado), amarelo (pendente/em análise)
- **Score card** separado com breakdown
- **Botão "Sair"** pill-shaped com borda vermelha
- Modal de reenvio de documento mantido inalterado
