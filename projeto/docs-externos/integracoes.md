# Jaxegô — Integrações externas

> Por integração: provedor, endpoints usados, payload entra/sai, comportamento em falha, webhooks (assinatura/idempotência).

---

## 1. Safe2Pay (pagamentos) — CRÍTICA

**Usos:** (a) assinatura recorrente da loja; (b) cobrança por entrega cartão/PIX com **split** para a subconta do entregador; (c) fatura mensal de taxas (PIX/cartão/boleto); (d) transferência de saque.

**Entra (criação de cobrança de entrega, simplificado):**
```json
POST /v2/Payment  (cartão ou PIX)
{
  "Amount": 10.50,                  // corrida 8,50 + taxa 2,00
  "Reference": "dlv_01HXAQ3K9P",    // nossa idempotência de negócio
  "Splits": [
    {"Recipient": "subconta_entregador", "Amount": 8.50},
    {"Recipient": "conta_jaxego", "Amount": 2.00}
  ],
  "Customer": { "...dados da loja..." }
}
```
**Sai:** `IdTransaction`, status (`authorized|paid|refused`), QRCode PIX quando aplicável.

**Subcontas:** entregador elegível (MEI ativo — RN-010) é cadastrado como recebedor/subconta com a conta do MEI. Cadastro disparado quando o MEI é aprovado no KYC.

**Webhooks Safe2Pay → Jaxegô:** notificação de status (paga, recusada, estornada, boleto compensado). Validar assinatura/token do header conforme doc do provedor; processar idempotente por `IdTransaction` (tabela de eventos processados). Responder 200 em <5 s; trabalho pesado vai para fila.

**Falhas:**
- Cobrança recusada na criação da entrega → entrega NÃO nasce (F-03 E3); oferecer retry e troca para pagamento direto.
- API fora do ar → circuit breaker; criação cartão/PIX indisponível com aviso; pagamento direto continua funcionando (resiliência do modelo).
- Estorno necessário (cancelamento pré-aceite) → estorno total automático; parcial conforme RN-004.
- Divergência extrato × registros → job de conciliação diária; diferença > R$ 0,01 → alerta admin plataforma.

[DECIDIR] Confirmar na conta Safe2Pay contratada: disponibilidade de split/marketplace no plano, prazo de repasse de subconta e taxa por transação — ajustar escrow interno se o provedor já retiver.

---

## 2. Menu Certo (primeiro cliente da API) — CRÍTICA

**Direção 1 — Menu Certo → Jaxegô:** `POST /v1/deliveries` com `Authorization: Bearer jx_live_...` (API key da área) + `Idempotency-Key` único por pedido.

Entra: endereços, destinatário (nome/telefone), itens, `reference_number` (nº do pedido), `payment_method` (`card|pix|direct`), `external_order_id`.
Sai (202): `delivery_id`, `tracking_url`, `estimated_pickup_in_seconds`, `delivery_fee` estimado, `platform_fee`.

**Direção 2 — Jaxegô → Menu Certo (webhooks):** eventos `delivery.accepted`, `delivery.picked_up`, `delivery.delivered`, `delivery.refused_at_destination`, `delivery.cancelled`, `delivery.finalized`.
Headers: `X-Jaxego-Signature: t=<ts>,v1=<hmac_sha256(t + "." + body, secret)>` + `X-Jaxego-Event-Id` (UUID).
Receptor valida janela de 5 min (anti-replay) e deduplica por Event-Id.

**Falhas:** retry exponencial 0s/30s/2min/10min/1h/4h/12h/24h (8 tentativas); 4xx ≠ 429 = falha permanente (sem retry); após 8 falhas endpoint `unhealthy` + alerta ao admin de área. Idempotência server-side: mesma `Idempotency-Key` retorna a resposta original por 24h.

---

## 3. Receita Federal (consulta CNPJ)

**Uso:** validar situação cadastral de loja (RN-011) e do MEI do entregador (RN-010, CNAEs compatíveis: 4930-2/01, 4930-2/02, 5320-2/02, 5229-0/99).
**Entra:** CNPJ. **Sai:** situação, CNAEs, razão social.
**Falha:** indisponível → cadastro segue `pending_validation` com retry em job (6/6/12/24h); funcionalidade limitada até validar (F-01 E4). Provedor: API pública (minhareceita.org self-hosted como primário [ASSUMIDO], BrasilAPI como fallback).

---

## 4. SMS — Zenvia (primário) / Twilio (fallback)

**Uso:** confirmação de telefone no cadastro (OTP de verificação) + notificação "a caminho" com link de tracking (RN-018). Quota por plano; excedente cobrado na fatura.
**Entra:** telefone E.164, template, variáveis. **Sai:** id da mensagem, status por callback.
**Falha:** provedor primário falha → fallback automático; ambos falham → degrada para e-mail + push, evento logado, custo zero.

---

## 5. E-mail — AWS SES

**Uso:** confirmação de e-mail, notificações de ciclo (fatura fechada, fatura vencendo, KYC aprovado/reprovado, recurso respondido), fallback de SMS.
**Falha:** bounce/complaint → suprimir endereço e marcar para revisão; SES indisponível → fila com retry.

---

## 6. Web Push (VAPID)

**Uso:** canal principal de notificação no app do entregador (nova oferta, lembretes) e da loja (entregador aceitou, entrega concluída). Gratuito.
**Falha:** permissão negada → degrade silencioso para e-mail; tokens expirados limpos por job.

---

## 7. Backblaze B2 + Cloudflare

**Uso:** buckets `jaxego-kyc-prod` (privado), `jaxego-proofs-prod` (privado), `jaxego-public-prod` (assets). Upload por URL pré-assinada direto do cliente; compressão server-side (máx 1920px, WebP); hash SHA-256 registrado.
**Falha:** upload falha → retry no cliente com backoff; B2 indisponível → comprovação aceita em modo offline-tolerante (foto fica no device, sobe quando voltar — flag `pending_upload`, transição só conclui com upload OK).

---

## 8. Rotas/ETA — OSRM self-hosted [ASSUMIDO]

**Uso:** distância em rota e ETA para ranking de despacho e estimativas. Mapa do app: tiles OpenStreetMap/MapLibre.
**Falha:** OSRM fora → fallback haversine × fator 1,4 com flag `eta_degraded`; Google Distance Matrix como fallback pago opcional.

---

## 9. LLMs — Claude (primário) / OpenAI (fallback) — pós-M1, infraestrutura desde o M1

**Uso futuro:** triagem de disputas, análise de foto de comprovação, antifraude de padrão. M1 só registra a infraestrutura: router simples + `ai_usage_log` (provedor, modelo, tokens, custo, latência).
**Falha:** indisponível → funcionalidade degrada para fila manual; nunca bloqueia fluxo operacional.
