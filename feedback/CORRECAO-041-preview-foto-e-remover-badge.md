# Correção 041 — Preview da foto selecionada + botão remover + badge corrigido no cadastro

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/app/src/features/entregador/cadastro/cadastro.page.ts`
- `apps/app/src/features/entregador/cadastro/cadastro.page.html`
- `apps/app/src/features/entregador/cadastro/cadastro.page.scss`

## Problemas

1. Ao selecionar uma foto no wizard, não aparecia preview — o usuário não via o que tinha selecionado
2. O badge mudava para "Em análise" (`status: 'pending'`) ao selecionar a foto, mas o documento ainda não foi enviado — está só em memória aguardando o submit final
3. Não havia forma de remover uma foto selecionada para escolher outra

## Correção

- `DocItem` agora tem campo `previewUrl: string | null`
- `onFileSelected()` gera preview via `URL.createObjectURL(file)` e passa ao `jx-doc-card` via `[previewUrl]`
- Status mantido como `pending_upload` ("A enviar") até o submit final — não usa mais `pending` ("Em análise")
- Botão "Remover" (vermelho, borda) aparece ao lado do texto "Foto selecionada" — revoga o objectURL, limpa o file e reseta o status
- `URL.revokeObjectURL()` chamado ao remover ou trocar foto para evitar memory leak
