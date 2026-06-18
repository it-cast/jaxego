# Correção 046 — Lightbox para visualizar documento KYC em tela cheia

> **Classe:** UX · **Data:** 2026-06-18

---

## Arquivos afetados

- `apps/web/src/features/admin/kyc/kyc-detalhe.page.ts`
- `apps/web/src/features/admin/kyc/kyc-detalhe.page.scss`

## Problema

Na página de revisão KYC do admin (`/admin/kyc/:courierId`), a thumbnail do documento era pequena e não havia forma de ver a imagem em tamanho real para avaliar se o documento é legítimo antes de aprovar.

## Correção

- Lightbox fullscreen implementado sem dependência externa (CSS puro + signals)
- Ao clicar na thumbnail, abre overlay escuro (rgba 0,0,0,0.85) com a imagem centralizada (max 90vw/90vh)
- Botão "✕" no canto superior direito para fechar
- Clique fora da imagem também fecha
- `stopPropagation` na imagem para não fechar ao clicar nela
- O evento `openFull` do `KycReviewRowComponent` (que já existia mas não era consumido) agora é conectado ao lightbox
