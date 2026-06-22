# Correção 069 — Seleção de comprovação não mudava o CSS ao trocar opção

> **Classe:** UX · **Data:** 2026-06-22

---

## Arquivos afetados

- `apps/web/src/features/loja/entregas/nova-entrega.page.html`
- `apps/web/src/features/loja/entregas/nova-entrega.page.ts`

## Problema

Na página de nova entrega, a seção "Comprovação" tinha a classe `jx-nova__radio--sel` hardcoded no primeiro radio ("Foto na entrega"). Ao selecionar "Foto + nº do pedido", o CSS não acompanhava — o destaque visual ficava preso na primeira opção.

## Correção

- Adicionado signal `proofMethod` no componente, alimentado via `valueChanges` do form control `proof_method`
- Template atualizado para usar `[class.jx-nova__radio--sel]="proofMethod() === 'photo'"` e `proofMethod() === 'photo_reference'` (dinâmico), igual ao padrão já usado na seção "Pagamento"
