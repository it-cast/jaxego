# Correção 077 — Tamanho do pacote trocado de inputs para cards selecionáveis

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/web/src/features/loja/entregas/nova-entrega.page.ts`
- `apps/web/src/features/loja/entregas/nova-entrega.page.html`
- `apps/web/src/features/loja/entregas/nova-entrega.page.scss`

## Problema

O tamanho do pacote era definido por 4 inputs numéricos separados (peso, comprimento, largura, altura), pouco intuitivo para o lojista.

## Correção

- Inputs de peso e dimensões substituídos por 4 cards selecionáveis com tamanhos pré-definidos: Pequeno, Médio, Grande, Extra Grande
- Cada card exibe: ícone de caixa, nome, descrição dos tipos de produto, dimensões e peso máximo
- Ao selecionar, os valores de peso e dimensões são preenchidos nos form controls ocultos (o banco continua recebendo os valores separados)
- Grid de 2 colunas, card selecionado com borda brand + background wash
- Default: Pequeno selecionado ao carregar
