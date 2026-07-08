# CORRECAO-215 — Telefone clicável com modal Ligação/WhatsApp (app entregador)

**Data:** 2026-07-08

## Mudança

**Arquivo:** `apps/app/src/features/entregador/entrega-ativa/entrega-ativa.page.ts`

### Antes
O telefone do destinatário na seção "Entrega" era exibido como texto estático (`<p class="jx-active__muted">`).

### Depois
O telefone vira um botão laranja (`var(--brand)`) que abre um bottom-sheet modal com 2 opções:

- **Ligação** — ícone `faPhone` (laranja), abre `tel:<e164>` no discador nativo
- **WhatsApp** — ícone `faCommentDots` (verde `#25d366`), abre `https://wa.me/<número>` em nova aba

Ao escolher qualquer opção o modal fecha automaticamente.

### Implementação
- `showPhoneModal = signal(false)` — controla visibilidade do modal
- `callPhone()` — `window.location.href = tel:<phone>`
- `openWhatsApp()` — remove `+` do E.164 e abre `wa.me/<número>` via `window.open`
- `iconPhone = faPhone`, `iconWhatsApp = faCommentDots` (free-brands não disponível no projeto)
- Estilos: `.jx-active__phone-btn` (laranja, inline-flex), `.jx-active__modal-opt--whatsapp` (borda/hover verde)
