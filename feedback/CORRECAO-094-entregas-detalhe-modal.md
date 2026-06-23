# Correção 094 — Modal bottom-sheet com detalhes da entrega

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/app/src/features/entregador/entregas.page.ts`

## Problema

Ao clicar em uma entrega na lista, só entregas ativas navegavam para a tela de entrega ativa. Entregas finalizadas/canceladas não tinham ação — não havia como ver detalhes.

## Correção

- Ao clicar em qualquer entrega, carrega os detalhes completos via `getDelivery()` e abre um modal bottom-sheet
- Modal exibe: ID, status, coleta (endereço + bairro), destino (endereço + número), destinatário (nome + telefone mascarado), itens (descrição + quantidade), forma de recebimento, observações, valor, data
- Entregas ativas (ACEITA/COLETADA) continuam navegando para a tela de entrega ativa
- Botão "Fechar" para dismiss do modal
- Todos os itens da lista agora são clicáveis
