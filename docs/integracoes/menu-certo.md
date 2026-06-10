# Integração — Menu Certo (CRÍTICA)

**Fonte:** `projeto/docs-externos/integracoes.md:40-51` · ADR-010 · F-04 (`projeto/regras-negocio/fluxos.md:72-86`)

Marketplace de food do Grupo Itcast — **primeiro cliente da API pública** e solução do cold start: pedido pronto → "Chamar Jaxegô" → entrega despachada.

## Direção 1 — Menu Certo → Jaxegô

`POST /v1/deliveries` com `Authorization: Bearer jx_live_...` (API key da área) + **`Idempotency-Key` único por pedido**.

- **Entra:** endereços, destinatário (nome/telefone), itens, `reference_number` (nº do pedido), `payment_method` (`card|pix|direct`), `external_order_id`
- **Sai (202):** `delivery_id`, `tracking_url`, `estimated_pickup_in_seconds`, `delivery_fee` estimado, `platform_fee`
- Entrega criada com `source=menu_certo`; o `reference_number` serve de comprovação leve (ADR-008)

## Direção 2 — Jaxegô → Menu Certo (webhooks)

Eventos: `delivery.accepted`, `delivery.picked_up`, `delivery.delivered`, `delivery.refused_at_destination`, `delivery.cancelled`, `delivery.finalized`.

Headers: `X-Jaxego-Signature: t=<ts>,v1=<hmac_sha256(t + "." + body, secret)>` + `X-Jaxego-Event-Id` (UUID).
Receptor valida janela de 5 min (anti-replay) e deduplica por Event-Id.

## Falhas
- Retry exponencial: 0s / 30s / 2min / 10min / 1h / 4h / 12h / 24h (8 tentativas)
- 4xx ≠ 429 = falha permanente (sem retry)
- 8 falhas → endpoint `unhealthy` + alerta ao admin de área; **a entrega nunca é afetada** (desacoplamento)
- Idempotência server-side: mesma `Idempotency-Key` retorna a resposta original por 24h
- API key revogada → 401 com código de erro estável ("reconfigurar integração")
- Rate limit excedido → 429 com `Retry-After`
