# deliveries — módulo transacional (Phase 7)

Coração transacional do Jaxegô: criação de entrega (F-03, modalidade **direta**),
a **máquina de 7 estados** (RN-019) e o histórico **append-only** de transições
(RN-012).

## Mapa do módulo

| Arquivo | Responsabilidade |
|---------|------------------|
| `models.py` | `Delivery`, `DeliveryStateTransition` (append-only), `Recipient` (cpf_hash) |
| `state_machine.py` | `DELIVERY_TRANSITIONS` (7 estados) + `assert_delivery_transition` (422) |
| `estimate.py` | mediana de frete (RN-030) compondo a elegibilidade espacial da Phase 6 |
| `schemas.py` | contratos Pydantic v2 (`extra=forbid`), `mask_phone_display` |
| `service.py` | `transition()` (lock pessimista), `create_delivery`, `cancel_delivery`, `list_deliveries`, limite de plano |
| `dependencies.py` | `merchant_scope` — resolve a loja do usuário autenticado (IDOR → 404) |
| `router.py` | `/v1/deliveries` (POST / GET / `{id}` / `{id}/cancel`) |

## Invariantes (não quebrar)

- **`transition()` é o ÚNICO ponto de escrita de `deliveries.state`.** Nunca dar
  `UPDATE deliveries SET state = ...` fora dele — burla a máquina e o histórico.
- **`delivery_state_transitions` é append-only** (trigger MySQL `SIGNAL 45000`).
  A aplicação só faz INSERT; nunca UPDATE/DELETE.
- **Dinheiro em centavos inteiros** (`Integer`), nunca `Float`.
- **PII do destinatário nunca em log** (telefone/endereço/CPF). CPF só como
  `cpf_hash` SHA-256 — sem coluna de CPF cru.
- **Isolamento por `(area_id, merchant_id)` no WHERE** → recurso de outra
  loja/área retorna **404** (não 403; não vaza existência).

## RN-013 — fronteira de privacidade do endereço do destino (NOTA PARA A PHASE 8)

> **Regra (RN-013):** o endereço completo do destino só é revelado ao entregador
> **APÓS a coleta confirmada**. Antes disso, o entregador vê apenas **bairro +
> distância estimada**.

### O que a Phase 7 já fez (modelagem estrutural)

`Delivery` separa, **por construção**, os campos de endereço:

- **Endereço COMPLETO** (revelado só após a coleta — Phase 9):
  `dropoff_address`, `dropoff_number`, `dropoff_complement`.
- **Revelado ANTES da coleta** (na oferta — Phase 8):
  `dropoff_neighborhood_id`, `distance_m`.

A entrega nasce **CRIADA** com `courier_id = NULL` (nenhum entregador vinculado
até o aceite). Portanto, **na Phase 7 nenhum endereço de destino é exposto a
entregador** — não há entregador na entrega ainda. O `DeliveryOut` (superfície da
**loja**) pode conter o endereço completo: a loja é quem digitou, é dona do dado.

### Obrigação da Phase 8 (despacho / F-05)

Ao construir o `OfferOut` (payload da oferta ao entregador), **NÃO incluir o
endereço completo do destino**. A oferta deve conter **apenas**
`dropoff_neighborhood_id` (ou o nome do bairro resolvido) + `distance_m`.

Como os campos já estão separados no modelo, o serializer da oferta monta o
payload **por construção** (selecionando só os campos revelados-antes-da-coleta),
**não por um filtro esquecível** que poderia vazar o endereço. O endereço completo
só entra no contrato do entregador **após** a transição `COLETADA` (Phase 9).

> Teste de contrato esperado na Phase 8 (já listado no ROADMAP): "payload de
> oferta sem endereço completo do destino — RN-013".

## RN-022 — janela do telefone do destinatário (NOTA PARA AS PHASES 8/9)

O telefone do destinatário só é acessível às partes na janela
**ACEITA → FINALIZADA** (RN-022). Em **CRIADA** (Phase 7) o telefone **não** é
exposto a nenhum entregador. Nas superfícies da loja, o telefone é **mascarado**
(`mask_phone_display`); o telefone cru nunca aparece em log nem em lista.
