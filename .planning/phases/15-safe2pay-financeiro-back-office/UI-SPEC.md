# Phase 15: UI-SPEC — Fatura, extrato/saque, recibo (telas 15/16/08)

**Status:** Visual contract — bloqueante (Gate 2) · **Date:** 2026-06-11 (autopilot)
**Design system:** `docs/identidade-visual/tokens.json`. **Zero hex.** Dark mode (DEC-001).
**Superfícies:** web/mobile loja (15, 08) + mobile entregador (16).

## Escopo de UI
Tela 15 (fatura mensal da loja), 16 (extrato/saldo + saque do entregador), 08 (recibo do pagamento
direto). Reuso obrigatório de componentes governados; nenhuma cor nova.

## Componentes (governados)
### Reuso
- `jx-data-table` — linhas da fatura, extrato do entregador, histórico de saques
- estados empty/error/loading; confirmação sensível (solicitar saque / pagar fatura)
- `jx-state-badge`/badge — status da fatura (em aberto/vencida/paga) e do saque (solicitado/pago/falhou)
### Novo
- `jx-money` — formatação monetária pt-BR consistente (R$, centavos) — reuso da máscara das Phases 4/7
- `jx-invoice-summary` — cartão da fatura (competência, total, vencimento, status, CTA pagar)

## Tokens (todos existem em tokens.json — Gate 2)
### Status / semântica
- paga / saque concluído: `color.semantic.success` / `success_bg`
- vencida / saque falhou / abaixo do mínimo: `color.semantic.error` / `error_bg`
- a vencer / saque em processamento: `color.semantic.warning` / `warning_bg`
- informativo (mínimo de saque, prazo): `color.semantic.info` / `info_bg`
### Base / tipografia / forma
- Texto `color.neutral.900/600/400`; superfícies `color.neutral.50/100/200`; marca/CTA `color.brand.500/600`
- Valores monetários: `font.family.mono`; título `font.family.display` `font.size.2xl` `font.weight.bold`
- Corpo `font.family.body` `font.size.base`; ênfase `font.weight.semibold`
- Cartões `radius.lg` `shadow.sm`; pílulas `radius.full`; foco `shadow.focus`

## Layout & estados
### Tela 15 — Fatura da loja
`jx-invoice-summary` (competência, total mono, vencimento, status badge) + `jx-data-table` das linhas
(entrega, data, taxa). Vencida → banner `error_bg` "Fatura vencida — novas entregas bloqueadas após 7
dias". CTA "Pagar" (fluxo checkout reusado). Empty: "Nenhuma fatura ainda".

### Tela 16 — Extrato/saldo + saque (entregador, mobile)
Saldo disponível (mono, destaque) + `jx-data-table` do extrato (crédito/débito). CTA "Solicitar saque"
→ confirmação sensível; **mínimo R$ 20 citado** ("Saque mínimo de R$ 20,00"); abaixo → erro semântico.
Histórico de saques com status. Empty: "Sem movimentações ainda".

### Tela 08 — Recibo do pagamento direto
Confirmação/recibo: valor, entrega (public_token/referência), data, status. Reuso de trust-safety-ux
(transparência do valor). Sem PII além do permitido (RN-013).

## Acessibilidade (accessibility-pro)
- Valores monetários legíveis (mono + contraste AA); status por cor **+ texto**.
- Confirmação de saque: foco preso, Esc, aria-modal; erro de mínimo com aria-live.
- Mobile (tela 16): touch targets ≥ 44px; gestos coerentes com o app do entregador.

## Copy (br/ux-copywriting-ptbr)
- "Fatura de {competência} — vence em {data}." · "Novas entregas ficam bloqueadas 7 dias após o vencimento."
- "Saque mínimo de R$ 20,00." · "Se o saque falhar, o valor volta para o seu saldo."

## Performance
- Rotas lazy; tabelas paginadas. Valores formatados client-side sem recalcular layout (CLS).

---
*Gate 2: todos os tokens citados existem em tokens.json. Zero hex. Nenhuma cor nova.*
