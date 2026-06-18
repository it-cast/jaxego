# Correção 042 — Badge "A enviar" removido dos docs no cadastro + botão X vermelho para remover foto

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `packages/shared/src/shared/components/doc-card/doc-card.component.ts`
- `apps/app/src/features/entregador/cadastro/cadastro.page.html`
- `apps/app/src/features/entregador/cadastro/cadastro.page.scss`

## Problema

1. O badge "A enviar" aparecia nos cards de documento durante o cadastro — desnecessário já que o entregador ainda está montando o pacote, não enviou nada
2. O botão "Remover" era texto na lateral, pouco intuitivo para mobile

## Correção

- `DocCardComponent` ganhou input `hideBadge` (default false) — quando true, esconde o badge sem afetar outros usos do componente
- No cadastro, todos os doc-cards usam `[hideBadge]="true"`
- Botão "Remover" texto substituído por botão "✕" circular vermelho (28×28px) posicionado no canto superior direito sobre a área do preview (position absolute, z-index 1, sombra)
- Só aparece quando há foto selecionada (`@if (doc.file)`)
