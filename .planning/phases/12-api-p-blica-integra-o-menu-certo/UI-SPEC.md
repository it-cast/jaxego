# Phase 12: UI-SPEC — Tela 22 (Admin de área · API keys & Webhooks)

**Status:** Visual contract — bloqueante para plan-phase (Gate 2)
**Date:** 2026-06-11 (autopilot)
**Design system:** `docs/identidade-visual/tokens.json` (canônico). **Zero hex hardcoded.**
**Superfície:** Web admin de área (desktop-first, responsivo). Dark mode obrigatório (DEC-001).

## Escopo de UI desta phase
Apenas a **tela 22** (`wireframes/22-admin-area-apikeys.html`). Sem UI mobile. Sem checkout.

## Wireframe-contract (22)
Cobrir: lista de API keys, criação (segredo exibido 1×), revogação, e painel de webhook
(URL + secret + eventos + histórico de entregas/falhas).

---

## Componentes (governados — reuso obrigatório, component-library-governance)

### Reuso (não recriar)
- `jx-data-table` (Phase 6) — tabela de keys e tabela de entregas de webhook
- `jx-empty-state` / estados (Phase 3) — sem keys ainda / sem webhooks
- confirmação sensível before→after (Phase 6) — revogar key / rotacionar secret
- `jx-badge` / state badge styling (Phase 7) — status da key (ativa/revogada) e do webhook
  (sucesso/falha/pendente)

### Novo
- `jx-secret-reveal` — exibe o segredo **uma vez** após criação: campo monoespaçado + botão copiar
  + aviso permanente "Guarde agora — não exibiremos novamente". Após fechar, some.

---

## Tokens (todos existem em tokens.json — Gate 2)

### Cores
- Marca / CTA criar: `color.brand.500`, hover `color.brand.600`, sutil `color.brand.50`
- Texto: `color.neutral.900` (título), `color.neutral.600` (secundário), `color.neutral.400` (hint)
- Superfícies/bordas: `color.neutral.50`, `color.neutral.100`, `color.neutral.200`
- Status semântico:
  - key ativa / webhook entregue: `color.semantic.success` sobre `color.semantic.success_bg`
  - webhook pendente/retry: `color.semantic.warning` sobre `color.semantic.warning_bg`
  - key revogada / webhook failed: `color.semantic.error` sobre `color.semantic.error_bg`
  - aviso do segredo 1×: `color.semantic.info` sobre `color.semantic.info_bg`
- Highlight do segredo recém-criado: `color.semantic.highlight`

### Tipografia
- Título da tela: `font.family.display`, `font.size.2xl`, `font.weight.bold`
- Segredo / key_id / payload: `font.family.mono`, `font.size.sm`
- Corpo/labels: `font.family.body`, `font.size.base`, `font.weight.regular`
- Ênfase de seção: `font.weight.semibold`

### Forma / elevação / foco
- Cartões: `radius.lg`, `shadow.sm` (hover `shadow.md`)
- Modal de criação: `radius.xl`, `shadow.lg`
- Pílulas de status: `radius.full`
- Foco visível (a11y): `shadow.focus` (todos os interativos)

---

## Layout & estados

### Lista de API keys (jx-data-table)
Colunas: Nome | `key_id` (mono, prefixo público) | Escopos | Criada em | Último uso | Status | Ações.
- Ação **Revogar** → confirmação sensível (mostra nome+key_id, "efetiva em < 1 min").
- Empty state: ilustração + "Nenhuma API key ainda" + CTA "Criar primeira key".

### Criar API key (modal)
Form: Nome (obrigatório) + escopos (checkbox `deliveries:write` default). Submit → modal de sucesso
com `jx-secret-reveal` (segredo completo `jxg_...`, copiar, aviso). Fechar volta à lista (key nova
destacada com `color.semantic.highlight` por ~2s).

### Painel de Webhook (por área)
- URL (input https, validação de formato + aviso anti-SSRF inline se host inválido)
- Secret (gerar/rotacionar — `jx-secret-reveal` na rotação)
- Eventos (checkboxes: created/accepted/collected/delivered/finalized/canceled)
- Histórico: `jx-data-table` (Evento | Tentativa | Status HTTP | Próx. retry | Quando) com badge de
  status; falha em vermelho semântico. Empty: "Nenhuma entrega de webhook ainda".

## Acessibilidade (accessibility-pro)
- Contraste AA nos dois temas (success/warning/error/info já calibrados em tokens).
- Modal: foco preso, `Esc` fecha, `aria-modal`, retorno de foco ao gatilho.
- Segredo: `aria-live` no aviso; botão copiar com feedback textual ("Copiado").
- Tabelas: header scope, navegação por teclado, ações com label acessível.

## Copy (br/ux-copywriting-ptbr)
- pt-BR, vocabulário canônico. Sem jargão cru: "Chave de API", "Segredo", "Webhook (notificações)".
- Aviso do segredo: "Esta é a única vez que mostramos o segredo completo. Copie e guarde em local
  seguro."
- Revogar: "Revogar interrompe o acesso desta chave em até 1 minuto. Esta ação não pode ser desfeita."

## Performance (performance-web-vitals)
- Rota lazy. Tabelas paginadas (sem render de histórico inteiro). LCP = título/lista.

---
*Gate 2: todos os tokens citados existem em `docs/identidade-visual/tokens.json`. Zero hex.*
