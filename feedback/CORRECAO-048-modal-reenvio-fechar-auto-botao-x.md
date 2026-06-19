# Correção 048 — Modal de reenvio: fechar após sucesso + botão X para remover foto

> **Classe:** UX · **Data:** 2026-06-18 · **Relacionada:** Correção 047

---

## Arquivo afetado

- `apps/app/src/features/entregador/perfil.page.ts`

## Problemas

1. Após enviar o documento com sucesso, o modal permanecia aberto — o entregador precisava fechar manualmente
2. Não havia forma de remover a foto selecionada no modal para escolher outra (como existe no cadastro)

## Correção

- Modal fecha automaticamente após upload bem-sucedido (`closeResendModal()` chamado antes do `finally`)
- Botão "✕" vermelho circular (28×28px) posicionado no canto superior direito da área de preview, idêntico ao do cadastro
- `clearResendFile()` revoga o objectURL e limpa file + preview
